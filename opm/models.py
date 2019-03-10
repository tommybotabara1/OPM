# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User
from aesfield.field import AESField



class RefUsertype(models.Model):
    usertypeid = models.IntegerField(db_column='usertypeID', primary_key=True)  # Field name made lowercase.
    type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'ref_usertype'

class Userdetails(models.Model):
    userid = models.IntegerField(db_column='userID', primary_key=True)  # Field name made lowercase.
    middlename = models.CharField(db_column='middleName', max_length=45, blank=True, null=True)  # Field name made lowercase.
    birthday = models.DateField(blank=True, null=True)
    contactno = models.CharField(max_length=45, blank=True, null=True)
    usertype = models.ForeignKey(RefUsertype, models.DO_NOTHING, db_column='userType')  # Field name made lowercase.
    auth_user_id = models.ForeignKey(User, models.DO_NOTHING, db_column='auth_user_id')
    sex = models.TextField()

    class Meta:
        managed = False
        db_table = 'userdetails'
        unique_together = (('userid', 'auth_user_id'),)


class Device(models.Model):
    deviceid = models.AutoField(db_column='deviceID', primary_key=True)  # Field name made lowercase.
    macaddress = models.CharField(db_column='macAddress', max_length=45)  # Field name made lowercase.
    status = models.IntegerField()
    borroweddate = models.DateTimeField(db_column='borrowedDate', blank=True, null=True)  # Field name made lowercase.
    returneddate = models.DateTimeField(db_column='returnedDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'device'


class Doctor(models.Model):
    doctorid = models.AutoField(db_column='doctorID', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey(Userdetails, models.DO_NOTHING, db_column='userID')  # Field name made lowercase.
    licensenumber = models.CharField(db_column='licenseNumber', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'doctor'
        unique_together = (('doctorid', 'userid'),)


class Patient(models.Model):
    patientid = models.AutoField(db_column='patientID', primary_key=True)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID')  # Field name made lowercase.
    userid = models.ForeignKey(Userdetails, models.DO_NOTHING, db_column='userID')  # Field name made lowercase.
    bloodtype = models.CharField(db_column='bloodType', max_length=45)  # Field name made lowercase.
    restrictmedicalinformationaccess = models.IntegerField(db_column='restrictMedicalInformationAccess')  # Field name made lowercase.
    restrictvitalsinformationaccess = models.IntegerField(db_column='restrictVitalsInformationAccess')  # Field name made lowercase.
    currentdeviceid = models.IntegerField(db_column='currentDeviceID')  # Field name made lowercase.
    deadlinereturndate = models.DateField(db_column='deadlineReturnDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient'
        unique_together = (('patientid', 'userid'),)


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
    remarks = models.CharField(db_column='remarks', max_length=120)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient_device'


class Ecg(models.Model):
    ecgid = models.IntegerField(db_column='ecgID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING,
                                        db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ecg'


class Heartrate(models.Model):
    heartrateid = models.IntegerField(db_column='heartrateID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.TextField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'heartrate'


class Temperature(models.Model):
    temperatureid = models.IntegerField(db_column='temperatureID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.TextField()
    batchid = models.IntegerField(db_column='batchID')  # Field name made lowercase.


    class Meta:
        managed = False
        db_table = 'temperature'


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


class RefTypeofvital(models.Model):
    typeofvitalid = models.IntegerField(db_column='typeOfVitalID', primary_key=True)  # Field name made lowercase.
    type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'ref_typeofvital'


class Comments(models.Model):
    commentid = models.IntegerField(db_column='commentID', primary_key=True)  # Field name made lowercase.
    comment = models.TextField()
    patientdeviceid = models.ForeignKey('PatientDevice', models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timestamp = models.DateTimeField()
    typeofvital = models.ForeignKey('RefTypeofvital', models.DO_NOTHING, db_column='typeOfVital')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'comments'


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


class Notifications(models.Model):
    notificationid = models.IntegerField(db_column='notificationID', primary_key=True)  # Field name made lowercase.
    notificationdescription = models.TextField(db_column='notificationDescription')  # Field name made lowercase.
    datetime = models.DateTimeField(db_column='dateTime')  # Field name made lowercase.
    userid = models.ForeignKey('Userdetails', models.DO_NOTHING, db_column='userID')  # Field name made lowercase.
    viewed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'notifications'


class Day(models.Model):
    dayid = models.IntegerField(db_column='dayID', primary_key=True)  # Field name made lowercase.
    actualday = models.CharField(db_column='actualDay', max_length=45, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'day'


class Time(models.Model):
    timeid = models.IntegerField(db_column='timeID', primary_key=True)  # Field name made lowercase.
    actualtime = models.CharField(db_column='actualTime', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'time'


class PatientSchedule(models.Model):
    patientscheduleid = models.IntegerField(db_column='patientScheduleID', primary_key=True)  # Field name made lowercase.
    patientdeviceid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientDeviceID')  # Field name made lowercase.
    timeid = models.ForeignKey('Time', models.DO_NOTHING, db_column='timeID')  # Field name made lowercase.
    dayid = models.ForeignKey(Day, models.DO_NOTHING, db_column='dayID')  # Field name made lowercase.
    earlyalert = models.CharField(db_column='earlyAlert', max_length=45, blank=True,
                                  null=True)  # Field name made lowercase.
    beforerecordalert = models.CharField(db_column='beforeRecordAlert', max_length=45, blank=True,
                                         null=True)  # Field name made lowercase.
    recordalert = models.CharField(db_column='recordAlert', max_length=45, blank=True,
                                   null=True)  # Field name made lowercase.
    latealert = models.CharField(db_column='lateAlert', max_length=45, blank=True,
                                 null=True)  # Field name made lowercase.
    lastalert = models.CharField(db_column='lastAlert', max_length=45, blank=True,
                                 null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'patient_schedule'


class Testing(models.Model):
    testing = models.IntegerField(primary_key=True)
    datatest = models.TextField(db_column='dataTest', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'testing'