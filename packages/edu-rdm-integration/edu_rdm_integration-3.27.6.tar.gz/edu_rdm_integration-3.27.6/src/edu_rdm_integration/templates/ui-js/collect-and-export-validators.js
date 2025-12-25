function logsPeriodsValidator(startField, endField) {
    if (
        startField.getValue() &&
        endField.getValue() &&
        startField.getValue() > endField.getValue()
    ) {
        return 'Дата конца периода не может быть меньше даты начала периода';
    }
    return true;
}

function setupPeriodFields(startField, endField) {
    // Функция валидации обоих полей
    function validatePeriodFields() {
        startField.validate();
        endField.validate();
    }

    // Установка времени начала по умолчанию 00:00:00
    function setDefaultStartTime() {
        if (!startField.getValue()) {
            const defaultDateTime = new Date();
            defaultDateTime.setHours(0, 0, 0);
            startField.setValue(defaultDateTime);
        }
    }

    // Установка времени конца по умолчанию 23:59:59
    function setDefaultEndTime() {
        if (!endField.getValue()) {
            const defaultDateTime = new Date();
            defaultDateTime.setHours(23, 59, 59);
            endField.setValue(defaultDateTime);
        }
    }

    // Настройка обработчиков для поля начала периода
    startField.menu.on('beforeshow', setDefaultStartTime);
    startField.on('change', validatePeriodFields);
    startField.on('select', validatePeriodFields);

    // Настройка обработчиков для поля конца периода
    endField.menu.on('beforeshow', setDefaultEndTime);
    endField.on('change', validatePeriodFields);
    endField.on('select', validatePeriodFields);

    // Установка валидаторов
    startField.validator = function() {
        return logsPeriodsValidator(startField, endField);
    };
    endField.validator = function() {
        return logsPeriodsValidator(startField, endField);
    };
}