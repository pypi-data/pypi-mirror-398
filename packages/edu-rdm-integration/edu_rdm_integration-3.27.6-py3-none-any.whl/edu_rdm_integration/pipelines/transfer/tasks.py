import time
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    TYPE_CHECKING,
    Iterable,
)

import celery
from celery.schedules import (
    crontab,
)
from django.conf import (
    settings,
)
from django.utils import (
    timezone,
)

from educommon import (
    logger,
)
from educommon.async_task.models import (
    AsyncTaskType,
    RunningTask,
)
from educommon.async_task.tasks import (
    SelfReschedulingAsyncTask,
    UniquePeriodicAsyncTask,
)
from educommon.django.db.mixins.validation import (
    QuerySet,
)
from educommon.utils.date import (
    get_today_min_datetime,
)

from edu_rdm_integration.core.consts import (
    FAST_TRANSFER_TASK_QUEUE_NAME,
    LONG_TRANSFER_TASK_QUEUE_NAME,
    PAUSE_TIME,
    TASK_QUEUE_NAME,
)
from edu_rdm_integration.core.enums import (
    CommandType,
)
from edu_rdm_integration.core.helpers import (
    save_command_log_link,
)
from edu_rdm_integration.pipelines.transfer.enums import (
    EntityLevelQueueTypeEnum,
)
from edu_rdm_integration.pipelines.transfer.mixins import (
    BaseTransferLatestEntitiesDataMixin,
)
from edu_rdm_integration.pipelines.transfer.models import (
    TransferredEntity,
)
from edu_rdm_integration.stages.collect_data.models import (
    RDMCollectingDataCommandProgress,
)
from edu_rdm_integration.stages.collect_data.operations import (
    BaseCollectLatestModelsData,
)
from edu_rdm_integration.stages.export_data.models import (
    RDMExportingDataCommandProgress,
)
from edu_rdm_integration.stages.export_data.operations import (
    ExportLatestEntitiesData,
)


if TYPE_CHECKING:
    from django.db.models import (
        QuerySet,
    )


# Задержки перезапуска задач
DEFAULT_TASK_REAPPLY_DELAY = 5  # По-умолчанию
RDM_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS = int(
    getattr(settings, 'RDM_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS', None) or DEFAULT_TASK_REAPPLY_DELAY
)
RDM_FAST_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS = int(
    getattr(settings, 'RDM_FAST_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS', None) or DEFAULT_TASK_REAPPLY_DELAY
)
RDM_LONG_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS = int(
    getattr(settings, 'RDM_LONG_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS', None) or DEFAULT_TASK_REAPPLY_DELAY
)


def split_interval(
    start: datetime,
    end: datetime,
    delta: int,
) -> Iterable[tuple[datetime, datetime]]:
    """Делит интервал start - end на отрезки длиной delta."""
    if delta == 0:
        yield (start, end)
    else:
        current_start = start

        while current_start < end:
            current_end = current_start + timedelta(minutes=delta)
            if current_end > end:
                current_end = end

            yield (current_start, current_end)

            current_start = current_end


class BaseTransferLatestEntitiesDataPeriodicTask(BaseTransferLatestEntitiesDataMixin, UniquePeriodicAsyncTask):
    """Базовая периодическая задача сбора и выгрузки данных для переиспользования в разных очередях."""

    def _run_collect_model_data(self, model: str, task_id: str, interval_delta: int, startup_period: int) -> None:
        """Запускает сбор данных модели РВД."""
        manager = self._collecting_data_managers[model]
        manager_last_collected = (
            self._collecting_data_manager_to_logs_period_end.get(manager.uuid) or get_today_min_datetime()
        )

        now = timezone.now()

        # Если задан период запуска сборки и выгрузки данных сущности, то необходимо проверить, настало ли время для
        # сбора данных модели
        if startup_period != 0 and manager_last_collected > now - timedelta(minutes=startup_period):
            logger.info(f'Skip collecting {model} data by startup period.')

            return

        for begin, end in split_interval(
            start=manager_last_collected,
            end=now,
            delta=interval_delta,
        ):
            command = self._create_collect_command(model, task_id, begin, end)
            collect_model_data = self._prepare_collect_model_data_class(command)
            collect_model_data.collect()

            command.refresh_from_db(fields=['stage_id'])
            save_command_log_link(command, settings.RDM_COLLECT_LOG_DIR)

    def _run_export_entity_data(self, entity: str, task_id: str, interval_delta: int) -> None:
        """Запускает экспорт данных сущности РВД."""
        manager = self._exporting_data_managers[entity]
        manager_last_exported = self._exporting_data_manager_to_period_end.get(manager.uuid)

        if not manager_last_exported:
            return

        for begin, end in split_interval(
            start=manager_last_exported,
            end=timezone.now(),
            delta=interval_delta,
        ):
            command = self._create_export_command(entity, task_id, begin, end)

            export_entity_data = self._prepare_export_entity_data_class(command)
            export_entity_data.export()

            command.refresh_from_db(fields=['stage_id'])
            save_command_log_link(command, settings.RDM_EXPORT_LOG_DIR)

    def _create_collect_command(
        self, model: str, task_id: str, period_started_at: datetime, period_ended_at: datetime
    ) -> RDMCollectingDataCommandProgress:
        """Создает команду сбора данных моделей РВД."""
        return RDMCollectingDataCommandProgress.objects.create(
            model_id=model,
            logs_period_started_at=period_started_at,
            logs_period_ended_at=period_ended_at,
            task_id=task_id,
            type=CommandType.AUTO,
        )

    def _create_export_command(
        self, entity: str, task_id: str, period_started_at: datetime, period_ended_at: datetime
    ) -> RDMExportingDataCommandProgress:
        """Создает команду экспорта данных сущностей РВД."""
        return RDMExportingDataCommandProgress.objects.create(
            entity_id=entity,
            period_started_at=period_started_at,
            period_ended_at=period_ended_at,
            task_id=task_id,
            type=CommandType.AUTO,
        )

    def _prepare_collect_model_data_class(
        self, command: RDMCollectingDataCommandProgress
    ) -> BaseCollectLatestModelsData:
        """Подготавливает объект класса сбора данных моделей РВД."""
        return BaseCollectLatestModelsData(
            models=[command.model_id],
            logs_period_started_at=command.logs_period_started_at,
            logs_period_ended_at=command.logs_period_ended_at,
            command_id=command.id,
            use_times_limit=True,
        )

    def _prepare_export_entity_data_class(self, command: RDMExportingDataCommandProgress) -> ExportLatestEntitiesData:
        """Подготавливает объект класса экспорта данных сущностей РВД.

        При экспорте данных передаем параметр task_id для обновления поля "Описание"
        наименованиями выгруженных сущностей.
        """
        return ExportLatestEntitiesData(
            entities=[command.entity_id],
            period_started_at=command.period_started_at,
            period_ended_at=command.period_ended_at,
            command_id=command.id,
            task_id=self.request.id,
        )

    def process(self, *args, **kwargs):
        """Выполняет задачу."""
        super().process(*args, **kwargs)

        self.prepare_collect_export_managers()

        task_id = (
            RunningTask.objects.filter(
                pk=self.request.id,
            )
            .values_list('pk', flat=True)
            .first()
        )

        collected_entity_models = set()

        for entity_enum, export_enabled, interval_delta, startup_period_collect_data in sorted(
            self._transferred_entities, key=lambda entity: entity[0].order_number
        ):
            entity_models = self._entites_models_map.get(entity_enum.key, ())
            for model_enum_value in entity_models:
                if model_enum_value.key not in collected_entity_models:
                    collected_entity_models.add(model_enum_value.key)
                    try:
                        self._run_collect_model_data(
                            model=model_enum_value.key,
                            task_id=task_id,
                            interval_delta=interval_delta,
                            startup_period=startup_period_collect_data,
                        )
                    except Exception as e:
                        logger.warning(e)

                        continue

            # Лаг времени для доставки данных в реплику
            time.sleep(PAUSE_TIME)

            try:
                # Если экспорт включен, то он должен запускать независимо от периодичности сбора данных. Это
                # обусловлено необходимостью экспорта данных моделей РВД, у которых изменяется поле modified.
                # Экспорт должен работать на постоянной основе, как выгрузка файлов или проверка статусов загрузки
                # файлов.
                if export_enabled:
                    self._run_export_entity_data(
                        entity=entity_enum.key,
                        task_id=task_id,
                        interval_delta=interval_delta,
                    )
            except Exception as e:
                logger.warning(e)

                continue


class TransferLatestEntitiesDataPeriodicTask(SelfReschedulingAsyncTask, BaseTransferLatestEntitiesDataPeriodicTask):
    """Периодическая задача сбора и выгрузки данных."""

    queue = TASK_QUEUE_NAME
    routing_key = TASK_QUEUE_NAME
    description = 'Периодическая задача сбора и экспорта данных РВД'
    lock_expire_seconds = settings.RDM_TRANSFER_TASK_LOCK_EXPIRE_SECONDS
    next_task_delay_seconds = RDM_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS
    task_type = AsyncTaskType.UNKNOWN
    run_every = crontab(
        minute=settings.RDM_TRANSFER_TASK_MINUTE,
        hour=settings.RDM_TRANSFER_TASK_HOUR,
        day_of_week=settings.RDM_TRANSFER_TASK_DAY_OF_WEEK,
    )

    def get_entity_qs(self) -> 'QuerySet[TransferredEntity]':
        """Возвращает QuerySet сущностей сбора и выгрузки."""
        return TransferredEntity.objects.filter(queue_level=EntityLevelQueueTypeEnum.BASE)


class TransferLatestEntitiesDataFastPeriodicTask(SelfReschedulingAsyncTask, BaseTransferLatestEntitiesDataPeriodicTask):
    """Периодическая задача сбора и выгрузки данных для быстрого уровня очереди."""

    queue = FAST_TRANSFER_TASK_QUEUE_NAME
    routing_key = FAST_TRANSFER_TASK_QUEUE_NAME
    description = 'Периодическая задача сбора и экспорта данных РВД (быстрый уровень)'
    lock_expire_seconds = settings.RDM_FAST_TRANSFER_TASK_LOCK_EXPIRE_SECONDS
    next_task_delay_seconds = RDM_FAST_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS
    task_type = AsyncTaskType.UNKNOWN
    run_every = crontab(
        minute=settings.RDM_FAST_TRANSFER_TASK_MINUTE,
        hour=settings.RDM_FAST_TRANSFER_TASK_HOUR,
        day_of_week=settings.RDM_FAST_TRANSFER_TASK_DAY_OF_WEEK,
    )

    def get_entity_qs(self) -> 'QuerySet[TransferredEntity]':
        """Возвращает QuerySet сущностей сбора и выгрузки."""
        return TransferredEntity.objects.filter(queue_level=EntityLevelQueueTypeEnum.FAST)


class TransferLatestEntitiesDataLongPeriodicTask(SelfReschedulingAsyncTask, BaseTransferLatestEntitiesDataPeriodicTask):
    """Периодическая задача сбора и выгрузки данных для долгого уровня очереди."""

    queue = LONG_TRANSFER_TASK_QUEUE_NAME
    routing_key = LONG_TRANSFER_TASK_QUEUE_NAME
    description = 'Периодическая задача сбора и экспорта данных РВД (долгий уровень)'
    lock_expire_seconds = settings.RDM_LONG_TRANSFER_TASK_LOCK_EXPIRE_SECONDS
    next_task_delay_seconds = RDM_LONG_TRANSFER_TASK_NEXT_TASK_DELAY_SECONDS
    task_type = AsyncTaskType.UNKNOWN
    run_every = crontab(
        minute=settings.RDM_LONG_TRANSFER_TASK_MINUTE,
        hour=settings.RDM_LONG_TRANSFER_TASK_HOUR,
        day_of_week=settings.RDM_LONG_TRANSFER_TASK_DAY_OF_WEEK,
    )

    def get_entity_qs(self) -> 'QuerySet[TransferredEntity]':
        """Возвращает QuerySet сущностей сбора и выгрузки."""
        return TransferredEntity.objects.filter(queue_level=EntityLevelQueueTypeEnum.LONG)


celery_app = celery.app.app_or_default()
celery_app.register_task(TransferLatestEntitiesDataPeriodicTask)
celery_app.register_task(TransferLatestEntitiesDataFastPeriodicTask)
celery_app.register_task(TransferLatestEntitiesDataLongPeriodicTask)
