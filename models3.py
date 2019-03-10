# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Alerts(models.Model):
    alertid = models.AutoField(db_column='alertID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    typeofvital = models.ForeignKey('RefTypeofvital', models.DO_NOTHING, db_column='typeOfVital')  # Field name made lowercase.
    data = models.FloatField()
    timestamp = models.DateTimeField()
    viewed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'alerts'


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


class Comments(models.Model):
    commentid = models.AutoField(db_column='commentID', primary_key=True)  # Field name made lowercase.
    comment = models.TextField()
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    typeofvital = models.IntegerField(db_column='typeOfVital')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'comments'


class Day(models.Model):
    dayid = models.IntegerField(db_column='dayID', primary_key=True)  # Field name made lowercase.
    actualday = models.CharField(db_column='actualDay', max_length=45, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'day'


class Device(models.Model):
    deviceid = models.AutoField(db_column='deviceID', primary_key=True)  # Field name made lowercase.
    macaddress = models.CharField(db_column='macAddress', max_length=45)  # Field name made lowercase.
    status = models.IntegerField()
    borroweddate = models.DateTimeField(db_column='borrowedDate', blank=True, null=True)  # Field name made lowercase.
    returneddate = models.DateTimeField(db_column='returnedDate', blank=True, null=True)  # Field name made lowercase.

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
    licensenumber = models.CharField(db_column='licenseNumber', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'doctor'
        unique_together = (('doctorid', 'userid'),)


class Ecg(models.Model):
    ecgid = models.AutoField(db_column='ecgID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ecg'


class Heartrate(models.Model):
    heartrateid = models.AutoField(db_column='heartrateID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.TextField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'heartrate'


class Notifications(models.Model):
    notificationid = models.AutoField(db_column='notificationID', primary_key=True)  # Field name made lowercase.
    notificationdescription = models.TextField(db_column='notificationDescription')  # Field name made lowercase.
    datetime = models.DateTimeField(db_column='dateTime')  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='userID')  # Field name made lowercase.
    viewed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'notifications'


class Patient(models.Model):
    patientid = models.AutoField(db_column='patientID', primary_key=True)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID')  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='userID')  # Field name made lowercase.
    bloodtype = models.CharField(db_column='bloodType', max_length=45, blank=True, null=True)  # Field name made lowercase.
    restrictmedicalinformationaccess = models.IntegerField(db_column='restrictMedicalInformationAccess', blank=True, null=True)  # Field name made lowercase.
    restrictvitalsinformationaccess = models.IntegerField(db_column='restrictVitalsInformationAccess', blank=True, null=True)  # Field name made lowercase.
    currentdeviceid = models.IntegerField(db_column='currentDeviceID')  # Field name made lowercase.
    deadlinereturndate = models.DateField(db_column='deadlineReturnDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient'
        unique_together = (('patientid', 'userid'),)


class PatientDevice(models.Model):
    patientdeviceid = models.IntegerField(db_column='patientDeviceID', primary_key=True)  # Field name made lowercase.
    patient_patientid = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_patientID')  # Field name made lowercase.
    device_deviceid = models.ForeignKey(Device, models.DO_NOTHING, db_column='device_deviceID')  # Field name made lowercase.
    inuse = models.IntegerField(db_column='inUse')  # Field name made lowercase.
    isrecording = models.IntegerField(db_column='isRecording', blank=True, null=True)  # Field name made lowercase.
    recordingduration = models.IntegerField(db_column='recordingDuration', blank=True, null=True)  # Field name made lowercase.
    mintemperature = models.FloatField(db_column='minTemperature', blank=True, null=True)  # Field name made lowercase.
    maxtemperature = models.FloatField(db_column='maxTemperature', blank=True, null=True)  # Field name made lowercase.
    minheartrate = models.IntegerField(db_column='minHeartrate', blank=True, null=True)  # Field name made lowercase.
    maxheartrate = models.IntegerField(db_column='maxHeartrate', blank=True, null=True)  # Field name made lowercase.
    remarks = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_device'


class PatientDoctor(models.Model):
    patientdoctorid = models.IntegerField(db_column='patientDoctorID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patientID', blank=True, null=True)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID', blank=True, null=True)  # Field name made lowercase.
    restrictmedicalinformationaccess = models.IntegerField(db_column='restrictMedicalInformationAccess', blank=True, null=True)  # Field name made lowercase.
    restrictvitalsinformationaccess = models.IntegerField(db_column='restrictVitalsInformationAccess', blank=True, null=True)  # Field name made lowercase.
    assigneddoctor = models.IntegerField(db_column='assignedDoctor', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient_doctor'


class PatientMedicalHistory(models.Model):
    patient_medical_historyid = models.IntegerField(db_column='patient_medical_historyID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    date = models.DateField()
    presentcomplaint = models.TextField(db_column='presentComplaint')  # Field name made lowercase.
    historyofpresentcomplaint = models.TextField(db_column='historyOfPresentComplaint')  # Field name made lowercase.
    pastmedicalhistory = models.TextField(db_column='pastMedicalHistory', blank=True, null=True)  # Field name made lowercase.
    drughistory = models.TextField(db_column='drugHistory', blank=True, null=True)  # Field name made lowercase.
    familyhistory = models.TextField(db_column='familyHistory', blank=True, null=True)  # Field name made lowercase.
    socialhistory = models.TextField(db_column='socialHistory', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient_medical_history'


class PatientSchedule(models.Model):
    patientscheduleid = models.AutoField(db_column='patientScheduleID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timeid = models.ForeignKey('Time', models.DO_NOTHING, db_column='timeID')  # Field name made lowercase.
    dayid = models.ForeignKey(Day, models.DO_NOTHING, db_column='dayID')  # Field name made lowercase.
    earlyalert = models.IntegerField(db_column='earlyAlert', blank=True, null=True)  # Field name made lowercase.
    beforerecordalert = models.IntegerField(db_column='beforeRecordAlert', blank=True, null=True)  # Field name made lowercase.
    recordalert = models.IntegerField(db_column='recordAlert', blank=True, null=True)  # Field name made lowercase.
    latealert = models.IntegerField(db_column='lateAlert', blank=True, null=True)  # Field name made lowercase.
    lastalert = models.IntegerField(db_column='lastAlert', blank=True, null=True)  # Field name made lowercase.
    accomplished = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_schedule'


class Presets(models.Model):
    presetid = models.IntegerField(db_column='presetID', primary_key=True)  # Field name made lowercase.
    presetname = models.CharField(db_column='presetName', max_length=45)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID')  # Field name made lowercase.
    recordingduration = models.IntegerField(db_column='recordingDuration', blank=True, null=True)  # Field name made lowercase.
    mintemperature = models.FloatField(db_column='minTemperature', blank=True, null=True)  # Field name made lowercase.
    maxtemperature = models.FloatField(db_column='maxTemperature', blank=True, null=True)  # Field name made lowercase.
    minheartrate = models.IntegerField(db_column='minHeartrate', blank=True, null=True)  # Field name made lowercase.
    maxheartrate = models.IntegerField(db_column='maxHeartRate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'presets'


class RefTypeofvital(models.Model):
    typeofvitalid = models.IntegerField(db_column='typeOfVitalID', primary_key=True)  # Field name made lowercase.
    type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'ref_typeofvital'


class RefUsertype(models.Model):
    usertypeid = models.IntegerField(db_column='usertypeID', primary_key=True)  # Field name made lowercase.
    type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'ref_usertype'


class Temperature(models.Model):
    temperatureid = models.AutoField(db_column='temperatureID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'temperature'


class Testing(models.Model):
    testing = models.IntegerField(primary_key=True)
    datatest = models.TextField(db_column='dataTest', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'testing'


class Time(models.Model):
    timeid = models.IntegerField(db_column='timeID', primary_key=True)  # Field name made lowercase.
    actualtime = models.CharField(db_column='actualTime', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'time'


class Userdetails(models.Model):
    userid = models.IntegerField(db_column='userID', primary_key=True)  # Field name made lowercase.
    middlename = models.CharField(db_column='middleName', max_length=45, blank=True, null=True)  # Field name made lowercase.
    birthday = models.DateField(blank=True, null=True)
    contactno = models.CharField(max_length=45, blank=True, null=True)
    usertype = models.ForeignKey(RefUsertype, models.DO_NOTHING, db_column='userType')  # Field name made lowercase.
    auth_user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    sex = models.TextField()

    class Meta:
        managed = False
        db_table = 'userdetails'
        unique_together = (('userid', 'auth_user'),)
