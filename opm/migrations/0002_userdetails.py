# Generated by Django 2.1.2 on 2018-10-21 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Userdetails',
            fields=[
                ('userid', models.IntegerField(db_column='userID', primary_key=True, serialize=False)),
                ('middlename', models.CharField(blank=True, db_column='middleName', max_length=45, null=True)),
                ('birthday', models.DateField(blank=True, null=True)),
                ('email', models.CharField(blank=True, max_length=45, null=True)),
                ('contactno', models.CharField(blank=True, max_length=45, null=True)),
                ('usertype', models.IntegerField(db_column='userType')),
                ('auth_user_id', models.IntegerField()),
            ],
            options={
                'db_table': 'users',
                'managed': False,
            },
        ),
    ]
