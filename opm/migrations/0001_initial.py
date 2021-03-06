# Generated by Django 2.1.2 on 2018-10-17 06:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('deviceid', models.AutoField(db_column='deviceID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'device',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('doctorid', models.AutoField(db_column='doctorID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'doctor',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('patientid', models.AutoField(db_column='patientID', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'patient',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RefUsertype',
            fields=[
                ('usertypeid', models.IntegerField(db_column='usertypeID', primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=45)),
            ],
            options={
                'db_table': 'ref_usertype',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('userid', models.IntegerField(db_column='userID', primary_key=True, serialize=False)),
                ('username', models.CharField(blank=True, max_length=45, null=True)),
                ('password', models.CharField(blank=True, max_length=45, null=True)),
                ('firstname', models.CharField(blank=True, db_column='firstName', max_length=45, null=True)),
                ('middlename', models.CharField(blank=True, db_column='middleName', max_length=45, null=True)),
                ('lastname', models.CharField(blank=True, db_column='lastName', max_length=45, null=True)),
                ('age', models.CharField(blank=True, max_length=45, null=True)),
                ('email', models.CharField(blank=True, max_length=45, null=True)),
                ('contactno', models.CharField(blank=True, max_length=45, null=True)),
                ('status', models.IntegerField(db_column='status')),
            ],
            options={
                'db_table': 'users',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PatientDevice',
            fields=[
                ('patient_patientid', models.ForeignKey(db_column='patient_patientID', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='opm.Patient')),
                ('inuse', models.IntegerField(db_column='inUse')),
                ('patient_devicecol', models.CharField(blank=True, max_length=45, null=True)),
            ],
            options={
                'db_table': 'patient_device',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Ecg',
            fields=[
                ('patientid', models.ForeignKey(db_column='patientID', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='opm.PatientDevice')),
                ('timestamp', models.DateTimeField()),
                ('data', models.FloatField()),
            ],
            options={
                'db_table': 'ecg',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Heartrate',
            fields=[
                ('patientid', models.ForeignKey(db_column='patientID', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='opm.PatientDevice')),
                ('timestamp', models.DateTimeField()),
                ('data', models.FloatField()),
            ],
            options={
                'db_table': 'heartrate',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Temperature',
            fields=[
                ('patientid', models.ForeignKey(db_column='patientID', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='opm.PatientDevice')),
                ('timestamp', models.DateTimeField()),
                ('data', models.FloatField()),
            ],
            options={
                'db_table': 'temperature',
                'managed': False,
            },
        ),
    ]
