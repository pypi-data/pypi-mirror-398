from django.db.models import (
    Case,
    CharField,
    F,
    Manager,
    PositiveSmallIntegerField,
    Q,
    Value,
    When,
)
from django.db.models.functions import (
    Cast,
)

from edu_rdm_integration.stages.upload_data.uploader_log.enums import (
    RequestResultStatus,
)


class UploaderClientLogManager(Manager):
    """Менеджер модели журнала Загрузчика данных в витрину."""

    def get_queryset(self):
        """Возвращает кварисет."""
        query = super().get_queryset()

        result_status = Case(
            When(
                Q(Q(error__isnull=True) | Q(error__exact='')) & Q(Q(response__isnull=False) & ~Q(response__exact='')),
                then=Value(RequestResultStatus.SUCCESS),
            ),
            default=Value(RequestResultStatus.ERROR),
            output_field=PositiveSmallIntegerField(),
        )

        query = query.annotate(
            request_datetime=F('date_time'),
            result_status=result_status,
        )

        return query
