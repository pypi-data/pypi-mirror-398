import asyncio
from abc import (
    ABCMeta,
)
from typing import (
    TYPE_CHECKING,
    Optional,
)

import asyncpg
from django.conf import (
    settings,
)
from django.db import (
    connections,
)
from django.db.models import (
    ForeignKey,
)

from educommon import (
    logger,
)
from m3_db_utils.models import (
    FictiveForeignKeyField,
)

from edu_rdm_integration.rdm_models.models import (
    BaseMainRDMModel,
    RDMModelEnum,
)


if TYPE_CHECKING:
    from asyncpg import (
        Pool,
    )

    from m3_db_utils.models import (
        ModelEnumValue,
    )


class BaseModelOutdatedDataCleaner(metaclass=ABCMeta):
    """Базовый класс уборщика устаревших данных моделей РВД."""

    # Запрос для разбиения таблицы на чанки и получения идентификаторов первых и последних записей
    SELECT_RDM_CHUNK_BOUNDED_SQL = """
            DO $$
            DECLARE
                chunk_size INT := {chunk_size};
                last_id INT := 0;
                first_id INT;
                last_chunk_id INT;
            BEGIN
                -- Создаем временную таблицу без ON COMMIT DROP
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

            -- Теперь можно безопасно выбрать данные
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

    def __init__(
        self,
        model_enum_value: 'ModelEnumValue',
        *args,
        safe: bool = False,
        log_sql: bool = False,
        **kwargs,
    ):
        self._model_enum_value = model_enum_value
        self._safe = safe
        self._log_sql = log_sql
        self._deleted_count = 0

        super().__init__(*args, **kwargs)

    def get_remove_empty_related_data_conditions(self) -> Optional[str]:
        """Формирование условий очистки данных, содержащих связи с моделями с отсутствующими связанными записями."""
        remove_empty_related_data_conditions = None

        rel_model_condition_template = """
            NOT EXISTS (
                SELECT 1 FROM {0} WHERE {0}.id = tbl.{1}
            )
        """

        rel_model_null_condition_template = """
            tbl.{1} IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM {0} WHERE {0}.id = tbl.{1}
            )
        """

        remove_empty_related_data_conditions_template = """
            (
                {}
            )
            -- Добавлено условие: удалить только записи старше 30 дней
            AND tbl.modified <= NOW() - INTERVAL '30 days'
        """

        model_label_enum_data = RDMModelEnum.get_model_label_enum_data()
        related_fields = []

        for field in self._model_enum_value.model._meta.concrete_fields:
            if isinstance(field, FictiveForeignKeyField):
                model_label = field.to
            elif isinstance(field, ForeignKey):
                model_label = field.related_model._meta.label
            else:
                continue

            if model_label in model_label_enum_data:
                table_name = model_label_enum_data[model_label].model._meta.db_table
                related_fields.append((field.name, table_name, field.null))

        if related_fields:
            rel_model_conditions_list = []

            for field_name, table_name, is_null in related_fields:
                if is_null:
                    rel_model_conditions_list.append(rel_model_null_condition_template.format(table_name, field_name))
                else:
                    rel_model_conditions_list.append(rel_model_condition_template.format(table_name, field_name))

            rel_model_conditions = ' OR '.join(rel_model_conditions_list)

            remove_empty_related_data_conditions = remove_empty_related_data_conditions_template.format(
                rel_model_conditions
            )

        return remove_empty_related_data_conditions

    def get_remove_data_by_deleted_records_conditions(self) -> Optional[str]:
        """Формирование условия очистки данных по удаленным записям в ЭШ.

        Если данные в ЭШ были удалены, то после оповещения "Региональной витрины данных" об удалении того или иного
        экземпляра сущности, данные могут быть удалены, т.к. больше не будут обновляться.
        """
        remove_data_by_deleted_records_conditions_sql = None

        if issubclass(self._model_enum_value.model, BaseMainRDMModel):
            remove_data_by_deleted_records_conditions_sql = """
                EXISTS (
                    SELECT 1
                    FROM rdm_exporting_data_sub_stage redss
                    WHERE redss.id = tbl.exporting_sub_stage_id
                        AND redss.status_id = 'FINISHED'
                        AND tbl.operation = 3
                )
            """

        return remove_data_by_deleted_records_conditions_sql

    def get_remove_data_by_finished_status_conditions(self) -> Optional[str]:
        """Формирование условия для удаления записей по выгруженным моделям."""
        remove_data_by_finished_status_conditions_sql = None

        if issubclass(self._model_enum_value.model, BaseMainRDMModel):
            remove_data_by_finished_status_conditions_sql = """
                EXISTS (
                    SELECT 1
                    FROM rdm_exporting_data_sub_stage redss
                    WHERE redss.id = tbl.exporting_sub_stage_id
                        AND redss.status_id = 'FINISHED'
                )
            """

        return remove_data_by_finished_status_conditions_sql

    def get_merged_conditions(self) -> Optional[str]:
        """Формирование общего условия для определения устаревших записей."""
        remove_empty_related_data_conditions = self.get_remove_empty_related_data_conditions()
        remove_data_by_deleted_records_conditions = self.get_remove_data_by_deleted_records_conditions()
        remove_data_by_finished_status_conditions = self.get_remove_data_by_finished_status_conditions()

        main_conditions = []
        if remove_empty_related_data_conditions:
            main_conditions.append(f'({remove_empty_related_data_conditions})')

        if remove_data_by_deleted_records_conditions:
            main_conditions.append(f'({remove_data_by_deleted_records_conditions})')

        if main_conditions:
            conditions = ' OR '.join(main_conditions)
        else:
            return None

        if remove_data_by_finished_status_conditions:
            conditions = f'({conditions}) AND ({remove_data_by_finished_status_conditions})'

        return conditions

    def get_chunk_bounded(self) -> list[tuple[int, int, int]]:
        """Получение идентификаторов-границ чанков для проверки и удаления устаревших данных."""
        get_chunk_bounded_sql = self.SELECT_RDM_CHUNK_BOUNDED_SQL.format(
            chunk_size=settings.RDM_CLEANUP_MODELS_OUTDATED_DATA_CHUNK_SIZE,
            table_name=self._model_enum_value.model._meta.db_table,
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
                f'Запрос для получения границ чанков модели {self._model_enum_value.key}: \n{get_chunk_bounded_sql}\n'
            )

        with connections[settings.USING_RDM_DB_NAME].cursor() as cursor:
            cursor.execute(get_chunk_bounded_sql)
            result = cursor.fetchall()

        return result

    def prepare_queries(self, chunk_bounded: list[tuple[int, int, int]]) -> list[str]:
        """Формирование списка запросов для удаления устаревших данных."""
        queries = []
        conditions = self.get_merged_conditions()

        if conditions:
            for chunk_number, first_id, last_id in chunk_bounded:
                remove_outdated_data_sql = self.REMOVE_OUTDATED_DATA_SQL.format(
                    table_name=self._model_enum_value.model._meta.db_table,
                    first_id=first_id,
                    last_id=last_id,
                    conditions=conditions,
                )

                queries.append(remove_outdated_data_sql)

        return queries

    async def execute_query(self, pool: 'Pool', query: str) -> str:
        """Асинхронное выполнение запроса."""
        async with pool.acquire() as conn:
            try:
                if self._safe:
                    logger.info('Запрос не будет выполнен, включен безопасный режим!\n')

                    if self._log_sql:
                        logger.info(f'{query}\n')
                else:
                    deleted_count = await conn.fetchval(query)

                    self._deleted_count += deleted_count

                    if self._log_sql:
                        logger.info(f'При помощи запроса:\n{query}\n')

                    logger.info(f'Было удалено записей: {deleted_count}\n')
            except Exception as e:
                logger.error(f'Ошибка при выполнении {query}\n{e}')

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

        logger.info(f'Удалено записей модели {self._model_enum_value.key}: {self._deleted_count}')
