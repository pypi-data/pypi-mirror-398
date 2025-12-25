from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ('edu_rdm_integration_transfer_pipeline', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transferredentity',
            name='interval_delta',
            field=models.PositiveIntegerField(default=60, verbose_name='Дельта разбиения периода на интервалы, мин.'),
        ),
        migrations.AddField(
            model_name='transferredentity',
            name='startup_period_collect_data',
            field=models.PositiveIntegerField(default=0, verbose_name='Период запуска сбора данных, мин.'),
        ),
    ]
