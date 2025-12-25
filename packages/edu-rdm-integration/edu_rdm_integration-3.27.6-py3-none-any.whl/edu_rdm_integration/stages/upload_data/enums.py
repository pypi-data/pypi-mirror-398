from m3.db import (
    BaseEnumerate,
)


class FileUploadStatusEnum(BaseEnumerate):
    """Действие по отслеживаемым данным."""

    IN_PROGRESS = 1
    FINISHED = 2
    ERROR = 3
    IN_CHECK = 4

    values = {
        IN_PROGRESS: 'В процессе загрузки в витрину',
        FINISHED: 'Загрузка в витрину закончена',
        ERROR: 'Ошибка загрузки в витрину',
        IN_CHECK: 'На проверке',
    }
