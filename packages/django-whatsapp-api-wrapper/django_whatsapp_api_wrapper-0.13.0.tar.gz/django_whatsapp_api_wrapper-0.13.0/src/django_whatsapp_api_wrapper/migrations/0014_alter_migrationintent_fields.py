# Make destination_waba_id and solution_id optional for Tech Partners

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_whatsapp_api_wrapper", "0013_migrationintent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="migrationintent",
            name="destination_waba_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Target WABA ID (filled after Embedded Signup)",
                max_length=50,
                verbose_name="Destination WABA ID",
            ),
        ),
        migrations.AlterField(
            model_name="migrationintent",
            name="solution_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Not used for Tech Partners (only for MPS)",
                max_length=50,
                verbose_name="Solution ID",
            ),
        ),
    ]
