from django.contrib import admin

from .models import Device, Doctor, Ecg, Heartrate, Patient, PatientDevice, RefUsertype, Temperature, Userdetails

admin.site.register(Device)
admin.site.register(Doctor)
admin.site.register(Ecg)
admin.site.register(Heartrate)
admin.site.register(Patient)
admin.site.register(PatientDevice)
admin.site.register(RefUsertype)
admin.site.register(Temperature)
admin.site.register(Userdetails)

# Register your models here.
