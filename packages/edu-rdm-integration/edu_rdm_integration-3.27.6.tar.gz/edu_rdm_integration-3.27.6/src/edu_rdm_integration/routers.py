from django.apps import (
    apps,
)
from django.conf import (
    settings,
)
from django.db.utils import (
    DEFAULT_DB_ALIAS,
)


app_configs = apps.get_app_configs()


class RdmRouter:
    """Роутер, направляющий все запросы к моделям из приложения 'edu_rdm_integration' в базу данных 'rdm_db'."""

    db_name = 'rdm'
    # Имена моделей, для исключение из БД РВД подключенных приложений.
    exclude_rdm_db_model_names = set()

    def __init__(self):
        # Получаем путь через AppConfig одного из приложений в пакете
        try:
            package_app_config = apps.get_app_config('edu_rdm_integration')
            base_package_path = package_app_config.path
        except LookupError:
            # Обработка случая, если приложение 'edu_rdm_integration' не найдено
            base_package_path = None

        self.use_rdm_db = getattr(settings, 'USE_RDM_DB', False)
        self.edu_rdm_apps = self._get_edu_rdm_apps(base_package_path)
        self.exclude_rdm_db_model_names = {model_name.lower() for model_name in self.exclude_rdm_db_model_names}

    def _get_edu_rdm_apps(self, base_package_path):
        """Динамически определяет приложения, которые находятся в пакете 'edu_rdm_integration'."""
        app_labels = []
        for app_config in apps.get_app_configs():
            if app_config.path.startswith(base_package_path):
                app_labels.append(app_config.label)

        # добавляем таблицу uploader_client_entry
        app_labels.append('uploader_client')

        return app_labels

    def is_rdm_app(self, app_label: str, model_name: str) -> bool:
        """Проверяет, что модель и приложение относится к РВД.

        Args:
            app_label: Название приложения
            model_name: Название модели
        Returns: Относится ли приложение и модель к РВД
        """
        return app_label in self.edu_rdm_apps and model_name not in self.exclude_rdm_db_model_names

    def db_for_read(self, model, **hints):
        return self.db_for_write(model, **hints)

    def db_for_write(self, model, **hints):
        res = None
        if self.is_rdm_app(model._meta.app_label, model.__name__.lower()) and self.use_rdm_db:
            res = self.db_name

        return res

    def allow_relation(self, obj1, obj2, **hints):
        # Если оба объекта принадлежат 'edu_rdm_integration', то отношения между ними разрешены.
        is_rdm_app1 = self.is_rdm_app(obj1._meta.app_label, obj1._meta.model.__name__.lower())
        is_rdm_app2 = self.is_rdm_app(obj2._meta.app_label, obj2._meta.model.__name__.lower())
        is_allow = False

        # Разрешить отношения, если оба объекта из RDM-приложений.
        if is_rdm_app1 and is_rdm_app2:
            is_allow = True
        # Если ни один из объектов не принадлежит RDM-приложениям, обработка делегируется следующим роутерам.
        elif not is_rdm_app1 and not is_rdm_app2:
            is_allow = None

        return is_allow

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        model_name = model_name.lower() if model_name else ''
        is_rdm_app = self.is_rdm_app(app_label, model_name)
        is_allow = None

        if is_rdm_app:
            if db == self.db_name and self.use_rdm_db or db == DEFAULT_DB_ALIAS and not self.use_rdm_db:
                is_allow = True
            else:
                is_allow = False
        elif db == self.db_name and not is_rdm_app:
            is_allow = False

        return is_allow
