# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Device(models.Model):
    deviceid = models.AutoField(db_column='deviceID', primary_key=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'device'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Doctor(models.Model):
    doctorid = models.AutoField(db_column='doctorID', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='userID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'doctor'
        unique_together = (('doctorid', 'userid'),)


class Ecg(models.Model):
    ecgid = models.IntegerField(db_column='ecgID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='deviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'ecg'


class Heartrate(models.Model):
    heartrateid = models.IntegerField(db_column='heartrateID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='deviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'heartrate'


class Patient(models.Model):
    patientid = models.AutoField(db_column='patientID', primary_key=True)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID')  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='userID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient'
        unique_together = (('patientid', 'userid'),)


class PatientDevice(models.Model):
    patient_patientid = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_patientID', primary_key=True)  # Field name made lowercase.
    device_deviceid = models.ForeignKey(Device, models.DO_NOTHING, db_column='device_deviceID')  # Field name made lowercase.
    inuse = models.IntegerField(db_column='inUse')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient_device'
        unique_together = (('patient_patientid', 'device_deviceid'),)


class RefUsertype(models.Model):
    usertypeid = models.IntegerField(db_column='usertypeID', primary_key=True)  # Field name made lowercase.
    type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'ref_usertype'


class Temperature(models.Model):
    temperatureid = models.IntegerField(db_column='temperatureID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='deviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'temperature'


class Userdetails(models.Model):
    userid = models.IntegerField(db_column='userID', primary_key=True)  # Field name made lowercase.
    middlename = models.CharField(db_column='middleName', max_length=45, blank=True, null=True)  # Field name made lowercase.
    birthday = models.DateField(blank=True, null=True)
    email = models.CharField(max_length=45, blank=True, null=True)
    contactno = models.CharField(max_length=45, blank=True, null=True)
    usertype = models.IntegerField(db_column='userType')  # Field name made lowercase.
    auth_user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'userdetails'
        unique_together = (('userid', 'auth_user_id'),)
