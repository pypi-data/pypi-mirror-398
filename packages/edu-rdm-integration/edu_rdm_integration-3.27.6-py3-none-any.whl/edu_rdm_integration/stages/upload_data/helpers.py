import asyncio
from json import (
    JSONDecodeError,
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
from django.db import (
    transaction,
)
from django.db.models import (
    QuerySet,
)
from django.utils import (
    timezone,
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

from edu_rdm_integration.core.redis_cache import (
    AbstractCache,
)
from edu_rdm_integration.stages.export_data.consts import (
    TOTAL_ATTACHMENTS_SIZE_KEY,
)
from edu_rdm_integration.stages.export_data.functions.base.requests import (
    RegionalDataMartStatusRequest,
)
from edu_rdm_integration.stages.export_data.models import (
    RDMExportingDataSubStageStatus,
)
from edu_rdm_integration.stages.upload_data.consts import (
    FAILED_STATUSES,
)
from edu_rdm_integration.stages.upload_data.enums import (
    FileUploadStatusEnum,
)
from edu_rdm_integration.stages.upload_data.models import (
    RDMExportingDataSubStageUploaderClientLog,
    RDMRequestStatus,
    RDMUploadStatusRequestLog,
)


if TYPE_CHECKING:
    from uploader_client.logging.base import (
        Entry,
    )


class UploadStatusHelper:
    """Хелпер проверки статуса загрузки данных в витрину."""

    def __init__(self, in_progress_uploads: QuerySet, cache: AbstractCache) -> None:
        self._in_progress_uploads = list(in_progress_uploads)
        self.cache = cache

    def run(self) -> None:
        """Запускает проверки статусов."""
        asyncio.run(self._run_process_uploads())

    async def _run_process_uploads(self) -> None:
        adapter = UploaderAdapter()
        await adapter.init()

        for chunk in make_chunks(self._in_progress_uploads, settings.RDM_UPLOAD_STATUS_TASK_CHUNK_SIZE):
            tasks = [self._process_upload(upload, adapter) for upload in chunk]

            await asyncio.gather(*tasks)

        await adapter.close()

    @classmethod
    async def send_upload_status_request(
        cls,
        request_id: str,
        adapter: UploaderAdapter,
    ) -> tuple[Optional[dict[str, Any]], 'Entry']:
        """Формирует и отправляет запрос для получения статуса загрузки данных в витрину."""
        request = RegionalDataMartStatusRequest(
            request_id=request_id,
            method='GET',
            parameters={},
            headers={
                'Content-Type': 'application/json',
            },
        )
        result = await adapter.send(request)
        response = None

        if result.error:
            logger.warning(
                f'Ошибка при получении статуса загрузки данных в витрину. Идентификатор загрузки: {request_id}. '
                f'Ошибка: {result.error}, запрос: {result.log.request}, ответ: {result.log.response}',
            )
        else:
            logger.info(
                f'Получен ответ со статусом {result.response.status_code} и содержимым {result.response.text}. '
                f'Идентификатор загрузки: {request_id}',
            )
            try:
                response = result.response.json()
            except JSONDecodeError:
                logger.error(
                    f'Не удалось получить данные из ответа запроса статуса загрузки данных в витрину. '
                    f'Идентификатор загрузки: {request_id}, ответ: {result.response.text}',
                )

        return response, result.log

    @classmethod
    def update_upload_status(
        cls,
        upload: RDMExportingDataSubStageUploaderClientLog,
        response: Optional[dict[str, Any]],
        log_entry: 'Entry',
    ) -> None:
        """Обновляет статус загрузки данных в витрину."""
        request_status = None

        if isinstance(response, dict):
            request_status = RDMRequestStatus.get_values_to_enum_data().get(response.get('code'))

            if not request_status:
                logger.error(
                    'Не удалось определить статус загрузки данных в витрину. Идентификатор загрузки: '
                    f'{upload.request_id}, данные ответа: {response}',
                )

        with transaction.atomic():
            RDMUploadStatusRequestLog.objects.create(
                upload=upload,
                entry_id=log_entry.id,
                request_status_id=getattr(request_status, 'key', None),
            )

            if request_status in FAILED_STATUSES:
                upload.file_upload_status = FileUploadStatusEnum.ERROR
                upload.sub_stage.status_id = RDMExportingDataSubStageStatus.PROCESS_ERROR.key
                upload.sub_stage.save()

            elif request_status == RDMRequestStatus.SUCCESSFULLY_PROCESSED:
                upload.file_upload_status = FileUploadStatusEnum.FINISHED

            upload.modified = timezone.now()
            upload.save()

    def update_cache_size(self, upload: RDMExportingDataSubStageUploaderClientLog) -> None:
        """Обновление размеров файлов в кэше."""
        with self.cache.lock(f'{TOTAL_ATTACHMENTS_SIZE_KEY}:lock', timeout=300):
            queue_total_file_size = self.cache.get(TOTAL_ATTACHMENTS_SIZE_KEY) or 0
            if queue_total_file_size:
                queue_total_file_size -= upload.attachment.attachment_size
                if queue_total_file_size > 0:
                    self.cache.set(
                        TOTAL_ATTACHMENTS_SIZE_KEY,
                        queue_total_file_size,
                        timeout=settings.RDM_REDIS_CACHE_TIMEOUT_SECONDS,
                    )

    async def _process_upload(
        self,
        upload: RDMExportingDataSubStageUploaderClientLog,
        adapter: UploaderAdapter,
    ) -> None:
        """Обрабатывает запись загрузки данных в витрину."""
        response, log_entry = await self.send_upload_status_request(upload.request_id, adapter)
        await sync_to_async(self.update_upload_status)(upload, response, log_entry)
        # Обновим размер файлов в кеш (с блокировкой на время обновления)
        await sync_to_async(self.update_cache_size)(upload)
