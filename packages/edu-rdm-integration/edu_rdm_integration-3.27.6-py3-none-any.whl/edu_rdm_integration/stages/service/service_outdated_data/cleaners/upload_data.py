from uploader_client.models import (
    Entry,
)

from edu_rdm_integration.stages.upload_data.models import (
    RDMExportingDataSubStageUploaderClientLog,
    RDMUploadStatusRequestLog,
)

from .base import (
    BaseServiceOutdatedDataCleaner,
)
from .export_data import (
    ExportingDataSubStageAttachmentCleaner,
    ExportingDataSubStageCleaner,
)


class ExportingDataSubStageUploaderClientLogCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка логов загрузчика подэтапов выгрузки данных без связи с подэтапами или файлами."""

    model = RDMExportingDataSubStageUploaderClientLog

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        sub_stage_table = ExportingDataSubStageCleaner.get_table_name()
        attachment_table = ExportingDataSubStageAttachmentCleaner.get_table_name()

        conditions = [
            f'({self.get_status_condition(sub_stage_table, "id", "FINISHED", 7, "sub_stage_id")})',
            f'({self.get_status_condition(sub_stage_table, "id", "FAILED", 30, "sub_stage_id")})',
            f'({self.get_orphan_reference_condition(sub_stage_table, "id", local_field="sub_stage_id")})',
            f'({self.get_orphan_reference_condition(attachment_table, "id", local_field="attachment_id")})',
        ]

        return ' OR '.join(conditions)


class UploadStatusRequestLogCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка логов статуса загрузки файла в витрину без связей upload."""

    model = RDMUploadStatusRequestLog

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        uploader_client_log_table = ExportingDataSubStageUploaderClientLogCleaner.get_table_name()

        return self.get_orphan_reference_condition(uploader_client_log_table, 'id', local_field='upload_id')


class EntryCleaner(BaseServiceOutdatedDataCleaner):
    """Очистка записей журнала, не связанные ни с upload, ни с логами."""

    model = Entry

    def get_merged_conditions(self) -> str:
        """Формирует условие удаления для устаревших данных."""
        uploader_client_log_table = ExportingDataSubStageUploaderClientLogCleaner.get_table_name()
        upload_status_log_table = UploadStatusRequestLogCleaner.get_table_name()
        conditions = [
            f'({self.get_orphan_reference_condition(uploader_client_log_table, "entry_id")})',
            f'({self.get_orphan_reference_condition(upload_status_log_table, "entry_id")})',
        ]

        return ' AND '.join(conditions)
