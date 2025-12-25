import asyncio
from pathlib import (
    Path,
)
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

from asgiref.sync import (
    sync_to_async,
)
from django.conf import (
    settings,
)
from django.db.models import (
    F,
    Q,
    Sum,
)
from django.db.transaction import (
    atomic,
)
from uploader_client.adapters import (
    UploaderAdapter,
)

from educommon import (
    logger,
)
from educommon.utils.seqtools import (
    make_chunks,
)

from edu_rdm_integration.core.consts import (
    LOGS_DELIMITER,
)
from edu_rdm_integration.core.redis_cache import (
    AbstractCache,
)
from edu_rdm_integration.stages.export_data.consts import (
    ATTACHMENTS_LIMIT,
    TOTAL_ATTACHMENTS_SIZE_KEY,
)
from edu_rdm_integration.stages.export_data.functions.base.consts import (
    OPERATIONS_METHODS_MAP,
    OPERATIONS_URLS_MAP,
)
from edu_rdm_integration.stages.export_data.functions.base.requests import (
    RegionalDataMartEntityRequest,
)
from edu_rdm_integration.stages.export_data.models import (
    RDMExportingDataSubStage,
    RDMExportingDataSubStageAttachment,
    RDMExportingDataSubStageStatus,
)
from edu_rdm_integration.stages.upload_data.consts import (
    FAILED_STATUSES,
)
from edu_rdm_integration.stages.upload_data.dataclasses import (
    UploadFile,
)
from edu_rdm_integration.stages.upload_data.enums import (
    FileUploadStatusEnum,
)
from edu_rdm_integration.stages.upload_data.helpers import (
    UploadStatusHelper,
)
from edu_rdm_integration.stages.upload_data.models import (
    RDMExportingDataSubStageUploaderClientLog,
    RDMRequestStatus,
    RDMUploadStatusRequestLog,
)
from edu_rdm_integration.stages.upload_data.queues import (
    Queue,
)


if TYPE_CHECKING:
    from uploader_client.models import (
        Entry,
    )


class ExportQueueSender:
    """Класс отправки данных в очередь РВД."""

    def __init__(self, data_cache: AbstractCache, queue: Queue, limit: Optional[int] = None):
        self.queue = queue
        self.cache = data_cache
        self.queue_total_file_size = self.cache.get(TOTAL_ATTACHMENTS_SIZE_KEY) or 0
        self.queue_is_full = False
        self.limit = limit or ATTACHMENTS_LIMIT

    @staticmethod
    def get_exported_file_size() -> int:
        """Возвращает размер отправленных в РВД файлов.

        При расчете используются только файлы, отмеченные как отправленные, но не обработанные витриной.
        """
        sended_attachment_ids = RDMExportingDataSubStageUploaderClientLog.objects.filter(
            file_upload_status=FileUploadStatusEnum.IN_PROGRESS
        ).values_list('attachment_id', flat=True)
        file_size = RDMExportingDataSubStageAttachment.objects.filter(id__in=sended_attachment_ids).aggregate(
            Sum('attachment_size')
        )['attachment_size__sum']

        return file_size or 0

    def _make_stage_filter(self) -> Q:
        """Формирование фильтра для выборки подэтапов."""
        return Q(
            status_id=RDMExportingDataSubStageStatus.READY_FOR_EXPORT.key,
            rdmexportingdatasubstageattachment__id__isnull=False,
        )

    def get_sub_stages_attachments_to_export(self):
        """Выборка готовых к экспорту подэтапов."""
        sub_stage_ids = set(
            RDMExportingDataSubStage.objects.filter(self._make_stage_filter())
            .order_by('started_at')
            .values_list('id', flat=True)[: self.limit]
        )

        return (
            RDMExportingDataSubStage.objects.filter(id__in=sub_stage_ids)
            .annotate(
                attachment_id=F('rdmexportingdatasubstageattachment__id'),
                attachment_name=F('rdmexportingdatasubstageattachment__attachment'),
                attachment_size=F('rdmexportingdatasubstageattachment__attachment_size'),
                operation=F('rdmexportingdatasubstageattachment__operation'),
                entity=F('rdmexportingdatasubstageentity__entity_id'),
            )
            .order_by('id', 'operation')
            .filter(entity__isnull=False)
            .values(
                'id',
                'attachment_id',
                'attachment_name',
                'attachment_size',
                'operation',
                'entity',
            )
        )

    def set_sub_stage_to_cache(self, sub_stage_id: int, entity_name: str, attachments: list[UploadFile]) -> bool:
        """Помещение подэтапа в очередь вместе с информацией по файлам и обновление счетчика объема файлов."""
        sub_stage_total_size = sum((attachment.attachment_size for attachment in attachments))
        if self.queue_total_file_size + sub_stage_total_size > settings.RDM_UPLOAD_QUEUE_MAX_SIZE:
            return False

        self.queue.enqueue(sub_stage_id, entity_name, attachments)
        self.queue_total_file_size += sub_stage_total_size
        # Обновим размер файлов в кеш
        self.cache.set(
            TOTAL_ATTACHMENTS_SIZE_KEY, self.queue_total_file_size, timeout=settings.RDM_REDIS_CACHE_TIMEOUT_SECONDS
        )

        logger.info(f'{LOGS_DELIMITER * 2}ExportedDataSubStage {sub_stage_id} {entity_name} added to the queue')

        return True

    def run(self):
        """Запуск работы очереди."""
        if not self.queue_total_file_size:
            self.queue_total_file_size = self.get_exported_file_size()
        if self.queue_total_file_size < settings.RDM_UPLOAD_QUEUE_MAX_SIZE:
            stage_files = []
            prev_sub_stage = None
            entity = ''
            # Если размер очереди позволяет - то отправляем все файлы подэтапа в очередь - иначе прерываем процесс
            for stage_attachment in self.get_sub_stages_attachments_to_export():
                if prev_sub_stage != stage_attachment['id']:
                    if stage_files:
                        to_cache = self.set_sub_stage_to_cache(prev_sub_stage, entity, stage_files)

                        stage_files = []

                        if not to_cache:
                            break

                    prev_sub_stage = stage_attachment['id']

                if stage_attachment['attachment_size']:
                    stage_files.append(
                        UploadFile(
                            stage_attachment['attachment_id'],
                            stage_attachment['attachment_name'],
                            stage_attachment['attachment_size'],
                            stage_attachment['operation'],
                        )
                    )
                    entity = stage_attachment['entity']

            # Обновляем общий объем очереди и закидываем последний элемент
            if stage_files:
                self.set_sub_stage_to_cache(prev_sub_stage, entity, stage_files)
        else:
            # Сохраняем объем отправленных файлов в кеш
            self.cache.set(
                TOTAL_ATTACHMENTS_SIZE_KEY, self.queue_total_file_size, timeout=settings.RDM_REDIS_CACHE_TIMEOUT_SECONDS
            )
            self.queue_is_full = True
            logger.warning(f'Total exported file size:  {self.queue_total_file_size} - queue is full!!!')


class WorkerSender:
    """Непосредственная отправка файлов."""

    def __init__(self, queue: Queue):
        self.queue = queue
        self.entities = set()
        self.received_file_size = 0

    async def get_file_upload_status(
        self,
        request_id: str,
        adapter: UploaderAdapter,
    ) -> tuple[Optional[int], Optional[RDMRequestStatus], 'Entry']:
        """Возвращает статус файла в витрине по запросу."""
        file_upload_status = None

        response, log_entry = await UploadStatusHelper.send_upload_status_request(request_id, adapter)
        request_status = None

        if response:
            request_status = RDMRequestStatus.get_values_to_enum_data().get(response.get('code'))

            if not request_status:
                logger.error(
                    'Не удалось определить статус загрузки данных в витрину. Идентификатор загрузки: '
                    f'{request_id}, данные ответа: {response}',
                )

        if request_status in FAILED_STATUSES:
            file_upload_status = FileUploadStatusEnum.ERROR

        elif request_status == RDMRequestStatus.SUCCESSFULLY_PROCESSED:
            file_upload_status = FileUploadStatusEnum.FINISHED

        return file_upload_status, request_status, log_entry

    async def _process_single_file(
        self,
        file: 'UploadFile',
        sub_stage_id: int,
        entity_key: str,
        adapter: UploaderAdapter,
    ) -> tuple[
        Optional[RDMExportingDataSubStageUploaderClientLog],
        Optional[RDMUploadStatusRequestLog],
        dict[str, Any],
    ]:
        if settings.RDM_UPLOADER_CLIENT_ENABLE_REQUEST_EMULATION:
            logger.warning(
                f'{LOGS_DELIMITER * 3}ATTENTION!!! REGIONAL DATA MART INTEGRATION REQUEST EMULATION ENABLED!'
            )
        updates = {'stage_status': None, 'file_size': 0, 'entity_key': None, 'errors': []}
        file_path = Path.joinpath(Path(settings.MEDIA_ROOT), file.attachment_name)
        file_data = None
        try:
            file_data = await sync_to_async(file_path.open('rb').read, thread_sensitive=False)()
        except (OSError, IOError, FileNotFoundError) as error:
            logger.exception(f'Ошибка чтения файла {file_path} - {str(error)}')
            updates['stage_status'] = RDMExportingDataSubStageStatus.FAILED.key
            return None, None, updates

        method = OPERATIONS_METHODS_MAP.get(file.operation)

        request = RegionalDataMartEntityRequest(
            datamart_name=settings.RDM_UPLOADER_CLIENT_DATAMART_NAME,
            table_name=entity_key.lower(),
            method=method,
            operation=OPERATIONS_URLS_MAP.get(file.operation),
            parameters={},
            headers={
                'Content-Type': 'text/csv',
            },
            files=[],
            data=file_data,
        )

        result = await adapter.send(request)

        request_id = result.response.text if not result.error and result.response else ''
        file_upload_status = FileUploadStatusEnum.IN_PROGRESS if request_id else FileUploadStatusEnum.ERROR

        sub_stage_uploader_client_log = RDMExportingDataSubStageUploaderClientLog(
            entry_id=result.log.id,
            sub_stage_id=sub_stage_id,
            attachment_id=file.attachment_id,
            request_id=request_id,
            file_upload_status=file_upload_status,
            is_emulation=settings.RDM_UPLOADER_CLIENT_ENABLE_REQUEST_EMULATION,
        )

        upload_status_request_log = None

        if request_id:
            updated_file_upload_status, request_status, log_entry = await self.get_file_upload_status(
                request_id, adapter
            )

            upload_status_request_log = RDMUploadStatusRequestLog(
                upload=sub_stage_uploader_client_log,
                entry_id=log_entry.id,
                request_status_id=getattr(request_status, 'key', None),
            )

            if updated_file_upload_status and updated_file_upload_status != file_upload_status:
                sub_stage_uploader_client_log.file_upload_status = updated_file_upload_status

            if updated_file_upload_status == FileUploadStatusEnum.FINISHED:
                updates['file_size'] = file.attachment_size

            if updated_file_upload_status == FileUploadStatusEnum.ERROR:
                updates['stage_status'] = RDMExportingDataSubStageStatus.PROCESS_ERROR.key

        if result.error:
            logger.warning(f'{result.error}\nrequest - "{result.log.request}"\nresponse - "{result.log.response}"')
            updates['stage_status'] = RDMExportingDataSubStageStatus.FAILED.key
            updates['errors'].append(result.error)
        else:
            logger.info(f'Response with {result.response.status_code} code and content {result.response.text}')
            updates['entity_key'] = entity_key

        return sub_stage_uploader_client_log, upload_status_request_log, updates

    async def _process_sub_stage(
        self,
        sub_stage_id: int,
        entity_key: str,
        upload_files: list['UploadFile'],
        adapter: UploaderAdapter,
    ):
        sub_stage = await sync_to_async(RDMExportingDataSubStage.objects.filter(id=sub_stage_id).first)()
        if not sub_stage:
            return

        file_tasks = [self._process_single_file(file, sub_stage_id, entity_key, adapter) for file in upload_files]
        results = await asyncio.gather(*file_tasks)

        result_to_save = []
        upload_status_requests_to_save = []
        final_status = RDMExportingDataSubStageStatus.FINISHED.key
        total_received_size = 0
        updated_entities = set()

        for log, status_log, updates in results:
            if log:
                result_to_save.append(log)
            if status_log:
                upload_status_requests_to_save.append(status_log)

            if updates.get('stage_status') not in (RDMExportingDataSubStageStatus.FINISHED.key, None):
                final_status = updates.get('stage_status')

            total_received_size += updates.get('file_size', 0)
            if updates.get('entity_key'):
                updated_entities.add(updates['entity_key'])

        @sync_to_async
        @atomic
        def save_and_update_db_and_counters():
            RDMExportingDataSubStageUploaderClientLog.objects.bulk_create(result_to_save)
            RDMUploadStatusRequestLog.objects.bulk_create(upload_status_requests_to_save)
            sub_stage.status_id = final_status
            sub_stage.save()

            self.received_file_size += total_received_size
            self.entities.update(updated_entities)

        await save_and_update_db_and_counters()

        await sync_to_async(self.queue.delete_from_queue)(sub_stage_id=sub_stage_id, entity_name=entity_key)

        logger.info(f'{LOGS_DELIMITER * 3}ExportedDataSubStage {sub_stage_id} {entity_key} sent from the queue')

    async def send_files(self):
        """Отправка файлов."""
        adapter = UploaderAdapter()
        await adapter.init()

        sub_stages_map = self.queue.dequeue()

        for chunk in make_chunks(list(sub_stages_map.keys()), settings.RDM_UPLOAD_DATA_TASK_CHUNK_SIZE):
            sub_stage_tasks = [
                self._process_sub_stage(sub_stage_id, entity_key, sub_stages_map[(sub_stage_id, entity_key)], adapter)
                for sub_stage_id, entity_key in chunk
            ]

            await asyncio.gather(*sub_stage_tasks)

        await adapter.close()

    def run(self):
        """Запуск воркера отправки."""
        asyncio.run(self.send_files())
