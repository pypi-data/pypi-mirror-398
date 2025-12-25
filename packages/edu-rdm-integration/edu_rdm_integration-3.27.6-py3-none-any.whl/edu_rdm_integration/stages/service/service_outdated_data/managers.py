from typing import (
    Optional,
)

from educommon import (
    logger,
)

from edu_rdm_integration.stages.service.service_outdated_data.cleaners.collect_data import (
    CollectingDataCommandProgressCleaner,
    CollectingDataStageCleaner,
    CollectingDataSubStageCleaner,
)
from edu_rdm_integration.stages.service.service_outdated_data.cleaners.export_data import (
    ExportingDataCommandProgressCleaner,
    ExportingDataStageCleaner,
    ExportingDataSubStageAttachmentCleaner,
    ExportingDataSubStageCleaner,
    ExportingDataSubStageEntityCleaner,
)
from edu_rdm_integration.stages.service.service_outdated_data.cleaners.upload_data import (
    EntryCleaner,
    ExportingDataSubStageUploaderClientLogCleaner,
    UploadStatusRequestLogCleaner,
)


class ServiceOutdatedDataCleanerManager:
    """Управляет очисткой устаревших сервисных данных по разным этапам."""

    STAGES_MAPPING = {
        'collect': [
            CollectingDataSubStageCleaner,
            CollectingDataStageCleaner,
            CollectingDataCommandProgressCleaner,
        ],
        'export': [
            ExportingDataSubStageCleaner,
            ExportingDataStageCleaner,
            ExportingDataSubStageAttachmentCleaner,
            ExportingDataSubStageEntityCleaner,
            ExportingDataCommandProgressCleaner,
        ],
        'upload': [
            ExportingDataSubStageUploaderClientLogCleaner,
            UploadStatusRequestLogCleaner,
            EntryCleaner,
        ],
    }

    def __init__(self, *args, stages: Optional[list[str]] = None, safe: bool = False, log_sql: bool = False, **kwargs):
        """Инициализация менеджера."""
        self._stages = stages
        self._safe = safe
        self._log_sql = log_sql

        super().__init__(*args, **kwargs)

    def _process_stage(self, stage: str):
        """Запускает все зарегистрированные уборщики для указанного этапа."""
        cleaners = self.STAGES_MAPPING.get(stage, [])
        if not cleaners:
            logger.info(f'Для этапа "{stage}" нет зарегистрированных уборщиков.')
            return

        for cleaner_cls in cleaners:
            cleaner_cls(safe=self._safe, log_sql=self._log_sql).run()

    def run(self):
        """Запускает очистку устаревших данных сервисных моделей РВД."""
        stages_to_process = self._stages or self.STAGES_MAPPING.keys()
        for stage in stages_to_process:
            self._process_stage(stage)
