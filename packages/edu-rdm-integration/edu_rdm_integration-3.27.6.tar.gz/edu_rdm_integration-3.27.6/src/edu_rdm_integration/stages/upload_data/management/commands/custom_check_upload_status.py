from time import (
    sleep,
)
from typing import (
    Any,
)

from django.core.cache import (
    cache,
)
from django.core.management.base import (
    BaseCommand,
)

from edu_rdm_integration.core.consts import (
    BATCH_SIZE,
)
from edu_rdm_integration.stages.upload_data.enums import (
    FileUploadStatusEnum,
)
from edu_rdm_integration.stages.upload_data.helpers import (
    UploadStatusHelper,
)
from edu_rdm_integration.stages.upload_data.models import (
    RDMExportingDataSubStageUploaderClientLog,
)


class Command(BaseCommand):
    """Команда для отправки данных в витрину параллельно-последовательно. В рамках скрипта последовательно,
    параллельно количетвом запусков команды.
    """

    help = 'Команда для отправки данных в витрину параллельно-последовательно'  # noqa: A003

    def handle(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        """Обработчик команды."""
        while True:
            self.stdout.write('Начало проверки статуса загрузки данных в витрину..')

            # Получаем незавершенные загрузки данных в витрину
            in_progress_uploads = RDMExportingDataSubStageUploaderClientLog.objects.filter(
                file_upload_status=FileUploadStatusEnum.IN_PROGRESS,
                is_emulation=False,
            ).select_related('attachment')[:BATCH_SIZE]

            for upload in in_progress_uploads:
                upload.file_upload_status = FileUploadStatusEnum.IN_CHECK

            RDMExportingDataSubStageUploaderClientLog.objects.bulk_update(
                in_progress_uploads, fields=['file_upload_status']
            )

            self.stdout.write(f'Обновление статуса загрузки данных в витрину на {FileUploadStatusEnum.IN_CHECK}..')

            UploadStatusHelper(in_progress_uploads, cache).run()

            sleep(10)

            self.stdout.write('Окончание проверки статуса загрузки данных в витрину.\n\n')
