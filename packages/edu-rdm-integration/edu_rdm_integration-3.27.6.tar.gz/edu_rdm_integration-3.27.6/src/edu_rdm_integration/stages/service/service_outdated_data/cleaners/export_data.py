from typing import (
    Optional,
)

from django.core.exceptions import (
    FieldDoesNotExist,
)
from django.db.models import (
    Subquery,
)

from educommon.utils.seqtools import (
    make_chunks,
)

from edu_rdm_integration.rdm_models.models import (
    RDMModelEnum,
)
from edu_rdm_integration.stages.export_data.models import (
    RDMExportingDataCommandProgress,
    RDMExportingDataStage,
    RDMExportingDataSubStage,
    RDMExportingDataSubStageAttachment,
    RDMExportingDataSubStageEntity,
)

from .base import (
    BaseServiceOutdatedDataCleaner,
    ServiceFileCleaner,
)
from .consts import (
    UNION_CHUNK_SIZE,
)


class ExportingDataSubStageCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка подэтапов выгрузки данных, которые не ссылаются ни на одну модель РВД.

    Подход:
        - Проходим по всем моделям, зарегистрированным в RDMModelEnum, и собираем
            значения полей exporting_sub_stage_id (если модель содержит такое поле).
        - Объединяем запросы по моделям в UNION, получая набор валидных id.
        - Удаляем те подэтапы, id которых отсутствуют в полученном наборе.
    """

    model = RDMExportingDataSubStage

    def _get_valid_substage_ids_subquery(self) -> Optional[Subquery]:
        """Подзапрос, возвращающий все допустимые exporting_sub_stage_id из моделей, описанных в RDMModelEnum."""
        model_enum_values = RDMModelEnum.get_model_enum_values()
        all_model = [model_enum.model for model_enum in model_enum_values]
        chunk_queries = []

        for enum_values_chunk in make_chunks(all_model, UNION_CHUNK_SIZE, is_list=True):
            qs_list = []
            for model_cls in enum_values_chunk:
                try:
                    model_cls._meta.get_field('exporting_sub_stage_id')
                except FieldDoesNotExist:
                    continue
                qs_list.append(model_cls.objects.values('exporting_sub_stage_id'))

            if qs_list:
                chunk_union = qs_list[0].union(*qs_list[1:])
                chunk_queries.append(chunk_union)

        if not chunk_queries:
            return

        # Объединяем все чанки в один общий UNION
        full_union = chunk_queries[0].union(*chunk_queries[1:])

        return Subquery(full_union.values('exporting_sub_stage_id'))

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных.

         Удаляем подэтапы, которых нет в объединённом наборе валидных exporting_sub_stage_id
        (т.е. подэтапы, не используемые ни одной моделью данных).
        """
        conditions = ''
        subquery = self._get_valid_substage_ids_subquery()
        if subquery:
            conditions = f"""
                NOT EXISTS (
                    SELECT exporting_sub_stage_id
                    FROM ({str(subquery.query)}) AS valid
                    WHERE valid.exporting_sub_stage_id = tbl.id
                )
            """

        return conditions


class ExportingDataStageCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка этапов выгрузки данных без подэтапов."""

    model = RDMExportingDataStage

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        sub_stage_table = ExportingDataSubStageCleaner.get_table_name()

        return self.get_orphan_reference_condition(sub_stage_table, 'stage_id')


class ExportingDataSubStageAttachmentCleaner(ServiceFileCleaner, BaseServiceOutdatedDataCleaner):
    """Очистка вложений подэтапов выгрузки данных."""

    model = RDMExportingDataSubStageAttachment

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
            RETURNING attachment AS file_path
        )
        SELECT file_path FROM deleted_rows;
    """

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        sub_stage_table = ExportingDataSubStageCleaner.get_table_name()
        conditions = [
            'exporting_data_sub_stage_id IS NULL',
            f'({self.get_status_condition(sub_stage_table, "id", "FINISHED", 7, "exporting_data_sub_stage_id")})',
            f'({self.get_status_condition(sub_stage_table, "id", "FAILED", 30, "exporting_data_sub_stage_id")})',
            f'({self.get_orphan_reference_condition(sub_stage_table, "id", "exporting_data_sub_stage_id")})',
        ]

        return ' OR '.join(conditions)


class ExportingDataSubStageEntityCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка связей сущности и подэтапов выгрузки данных."""

    model = RDMExportingDataSubStageEntity

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        sub_stage_table = ExportingDataSubStageCleaner.get_table_name()
        conditions = [
            f'({self.get_status_condition(sub_stage_table, "id", "FINISHED", 7, "exporting_data_sub_stage_id")})',
            f'({self.get_status_condition(sub_stage_table, "id", "FAILED", 30, "exporting_data_sub_stage_id")})',
            f'({self.get_orphan_reference_condition(sub_stage_table, "id", "exporting_data_sub_stage_id")})',
        ]

        return ' OR '.join(conditions)


class ExportingDataCommandProgressCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка устаревших хранящихся задач по экспорту данных."""

    model = RDMExportingDataCommandProgress

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        stage_table = ExportingDataStageCleaner.get_table_name()
        conditions = [
            'stage_id IS NULL',
            f'({self.get_status_condition(stage_table, "id", "FINISHED", 7, "stage_id")})',
            f'({self.get_status_condition(stage_table, "id", "FAILED", 30, "stage_id")})',
            f'({self.get_orphan_reference_condition(stage_table, "id", "stage_id")})',
        ]

        return ' OR '.join(conditions)
