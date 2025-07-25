# Generated by Django 5.2 on 2025-06-11 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statement_tracker', '0002_bankstatement_modified_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankstatement',
            name='balance',
            field=models.CharField(default='0', help_text='Bank balance stored as text', max_length=20),
        ),
        migrations.AlterField(
            model_name='bankstatement',
            name='credit',
            field=models.CharField(blank=True, default='0', help_text='Credit amount', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatement',
            name='debit',
            field=models.CharField(blank=True, default='0', help_text='Debit amount', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatement',
            name='system_amount',
            field=models.CharField(blank=True, default='0', help_text='System amount', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatementchangehistory',
            name='balance',
            field=models.CharField(blank=True, help_text='Bank balance', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatementchangehistory',
            name='credit',
            field=models.CharField(blank=True, help_text='Credit amount', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatementchangehistory',
            name='debit',
            field=models.CharField(blank=True, help_text='Debit amount', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bankstatementchangehistory',
            name='system_amount',
            field=models.CharField(blank=True, help_text='System amount', max_length=10, null=True),
        ),
    ]
