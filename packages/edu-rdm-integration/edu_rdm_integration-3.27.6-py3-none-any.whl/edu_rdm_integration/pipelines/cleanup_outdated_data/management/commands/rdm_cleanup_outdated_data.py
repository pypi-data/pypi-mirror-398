from django.conf import (
    settings,
)
from django.core.management import (
    BaseCommand,
)

from edu_rdm_integration.rdm_models.models import (
    RDMModelEnum,
)
from edu_rdm_integration.stages.service.model_outdated_data.managers import (
    ModelOutdatedDataCleanerManager,
)
from edu_rdm_integration.stages.service.service_outdated_data.managers import (
    ServiceOutdatedDataCleanerManager,
)


class Command(BaseCommand):
    """Ночная команда для очистки устаревших данных РВД."""

    nightly_script = True

    help = 'Ночная команда для очистки устаревших данных РВД.'

    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        models = ', '.join(f'{key} - {value.title}' for key, value in RDMModelEnum.get_enum_data().items())
        models_help_text = (
            f'Значением параметра является перечисление моделей РВД, для которых должна быть произведена зачистка '
            f'устаревших данных. '
            f'Перечисление моделей:\n{models}. Если модели не указываются, то зачистка устаревших данных будет '
            f'производиться для всех моделей. Модели перечисляются через запятую без пробелов.'
        )
        parser.add_argument(
            '--models',
            action='store',
            dest='models',
            type=lambda ml: [m.strip().upper() for m in ml.split(',')] if ml else None,
            help=models_help_text,
        )

        # Аргумент для сервисных стадий
        stages_help_text = (
            'Значением параметра является перечисление стадий сервисных данных, '
            'для которых должна быть произведена зачистка устаревших данных. '
            'Перечисление этапов: collect, export, upload. '
            'Если стадии не указываются, то зачистка будет произведена для всех стадий. '
            'Стадии перечисляются через запятую без пробелов.'
        )
        parser.add_argument(
            '--stages',
            action='store',
            dest='stages',
            type=lambda st: [s.strip().lower() for s in st.split(',')] if st else None,
            help=stages_help_text,
        )

        parser.add_argument(
            '--safe',
            action='store_true',
            dest='safe',
            default=False,
            help='Запускать команду в безопасном режиме (без удаления данных, только логирование).',
        )

        parser.add_argument(
            '--log-sql',
            action='store_true',
            dest='log_sql',
            default=False,
            help='Включить логирование SQL-запросов, выполняемых во время работы команды.',
        )

    def _cleanup_model_outdated_data(self, options):
        """Очистка устаревших данных моделей РВД."""
        model_data_cleaner_manager = ModelOutdatedDataCleanerManager(
            models=options['models'],
            safe=options['safe'],
            log_sql=options['log_sql'],
        )
        model_data_cleaner_manager.run()

    def _cleanup_service_outdated_data(self, options):
        """Очистка устаревших данных сервисных моделей РВД."""
        service_data_cleaner_manager = ServiceOutdatedDataCleanerManager(
            stages=options['stages'],
            safe=options['safe'],
            log_sql=options['log_sql'],
        )
        service_data_cleaner_manager.run()

    def handle(self, *args, **options):
        """Запуск очистки устаревших данных РВД."""
        if settings.RDM_ENABLE_CLEANUP_MODELS_OUTDATED_DATA:
            self._cleanup_model_outdated_data(options)

        if settings.RDM_ENABLE_CLEANUP_SERVICE_OUTDATED_DATA:
            self._cleanup_service_outdated_data(options)
