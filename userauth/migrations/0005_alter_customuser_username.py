# Generated by Django 4.2.6 on 2023-10-20 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("userauth", "0004_rename_new_user_userprofile_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="username",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]