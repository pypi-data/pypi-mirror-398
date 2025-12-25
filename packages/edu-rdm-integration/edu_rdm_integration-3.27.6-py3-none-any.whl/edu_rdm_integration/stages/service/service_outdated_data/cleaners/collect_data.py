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
from edu_rdm_integration.stages.collect_data.models import (
    RDMCollectingDataCommandProgress,
    RDMCollectingDataStage,
    RDMCollectingDataSubStage,
)

from .base import (
    BaseServiceOutdatedDataCleaner,
)
from .consts import (
    UNION_CHUNK_SIZE,
)


class CollectingDataSubStageCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка подэтапов сбора данных, которые не ссылаются ни на одну модель РВД.

    Подход:
        - Проходим по всем моделям, зарегистрированным в RDMModelEnum, и собираем
            значения полей collecting_sub_stage_id (если модель содержит такое поле).
        - Объединяем запросы по моделям в UNION, получая набор валидных id.
        - Удаляем те подэтапы, id которых отсутствуют в полученном наборе.
    """

    model = RDMCollectingDataSubStage

    def _get_valid_substage_ids_subquery(self) -> Optional[Subquery]:
        """Подзапрос, возвращающий все допустимые collecting_sub_stage_id из моделей, описанных в RDMModelEnum."""
        model_enum_values = RDMModelEnum.get_model_enum_values()
        all_model = [model_enum.model for model_enum in model_enum_values]
        chunk_queries = []

        for enum_values_chunk in make_chunks(all_model, UNION_CHUNK_SIZE, is_list=True):
            qs_list = []
            for model_cls in enum_values_chunk:
                try:
                    model_cls._meta.get_field('collecting_sub_stage_id')
                except FieldDoesNotExist:
                    continue

                qs_list.append(model_cls.objects.values('collecting_sub_stage_id'))

            if qs_list:
                chunk_union = qs_list[0].union(*qs_list[1:])
                chunk_queries.append(chunk_union)

        if not chunk_queries:
            return

        # Объединяем все чанки в один общий UNION
        full_union = chunk_queries[0].union(*chunk_queries[1:])

        return Subquery(full_union)

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных.

         Удаляем подэтапы, которых нет в объединённом наборе валидных collecting_sub_stage_id
        (т.е. подэтапы, не используемые ни одной моделью данных).
        """
        conditions = ''
        subquery = self._get_valid_substage_ids_subquery()
        if subquery:
            conditions = f"""
                NOT EXISTS (
                    SELECT collecting_sub_stage_id
                    FROM ({str(subquery.query)}) AS valid
                    WHERE valid.collecting_sub_stage_id = tbl.id
                )
            """

        return conditions


class CollectingDataStageCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка этапов сбора данных, у которых нет связанных подэтапов."""

    model = RDMCollectingDataStage

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        sub_stage_table = CollectingDataSubStageCleaner.get_table_name()

        return self.get_orphan_reference_condition(sub_stage_table, 'stage_id')


class CollectingDataCommandProgressCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка устаревших хранящихся задач по сбору данных."""

    model = RDMCollectingDataCommandProgress

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        stage_table = CollectingDataStageCleaner.get_table_name()
        conditions = [
            'stage_id IS NULL',
            f'({self.get_status_condition(stage_table, "id", "FINISHED", 7, "stage_id")})',
            f'({self.get_status_condition(stage_table, "id", "FAILED", 30, "stage_id")})',
            f'({self.get_orphan_reference_condition(stage_table, "id", "stage_id")})',
        ]

        return ' OR '.join(conditions)
