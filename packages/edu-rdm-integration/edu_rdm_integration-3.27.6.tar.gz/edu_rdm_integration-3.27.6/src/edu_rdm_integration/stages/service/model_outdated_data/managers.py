import importlib
from typing import (
    TYPE_CHECKING,
    Optional,
)

from edu_rdm_integration.rdm_models.models import (
    RDMModelEnum,
)


if TYPE_CHECKING:
    from m3_db_utils.models import (
        ModelEnumValue,
    )


class ModelOutdatedDataCleanerManager:
    """Управляет очисткой устаревших данных моделей РВД.

    Получает все модели РВД зарегистрированные в модели-перечислении edu_rdm_integration.rdm_models.models.RDMModelEnum.
    У каждой модели проверяет наличие поля outdated_data_cleaners. Если такое поле есть, то инстанцирует его и вызывает
    метод run.
    """

    def __init__(
        self,
        *args,
        models: Optional[list[str]] = None,
        safe: bool = False,
        log_sql: bool = False,
        **kwargs,
    ):
        self._models = models
        self._safe = safe
        self._log_sql = log_sql

        super().__init__(*args, **kwargs)

    def _process_model(self, model_enum_value: 'ModelEnumValue'):
        """Обрабатывает модель РВД."""
        if not hasattr(model_enum_value, 'outdated_data_cleaners'):
            return

        for outdated_data_cleaner in model_enum_value.outdated_data_cleaners:
            if isinstance(outdated_data_cleaner, str):
                outdated_data_cleaner_module_path, cleaner_name = outdated_data_cleaner.rsplit('.', 1)
                outdated_data_cleaner_module = importlib.import_module(outdated_data_cleaner_module_path)
                outdated_data_cleaner = getattr(outdated_data_cleaner_module, cleaner_name)

            outdated_data_cleaner(model_enum_value=model_enum_value, safe=self._safe, log_sql=self._log_sql).run()

    def _process_models(self):
        """Обрабатывает все модели РВД."""
        for model_enum_value in RDMModelEnum.get_model_enum_values():
            if self._models is not None and model_enum_value.key not in self._models:
                continue

            self._process_model(model_enum_value=model_enum_value)

    def run(self):
        """Запускает очистку устаревших данных моделей РВД."""
        self._process_models()
