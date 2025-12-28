from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0002_categorysuggestion"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CategorySuggestion",
        ),
    ]
