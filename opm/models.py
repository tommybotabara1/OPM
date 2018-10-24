# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User


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

    class Meta:
        managed = False
        db_table = 'userdetails'
        unique_together = (('userid', 'auth_user_id'),)


class Device(models.Model):
    deviceid = models.AutoField(db_column='deviceID', primary_key=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'device'


class Doctor(models.Model):
    doctorid = models.AutoField(db_column='doctorID', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey(Userdetails, models.DO_NOTHING, db_column='userID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'doctor'
        unique_together = (('doctorid', 'userid'),)

class Patient(models.Model):
    patientid = models.AutoField(db_column='patientID', primary_key=True)  # Field name made lowercase.
    doctorid = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctorID')  # Field name made lowercase.
    userid = models.ForeignKey(Userdetails, models.DO_NOTHING, db_column='userID')  # Field name made lowercase.

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

class Ecg(models.Model):
    ecgid = models.AutoField(db_column='ecgID', primary_key=True)
    patientid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey(PatientDevice, related_name='ecgdevices', db_column='deviceID', on_delete=models.CASCADE)  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'ecg'
        unique_together = (('patientid', 'deviceid'),)


class Heartrate(models.Model):
    heartrateid = models.AutoField(db_column='heartrateID', primary_key=True)
    patientid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey(PatientDevice, related_name='heartratedevices', db_column='deviceID', on_delete=models.CASCADE)  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'heartrate'
        unique_together = (('patientid', 'deviceid'),)


class Temperature(models.Model):
    temperatureid = models.AutoField(db_column='temperatureID', primary_key=True)
    patientid = models.ForeignKey(PatientDevice, models.DO_NOTHING, db_column='patientID')  # Field name made lowercase.
    deviceid = models.ForeignKey(PatientDevice, related_name='temperaturedevices', db_column='deviceID', on_delete=models.CASCADE)  # Field name made lowercase.
    timestamp = models.DateTimeField()
    data = models.FloatField()

    class Meta:
        managed = False
        db_table = 'temperature'
        unique_together = (('patientid', 'deviceid'),)


