# Generated by Django 5.1.5 on 2025-02-04 16:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coderr_app', '0006_alter_review_rating'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='offer',
            options={'ordering': ['-updated_at']},
        ),
    ]
