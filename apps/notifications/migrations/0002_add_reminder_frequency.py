# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="reminder_frequency",
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text="Как часто отправлять напоминания в днях (от 1 до 7, не реже 1 раза в неделю)",
                verbose_name="Частота напоминаний (дни)",
            ),
        ),
    ]
