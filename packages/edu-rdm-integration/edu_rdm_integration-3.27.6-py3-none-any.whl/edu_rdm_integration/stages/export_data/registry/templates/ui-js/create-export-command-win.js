{% include "ui-js/collect-and-export-validators.js" %}

var periodStartField = Ext.getCmp('period_started_at');
var periodEndField = Ext.getCmp('period_ended_at');

Ext.onReady(function() {
    // Инициализация валидаторов
    initializeValidators();
});

function initializeValidators() {
    // Установка максимальной даты (завтра 23:59:59)
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 1);
    maxDate.setHours(23, 59, 59);

    periodStartField.setMaxValue(maxDate);
    periodEndField.setMaxValue(maxDate);

    // Устанавливаем время по умолчанию в календаре и доп валидатор
    setupPeriodFields(
        periodStartField,
        periodEndField,
    );
}