from django.shortcuts import render, HttpResponse, redirect, get_object_or_404, HttpResponseRedirect, Http404

from .models import *
from .forms import *
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import *
from django.http import JsonResponse
import paho.mqtt.client as mqtt
import datetime
from django.db.models import F
import time
import serial



# Create your views here.
def index(request):
    logout(request)
    form = LoginForm()
    try:
        del request.session['user_id']
    except KeyError:
        pass
    return render(request, 'login/index.html', {'form': form})


def loginuser(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                request.session['user_id'] = user.id
                return redirect(home)

            else:
                return redirect('index')


@login_required()
def home(request):
    if request.session['user_id'] is not None:
        userdetails = Userdetails.objects.get(auth_user_id=request.session['user_id'])

        context = {'user_id': request.session['user_id'],
                   'user_details': userdetails}

        if userdetails.usertype.usertypeid == 1:
            return render(request, 'home/systemAdminBody.html', context)
        elif userdetails.usertype.usertypeid == 2:
            return render(request, 'home/adminBody.html', context)
        elif userdetails.usertype.usertypeid == 3:
            return render(request, 'home/doctorBody.html', context)
        elif userdetails.usertype.usertypeid == 4:
            patient_object = Patient.objects.get(userid=request.session['user_id'])
            context = {'user_id': request.session['user_id'],
                       'user_details': userdetails,
                       'patient_object': patient_object,
                       }
            return render(request, 'home/patientBody.html', context)

    else:
        return redirect('index')


@login_required()
def listofusers(request):
    current_user_type = Userdetails.objects.get(auth_user_id=request.user.id).usertype_id
    user_list = User.objects.order_by('id')
    user_details_list = Userdetails.objects.order_by('userid')
    context = {'user_list': user_list,
               'user_id': request.session['user_id'],
               'user_details_list': user_details_list,
               'current_user_type': current_user_type}
    return render(request, 'listofusers/listOfUsers.html', context)


@login_required()
def filloutmedicalform(request):
    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            if PatientMedicalHistory.objects.count() == 0:
                patientmedicalhistoryid = 1
            else:
                patientmedicalhistoryid = PatientMedicalHistory.objects.latest('patient_medical_historyid').patient_medical_historyid + 1

            patientobject = Patient.objects.get(patientid=request.POST['patientid'])

            newPatientMedicalHistory = PatientMedicalHistory(
                patient_medical_historyid=patientmedicalhistoryid,
                patientid=patientobject,
                date=datetime.date.today(),
                presentcomplaint=request.POST['presentcomplaint'],
                historyofpresentcomplaint=request.POST['historyofpresentcomplaint'],
                pastmedicalhistory=request.POST['pastmedicalhistory'],
                drughistory=request.POST['drughistory'],
                familyhistory=request.POST['familyhistory'],
                socialhistory=request.POST['socialhistory'],
            )

            newPatientMedicalHistory.save()
            form = MedicalHistoryForm()
            context = {'form': form,
                       'message': "Medical Form Created",
                       }
            return render(request, 'filloutmedicalform/medicalForm.html', context)
    else:
        form = MedicalHistoryForm()
        context = {'form': form,
                   'message': "Create",
                   }
        return render(request, 'filloutmedicalform/medicalForm.html', context)


@login_required()
def createuser(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            if request.POST['password'] != request.POST['repeatPassword']:
                return HttpResponse("Password does not match!")
            if User.objects.filter(username=request.POST['username']).exists():
                return HttpResponse("Username exists!")

            validate_password(request.POST['password'])

            user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
            user.last_name = request.POST['lastname']
            user.first_name = request.POST['firstname']
            user.save()

            user = User.objects.get(username=request.POST['username'])

            usertype = RefUsertype.objects.get(usertypeid=request.POST['usertype'])

            newUserDetail = Userdetails(
                userid=user.id,
                middlename=request.POST['middlename'],
                birthday=request.POST['birthday'],
                contactno=request.POST['contactno'],
                usertype=usertype,
                auth_user_id=User.objects.get(id=user.id)
            )

            newUserDetail.save()

            if request.POST['usertype'] == '3':
                if Doctor.objects.count() == 0:
                    doctorid = 1
                else:
                    doctorid = Doctor.objects.latest('doctorid').doctorid + 1

                latestdoctoruser = Userdetails.objects.latest('userid')
                newDoctor = Doctor(
                    doctorid=doctorid,
                    userid=latestdoctoruser
                )

                newDoctor.save()
                return redirect('createuser')
            else:
                if Patient.objects.count() == 0:
                    patientid = 1
                else:
                    patientid = Patient.objects.latest('patientid').patientid + 1

                latestpatientuser = Userdetails.objects.latest('userid')
                doctor = Doctor.objects.get(doctorid=request.POST['doctorid'])
                newPatient = Patient(
                    patientid=patientid,
                    doctorid=doctor,
                    userid=latestpatientuser,
                    bloodtype=request.POST['bloodtype'],
                )

                newPatient.save()
                return redirect('createuser')
        else:
            return HttpResponse("bobo ka")
    else:
        form = CreateUserForm()
        return render(request, 'createusers/createUser.html', {'form': form})


@login_required()
def changeuserofdevice(request):
    patient_device_list = PatientDevice.objects.order_by('device_deviceid').all()
    device_list = Device.objects.order_by('deviceid').all()
    patient_list = Patient.objects.filter(userid__auth_user_id__is_active=1)

    context = {'patient_device_list': patient_device_list,
               'device_list': device_list,
               'patient_list': patient_list
               }

    return render(request, 'changeuserofdevice/changeUserOfDevice.html', context)


@login_required()
def viewassignedpatients(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)

    context = {'doctorid': doctorid,
               'patient_device_list': patient_device_list,
               }
    return render(request, 'viewassignedpatients/viewAssignedPatients.html', context)


@login_required()
def assignedpatientvitals(request, patient_id):
    currentdate = datetime.date.today()
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
    temperature_list = Temperature.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)
    heartrate_list = Heartrate.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)[:1000]

    if not temperature_list.exists():
        temperature_list = Temperature.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid)

    if not heartrate_list.exists():
        heartrate_list = Heartrate.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid)

    if not ecg_list.exists():
        ecg_list = Ecg.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid)

    if temperature_list.exists():
        latest_temperature = temperature_list.latest('timestamp')
    else:
        latest_temperature = -1
    if heartrate_list.exists():
        latest_heartrate = heartrate_list.latest('timestamp')
    else:
        latest_heartrate = -1
    if ecg_list.exists():
        latest_ecg = ecg_list.all()[ecg_list.count() - 1]
    else:
        latest_ecg = -1

    ecg_list_all = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=currentdate)

    ecg_list_batch_values = ecg_list_all.values_list('batchid', flat=True).distinct()

    batch_list = []
    for batch in ecg_list_batch_values:
        if not batch_list.__contains__(int(batch)):
            batch_list.append(int(batch))

    ecg_batch_start_end_time = []
    for batch in batch_list:
        current_batch_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=currentdate, batchid=batch)
        start_time = current_batch_list.first().timestamp
        end_time = current_batch_list.last().timestamp

        ecg_batch_start_end_time.append({
            'batchid': batch,
            'start_time': start_time.time().strftime('%I:%M:%S %p'),
            'end_time': end_time.time().strftime('%I:%M:%S %p'),
        })


    pagefrom = 1

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'latest_temperature': latest_temperature,
               'heartrate_list': heartrate_list,
               'latest_heartrate': latest_heartrate,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def assignedpatientmedicalinfo(request, patient_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientmedicalinfo = PatientMedicalHistory.objects.filter(patientid=patient.patientid)
    if patientmedicalinfo.exists():
        patientmedicalinfo = patientmedicalinfo.latest('date')
    else:
        patientmedicalinfo = -1
    pagefrom = 1
    context = {'patient': patient,
               'patientmedicalinfo': patientmedicalinfo,
               'pagefrom': pagefrom
               }

    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def assignedpatientrecords(request, patient_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientdevice = PatientDevice.objects.filter(patient_patientid=patient.patientid)
    patient_medical_history_list = PatientMedicalHistory.objects.filter(patientid=patient_id)
    temperature_distinct_date_records = Temperature.objects.filter(patientdeviceid__in=patientdevice)
    temperature_distinct_date_records = temperature_distinct_date_records.values_list('timestamp', flat=True).distinct()

    vitals_dates_list = []
    for temperature_data in temperature_distinct_date_records:
        if not vitals_dates_list.__contains__(temperature_data.date()):
            vitals_dates_list.append(temperature_data.date())

    vitals_dates_list_size = vitals_dates_list.__len__()
    context = {'patient': patient,
               'patient_medical_history_list': patient_medical_history_list,
               'vitals_dates_list': vitals_dates_list,
               'vitals_dates_list_size': vitals_dates_list_size
               }

    return render(request, 'patientrecords/patientRecords.html', context)

@login_required()
def assignedpatientrecordsmedicalhistory(request, patient_id, medical_history_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientmedicalinfo = PatientMedicalHistory.objects.get(patient_medical_historyid=medical_history_id)
    pagefrom = 2
    context = {'patient': patient,
               'patientmedicalinfo': patientmedicalinfo,
               'pagefrom': pagefrom
               }
    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def assignedpatientrecordsvitalrecords(request, patient_id, date):
    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
    temperature_list = Temperature.objects.order_by(F('timestamp').desc()).filter(
        patientdeviceid=patient_device.patientdeviceid, timestamp__date=convert_date)
    heartrate_list = Heartrate.objects.order_by(F('timestamp').desc()).filter(
        patientdeviceid=patient_device.patientdeviceid, timestamp__date=convert_date)
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                  timestamp__date=convert_date)

    latest_temperature = temperature_list.latest('timestamp')
    latest_heartrate = heartrate_list.latest('timestamp')
    latest_ecg = ecg_list.latest('timestamp')

    ecg_list = ecg_list.all()[:1000]

    ecg_list_all = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=convert_date)

    ecg_list_batch_values = ecg_list_all.values_list('batchid', flat=True).distinct()

    batch_list = []
    for batch in ecg_list_batch_values:
        if not batch_list.__contains__(int(batch)):
            batch_list.append(int(batch))

    ecg_batch_start_end_time = []
    for batch in batch_list:
        current_batch_list = Ecg.objects.order_by(F('timestamp').asc()).filter(
            patientdeviceid=patient_device.patientdeviceid,
            timestamp__date=convert_date, batchid=batch)
        start_time = current_batch_list.first().timestamp
        end_time = current_batch_list.last().timestamp

        ecg_batch_start_end_time.append({
            'batchid': batch,
            'start_time': start_time.time().strftime('%I:%M:%S %p'),
            'end_time': end_time.time().strftime('%I:%M:%S %p'),
        })

    pagefrom = 2

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'latest_temperature': latest_temperature,
               'heartrate_list': heartrate_list,
               'latest_heartrate': latest_heartrate,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def managedevicerecording(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)

    context = {
        'patient_device_list': patient_device_list
    }
    return render(request, 'managedevicerecording/manageDeviceRecording.html', context)


@login_required()
def notifications(request):
    return render(request, 'notifications/notifications.html')


@login_required()
def viewcurrentvitals(request):
    patient = Patient.objects.get(userid=request.session['user_id'])
    patient_id = patient.patientid
    currentdate = datetime.date.today()
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
    temperature_list = Temperature.objects.order_by(F('timestamp').desc()).filter(
        patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)
    heartrate_list = Heartrate.objects.order_by(F('timestamp').desc()).filter(
        patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)
    ecg_list = Ecg.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                  timestamp__date=currentdate)

    if not temperature_list.exists():
        temperature_list = Temperature.objects.order_by(F('timestamp').desc()).filter(
            patientdeviceid=patient_device.patientdeviceid)

    if not heartrate_list.exists():
        heartrate_list = Heartrate.objects.order_by(F('timestamp').desc()).filter(
            patientdeviceid=patient_device.patientdeviceid)

    if not ecg_list.exists():
        ecg_list = Ecg.objects.order_by(F('timestamp').desc()).filter(patientdeviceid=patient_device.patientdeviceid)

    if temperature_list.exists():
        latest_temperature = temperature_list.latest('timestamp')
    else:
        latest_temperature = -1
    if heartrate_list.exists():
        latest_heartrate = heartrate_list.latest('timestamp')
    else:
        latest_heartrate = -1
    if ecg_list.exists():
        latest_ecg = ecg_list.latest('timestamp')
    else:
        latest_ecg = -1

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'latest_temperature': latest_temperature,
               'heartrate_list': heartrate_list,
               'latest_heartrate': latest_heartrate,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               }

    return render(request, 'viewcurrentvitals/viewCurrentVitals.html', context)


@login_required()
def viewhistoryofvitals(request):
    return render(request, 'viewhistoryofvitals/viewHistoryOfVitals.html')


@login_required()
def restrictuseraccess(request):
    return render(request, 'restrictuseraccess/restrictUserAccess.html')


@login_required()
def managedoctoraccount(request):
    userid = request.session['user_id']
    user_object = Userdetails.objects.get(userid=userid)
    context = {'user_object': user_object,
               }
    return render(request, 'managedoctoraccount/manageDoctorAccount.html', context)


@login_required()
def managepatientaccount(request):
    userid = request.session['user_id']
    user_object = Userdetails.objects.get(userid=userid)
    patient_object = Patient.objects.get(userid=userid)
    context = {'user_object': user_object,
               'patient_object': patient_object,
               }
    return render(request, 'managepatientaccount/managePatientAccount.html', context)


@login_required()
def edituser(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(id=user_id)

        if request.POST['password'] != request.POST['repeatPassword']:
            return HttpResponse("Password does not match!")

        validate_password(request.POST['password'])

        user.set_password(request.POST['password'])
        user.last_name = request.POST['lastname']
        user.first_name = request.POST['firstname']
        user.email = request.POST['email']

        user.save()

        userdetails = Userdetails.objects.get(auth_user_id=user_id)

        usertype = RefUsertype.objects.get(usertypeid=request.POST['usertype'])

        userdetails.middlename = request.POST['middlename']
        userdetails.birthday = request.POST['birthday']
        userdetails.contactno = request.POST['contactno']

        if userdetails.usertype != usertype:
            userdetails.usertype = usertype

            if request.POST['usertype'] == '3':
                Patient.objects.get(userid=user_id).delete()
                if Doctor.objects.count() == 0:
                    doctorid = 1
                else:
                    doctorid = Doctor.objects.latest('doctorid').doctorid + 1
                userid = Userdetails.objects.get(auth_user_id=user.id)
                newDoctor = Doctor(
                    doctorid=doctorid,
                    userid=userid
                )
                newDoctor.save()
            else:
                Doctor.objects.get(userid=user_id).delete()
                doctor = Doctor.objects.get(doctorid=request.POST['doctorid'])
                if Patient.objects.count() == 0:
                    patientid = 1
                else:
                    patientid = Patient.objects.latest('patientid').patientid + 1

                userid = Userdetails.objects.get(auth_user_id=user.id)
                newPatient = Patient(
                    patientid=patientid,
                    doctorid=doctor,
                    userid=userid
                )
                newPatient.save()

        userdetails.save()

        return redirect('listofusers')

    else:
        user = User.objects.get(id=user_id)
        userdetails = Userdetails.objects.get(auth_user_id=user_id)
        form = EditUserForm(user)
        context = {'user': user,
                   'userdetails': userdetails,
                   'form': form
                   }

        return render(request, 'edituser/editUser.html', context)



#########################AJAX############################


def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


def search_user(request):
    search = request.GET.get('search', None)

    user_list = User.objects.filter(Q(last_name__contains=search) | Q(first_name__contains=search) |
                                    Q(username__contains=search) | Q(email__contains=search))
    user_array=[]

    for user in user_list:
        user_array.append({
            'id': user.id,
            'userName': user.username,
            'firstname': user.first_name,
            'lastname': user.last_name,
            'email': user.email,
            'usertype': user.userdetails_set.get(auth_user_id=user).usertype.type,
            'status': user.is_active
        })

    return JsonResponse(user_array, safe=False)


def get_user_details(request):
    userid = request.GET.get('userid', None)

    user_details = Userdetails.objects.get(userid=userid)
    user_details_array = []

    extra = ""

    if user_details.usertype.usertypeid == 3:
        patient_list = Patient.objects.filter(doctorid=user_details.doctor_set.get(userid=user_details.userid))

        if patient_list.count() == 0:
            extra += "No patients assigned"
        else:
            for patient in patient_list:
                extra += patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + " | "
    elif user_details.usertype.usertypeid == 4:
        patient = Patient.objects.get(patientid=user_details.patient_set.get(userid=user_details.userid).patientid)
        doctor = patient.doctorid.userid.auth_user_id.first_name + " " + patient.doctorid.userid.auth_user_id.last_name
        extra += doctor
    else:
        extra = 1

    user_details_array.append({
        'name': user_details.auth_user_id.first_name + " " + user_details.middlename + " " + user_details.auth_user_id.last_name,
        'birthday': user_details.birthday,
        'contactno': user_details.contactno,
        'usertype': user_details.usertype.usertypeid,
        'extra': extra,
    })

    return JsonResponse(user_details_array, safe=False)


def add_device(request):
    if Device.objects.count() == 0:
        deviceid = 1
    else:
        deviceid = Device.objects.latest('deviceid').deviceid + 1

    newDevice = Device(
        deviceid=deviceid
    )
    newDevice.save()

    device_list = Device.objects.all()
    device_array = []

    for device in device_list:
        patient_device_list = PatientDevice.objects.filter(device_deviceid=device.deviceid, inuse=1)
        if patient_device_list.count() != 0:
            for patient in patient_device_list:
                device_array.append({
                    'deviceid': device.deviceid,
                    'patient': patient.patient_patientid.userid.auth_user_id.first_name + " " + patient.patient_patientid.userid.auth_user_id.last_name
                })
        else:
            device_array.append({
                'deviceid': device.deviceid,
                'patient': "none"
            })

    return JsonResponse(device_array, safe=False)


def get_patients(request):
    patient_list = Patient.objects.filter(userid__auth_user_id__is_active=1)
    patient_array = []

    for patient in patient_list:
        patient_array.append({
            'patientid': patient.patientid,
            'patientname': patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name
        })
    return JsonResponse(patient_array, safe=False)


def search_patients(request):
    search = request.GET.get('search', None)

    patient_list = Patient.objects.filter((Q(userid__auth_user_id__first_name__contains=search) | Q(userid__auth_user_id__last_name__contains=search)) & Q(userid__auth_user_id__is_active=1))
    patient_array = []

    for patient in patient_list:
        patient_array.append({
            'patientid': patient.patientid,
            'patientname': patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name
        })
    return JsonResponse(patient_array, safe=False)


def set_patient_to_device(request):
    deviceid = request.GET.get('deviceID', None)
    patientid = request.GET.get('patientID', None)

    response = []

    if PatientDevice.objects.filter(device_deviceid=deviceid, inuse=1).exists():
        if PatientDevice.objects.filter(patient_patientid=patientid, device_deviceid=deviceid, inuse=1).exists():
            response.append({'outcome': "Patient is currently using the device"})
        else:
            response.append({'outcome': "Device is currently in use"})
        return JsonResponse(response, safe=False)
    elif PatientDevice.objects.filter(patient_patientid=patientid, device_deviceid=deviceid, inuse=0).exists():
        patientdevice = PatientDevice.objects.get(patient_patientid=patientid, device_deviceid=deviceid, inuse=0)
        patientdevice.inuse = 1

        mqttc = mqtt.Client("Device " + str(deviceid))
        mqttc.tls_set('opm/static/certificates/hivemqServeo-cert.pem')
        try:
            mqttc.connect("serveo.net", 8883)  # Change
        except:
            failedresponse = 0

        mqttc.publish("/devices/" + str(deviceid) + "/patient", patientdevice.patientdeviceid)

        patientdevice.save()

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient is set to device"})

        return JsonResponse(response, safe=False)
    elif PatientDevice.objects.filter(patient_patientid=patientid, inuse=1).exists():
        response.append({'outcome': "Patient is currently using another device"})
        return JsonResponse(response, safe=False)
    else:
        if PatientDevice.objects.count() == 0:
            patientdevice_id = 1
        else:
            patientdevice_id = PatientDevice.objects.latest('patientdeviceid').patientdeviceid + 1

        newPatientDevice = PatientDevice(
            patientdeviceid=patientdevice_id,
            patient_patientid=Patient.objects.get(patientid=patientid),
            device_deviceid=Device.objects.get(deviceid=deviceid),
            inuse=1
        )

        mqttc = mqtt.Client("Device " + str(deviceid))
        mqttc.tls_set('opm/static/certificates/hivemqServeo-cert.pem')
        try:
            mqttc.connect("serveo.net", 8883)  # Change
        except:
            failedresponse = 0

        mqttc.publish("/devices/" + str(deviceid) + "/patient", patientdevice_id)

        newPatientDevice.save()

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient is set to a new device"})

        return JsonResponse(response, safe=False)


def stop_recording(request):
    data = request.GET.get('data', None)
    patientdeviceId = request.GET.get('deviceid', None)
    deviceId = PatientDevice.objects.get(patientdeviceid=patientdeviceId).device_deviceid.deviceid
    failedresponse = 1
    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set('opm/static/certificates/hivemqServeo-cert.pem')
    try:
        mqttc.connect("192.168.1.23", 1883)  # Change
        #mqttc.connect("serveo.net", 8883)  # Change
    except:
        failedresponse = 0
    mqttc.publish("/devices/" + str(deviceId) + "/stop", data)

    patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)

    if data == 1:
        patientdeviceobject.isrecording = 0
    else:
        patientdeviceobject.isrecording = 1

    patientdeviceobject.save()

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


def set_recording_duration(request):
    hours = request.GET.get('hours', None)
    minutes = request.GET.get('minutes', None)
    seconds = request.GET.get('seconds', None)

    total_seconds = (int(hours)*60*60)+(int(minutes)*60)+int(seconds)

    patientdeviceId = request.GET.get('deviceid', None)
    deviceId = PatientDevice.objects.get(patientdeviceid=patientdeviceId).device_deviceid.deviceid
    failedresponse = 1
    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set('opm/static/certificates/hivemqServeo-cert.pem')
    try:
        mqttc.connect("192.168.1.23", 1883)  # Change
        #mqttc.connect("serveo.net", 8883)  # Change
    except:
        failedresponse = 0
    mqttc.publish("/devices/" + str(deviceId) + "/record_duration", total_seconds)

    patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)

    patientdeviceobject.recordingduration = total_seconds

    patientdeviceobject.save()

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


def unassign_patient(request):
    deviceid = request.GET.get('deviceID', None)

    is_assigned = PatientDevice.objects.filter(device_deviceid=deviceid, inuse=1).exists()

    response = []

    if is_assigned:
        mqttc = mqtt.Client("Device " + str(deviceid))
        mqttc.tls_set('opm/static/certificates/hivemqServeo-cert.pem')
        try:
            mqttc.connect("serveo.net", 8883)  # Change
        except:
            failedresponse = 0
        mqttc.publish("/devices/" + str(deviceid) + "/patient", 0)

        patientdevice = PatientDevice.objects.get(device_deviceid=deviceid, inuse=1)
        patientdevice.inuse = 0

        patientdevice.save()

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient unassigned"})

        return JsonResponse(response, safe=False)

    else:
        response.append({'outcome': "No patient assigned"})

        return JsonResponse(response, safe=False)


def get_records(request):
    searchby = request.GET.get('searchBy', None)
    date = request.GET.get('date', None)
    patientid = request.GET.get('patientID', None)

    patient = Patient.objects.get(patientid=patientid)
    patientdevice = PatientDevice.objects.filter(patient_patientid=patient.patientid)

    records_list = []

    if searchby == "date":
        medical_records_list = PatientMedicalHistory.objects.filter(patientid__patientid=patientid, date=date)
        convert_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')
        vitals_check_date = Temperature.objects.filter(timestamp__date=date, patientdeviceid__in=patientdevice)

        if vitals_check_date.exists():
            records_list.append({
                'date': convert_date,
                'recordtype': 2,
                'data': date,
            })
        else:
            records_list.append({
                'date': "No past vital records from this date!",
                'recordtype': 2,
                'data': -1
            })
    else:
        convert_date = datetime.datetime.strptime(date, '%Y-%m')
        medical_records_list = PatientMedicalHistory.objects.filter(patientid__patientid=patientid, date__year=convert_date.year, date__month=convert_date.month)

        temperature_distinct_date_records = Temperature.objects.filter(patientdeviceid__in=patientdevice, timestamp__year=convert_date.year, timestamp__month=convert_date.month)
        temperature_distinct_date_records = temperature_distinct_date_records.values_list('timestamp',
                                                                                          flat=True).distinct()

        vitals_dates_list = []
        for temperature_data in temperature_distinct_date_records:
            if not vitals_dates_list.__contains__(temperature_data.date()):
                vitals_dates_list.append(temperature_data.date())

        if vitals_dates_list.__len__() != 0:
            for vital_record in vitals_dates_list:
                records_list.append({
                    'date': vital_record.strftime('%B %d, %Y'),
                    'recordtype': 2,
                    'data': vital_record
                })
        else:
            records_list.append({
                'date': "No past vital records from this date!",
                'recordtype': 2,
                'data': -1,
            })

    if not medical_records_list.exists():
        records_list.append({
            'date': "No past medical forms from this date!",
            'recordtype': 1,
            'data': -1,
        })

    for medical_record in medical_records_list:
        records_list.append({
            'date': medical_record.date.strftime('%B %d, %Y'),
            'recordtype': 1,
            'data': medical_record.patient_medical_historyid,
        })

    print(records_list)
    return JsonResponse(records_list, safe=False)


def check_device_status(request):
    patientdeviceId = request.GET.get('patientdeviceid', None)
    patientdevicestatus = PatientDevice.objects.get(patientdeviceid=patientdeviceId).isrecording
    duration = PatientDevice.objects.get(patientdeviceid=patientdeviceId).recordingduration

    status = []

    status.append({
        'status': patientdevicestatus,
        'duration': duration
    })

    return JsonResponse(status, safe=False)


def get_ecg_batch(request):
    currentBatch = request.GET.get('currentBatch', None)
    patient_id = request.GET.get('patientid', None)
    direction = request.GET.get('direction', None)
    batch = request.GET.get('batch', None)

    currentdate = datetime.date.today()
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)

    if batch == "-1":
        ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)
    else:
        ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=currentdate, batchid=batch)
    if direction == "1":
        ecg_list = ecg_list.all()[int(currentBatch):int(currentBatch)+1000]
    elif int(currentBatch) - (2000 + (int(currentBatch) % 1000)) < 0:
        ecg_list = ecg_list.all()[int(currentBatch) - (1000 + (int(currentBatch) % 1000)):int(currentBatch) - ((int(currentBatch) % 1000))]
    else:
        ecg_list = ecg_list.all()[int(currentBatch) - (2000 + (int(currentBatch) % 1000)):int(currentBatch) - (1000 + (int(currentBatch) % 1000))]

    ecg_values = []
    for ecg_data in ecg_list:
        ecg_values.append({
            'value': ecg_data.data,
            'time': ecg_data.timestamp.time().strftime('%I:%M:%S %p')
        })

    return JsonResponse(ecg_values, safe=False)


def val_func(request):
    serport = serial.Serial('COM3', 9600)
    serport.write(1)
    time.sleep(1)
    serport.setDTR(False)
    time.sleep(1)
    data = serport.readline()
    now = datetime.datetime.now()
    html = "" \
           "<html>" \
           "<head>" \
           "<title>My Django App</title>" \
           "</head>" \
           "<body>It is now %s." % now + \
           "<br>Your data is: %s." % data + \
           "</body>" \
           "</html>"
    return HttpResponse(html)


