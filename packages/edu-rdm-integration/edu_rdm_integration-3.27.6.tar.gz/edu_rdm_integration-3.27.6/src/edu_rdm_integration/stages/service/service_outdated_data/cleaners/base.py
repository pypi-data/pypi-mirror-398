import asyncio
from abc import (
    ABCMeta,
    abstractmethod,
)
from pathlib import (
    Path,
)
from typing import (
    TYPE_CHECKING,
)

import asyncpg
from django.conf import (
    settings,
)
from django.db import (
    connections,
)

from educommon import (
    logger,
)


if TYPE_CHECKING:
    from asyncpg import (
        Pool,
    )


class BaseServiceOutdatedDataCleaner(metaclass=ABCMeta):
    """Базовый класс уборщика устаревших сервисных данных."""

    model = None

    SELECT_RDM_CHUNK_BOUNDED_SQL = """
        DO $$
        DECLARE
            chunk_size INT := {chunk_size};
            last_id INT := 0;
            first_id INT;
            last_chunk_id INT;
        BEGIN
            DROP TABLE IF EXISTS rdm_chunk_bounds;
            CREATE TEMP TABLE rdm_chunk_bounds (
                chunk_number INT,
                first_id INT,
                last_id INT
            );

            DROP TABLE IF EXISTS tmp_chunk;
            CREATE TEMP TABLE tmp_chunk (id INT) ON COMMIT DROP;

            WHILE TRUE LOOP
                TRUNCATE tmp_chunk;

                INSERT INTO tmp_chunk (id)
                SELECT id
                FROM {table_name}
                WHERE id > last_id
                ORDER BY id
                LIMIT chunk_size;

                IF NOT FOUND THEN
                    EXIT;
                END IF;

                SELECT MIN(id), MAX(id)
                INTO first_id, last_chunk_id
                FROM tmp_chunk;

                INSERT INTO rdm_chunk_bounds (chunk_number, first_id, last_id)
                VALUES (
                    (SELECT COUNT(*) FROM rdm_chunk_bounds) + 1,
                    first_id,
                    last_chunk_id
                );

                last_id := last_chunk_id;
            END LOOP;
        END $$;

        SELECT * FROM rdm_chunk_bounds ORDER BY chunk_number;
    """

    REMOVE_OUTDATED_DATA_SQL = """
        WITH deleted_rows AS (
            DELETE FROM {table_name}
            WHERE id IN (
                WITH tbl AS (
                    SELECT *
                    FROM {table_name}
                    WHERE id >= {first_id}
                        AND id <= {last_id}
                )
                SELECT tbl.id
                FROM tbl
                WHERE {conditions}
            )
            RETURNING id
        )
        SELECT COUNT(*) AS deleted_count FROM deleted_rows;
    """

    def __init__(self, *args, safe: bool = False, log_sql: bool = False, **kwargs):
        """Инициализация уборщика."""
        self._safe = safe
        self._log_sql = log_sql
        self._deleted_count = 0

        super().__init__(*args, **kwargs)

    @abstractmethod
    def get_merged_conditions(self) -> str:
        """Возвращает условия для удаления устаревших данных."""

    @classmethod
    def get_table_name(cls) -> str:
        """Возвращает имя таблицы в базе данных."""
        if cls.model is None:
            raise NotImplementedError('Необходимо задать атрибут "model"')

        return cls.model._meta.db_table

    async def file_deletion_process(self, file_paths: list[str]):
        """Функция для удаления файлов, связанных с удалёнными устаревшими записями.

        Очистка данных производится в таблицах системных моделей РВД.
        """

    def get_orphan_reference_condition(
        self, reference_table: str, reference_field: str, local_field: str = 'id'
    ) -> str:
        """Условие проверки отсутствия записей в связанной таблице."""
        return f"""
            NOT EXISTS (
                SELECT 1
                FROM {reference_table} ref
                WHERE ref.{reference_field} = tbl.{local_field}
            )
        """

    def get_status_condition(
        self, related_table: str, related_field: str, status_value: str, days: int, local_field: str = 'id'
    ) -> str:
        """Условие проверки записи с заданным статусом и возрастом."""
        return f"""
            EXISTS (
                SELECT 1
                FROM {related_table} sub
                WHERE sub.{related_field} = tbl.{local_field}
                  AND sub.status_id = '{status_value}'
                  AND sub.ended_at <= NOW() - INTERVAL '{days} days'
            )
        """

    def get_chunk_bounded(self):
        """Возвращает границы чанков для текущей таблицы."""
        get_chunk_bounded_sql = self.SELECT_RDM_CHUNK_BOUNDED_SQL.format(
            table_name=self.get_table_name(),
            chunk_size=settings.RDM_CLEANUP_MODELS_OUTDATED_DATA_CHUNK_SIZE,
        )

        if self._log_sql:
            # Проверка на доступность sqlparse для форматирования
            try:
                import sqlparse
            except ImportError:
                sqlparse = None

            if sqlparse:
                # Форматирование кода
                get_chunk_bounded_sql = sqlparse.format(
                    sql=get_chunk_bounded_sql,
                    reindent=True,
                    strip_comments=True,
                )
            logger.info(
                f'Запрос для получения границ чанков модели {self.get_table_name()}: \n{get_chunk_bounded_sql}\n'
            )

        with connections[settings.USING_RDM_DB_NAME].cursor() as cursor:
            cursor.execute(get_chunk_bounded_sql)
            result = cursor.fetchall()

        return result

    async def execute_query(self, pool: 'Pool', query: str):
        """Асинхронное выполнение запроса."""
        async with pool.acquire() as conn:
            try:
                if self._safe:
                    logger.info('Запрос не будет выполнен, включен безопасный режим!\n')

                    if self._log_sql:
                        logger.info(f'{query}\n')
                else:
                    result = await conn.fetch(query)
                    if not result:
                        return

                    if self._log_sql:
                        logger.info(f'При помощи запроса:\n{query}\n')

                    # Проверяем, что вернул запрос
                    if 'deleted_count' in result[0]:
                        deleted_count = result[0]['deleted_count']
                        self._deleted_count += deleted_count
                        logger.info(f'Было удалено записей: {deleted_count}')
                    else:
                        file_paths = [record['file_path'] for record in result if record.get('file_path')]
                        if file_paths:
                            await self.file_deletion_process(file_paths)
                        deleted_count = len(result)
                        self._deleted_count += deleted_count
                        logger.info(f'Было удалено записей с файлами: {deleted_count}')

            except Exception as e:
                logger.error(f'Ошибка при выполнении {query}\n{e}')

    def prepare_queries(self, chunk_bounded: list[tuple[int, int, int]]) -> list[str]:
        """Формирование списка запросов для удаления устаревших данных."""
        queries = []
        conditions = self.get_merged_conditions()

        for chunk_number, first_id, last_id in chunk_bounded:
            remove_outdated_data_sql = self.REMOVE_OUTDATED_DATA_SQL.format(
                table_name=self.get_table_name(),
                first_id=first_id,
                last_id=last_id,
                conditions=conditions,
            )

            queries.append(remove_outdated_data_sql)

        return queries

    async def execute_queries(self, queries: list[str]) -> None:
        """Асинхронное выполнение запросов."""
        DB_SETTINGS = settings.DATABASES[settings.USING_RDM_DB_NAME]

        pool = await asyncpg.create_pool(
            max_size=settings.RDM_CLEANUP_MODELS_OUTDATED_DATA_POOL_SIZE,
            min_size=settings.RDM_CLEANUP_MODELS_OUTDATED_DATA_POOL_SIZE,
            host=DB_SETTINGS['HOST'],
            port=DB_SETTINGS['PORT'],
            user=DB_SETTINGS['USER'],
            password=DB_SETTINGS['PASSWORD'],
            database=DB_SETTINGS['NAME'],
        )

        tasks = [self.execute_query(pool, query) for query in queries]

        await asyncio.gather(*tasks)

    def run(self):
        """Запуск очистки устаревших данных."""
        chunk_bounded = self.get_chunk_bounded()

        queries = self.prepare_queries(chunk_bounded=chunk_bounded)

        if queries:
            even_loop = asyncio.new_event_loop()
            try:
                even_loop.run_until_complete(self.execute_queries(queries=queries))
            finally:
                even_loop.close()

        logger.info(f'Удалено записей модели {self.model.__name__}: {self._deleted_count}')


class ServiceFileCleaner:
    """Асинхронный сервис для безопасного удаления файлов из MEDIA_ROOT."""

    @staticmethod
    async def file_deletion_process(file_paths: list[str]) -> None:
        """Удаляет указанные файлы, считая пути относительными к MEDIA_ROOT."""
        media_root = Path(settings.MEDIA_ROOT).resolve()

        async def delete_file(path_str: str):
            path = (media_root / path_str).resolve()
            try:
                exists = await asyncio.to_thread(path.exists)
                if exists and await asyncio.to_thread(path.is_file):
                    await asyncio.to_thread(path.unlink)

            except Exception as e:
                logger.warning(f'Не удалось удалить {path}: {e}')

        await asyncio.gather(*(delete_file(path) for path in file_paths))
