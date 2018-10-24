from django.shortcuts import render, HttpResponse, redirect, get_object_or_404, HttpResponseRedirect, Http404

from .models import Userdetails, Patient, Doctor, RefUsertype, PatientDevice, Temperature, Ecg, Heartrate, Device
from .forms import *
from django.db.models import Avg
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import *
from django.http import JsonResponse



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
            patient_list = Patient.objects.order_by('userid').filter()
            return render(request, 'home/doctorBody.html', context)
        elif userdetails.usertype.usertypeid == 4:
            return render(request, 'home/patientBody.html', context)

    else:
        return redirect('index')


def listofusers(request):
    current_user_type = Userdetails.objects.get(auth_user_id=request.user.id).usertype_id
    user_list = User.objects.order_by('id')
    user_details_list = Userdetails.objects.order_by('userid')
    context = {'user_list': user_list,
               'user_id': request.session['user_id'],
               'user_details_list': user_details_list,
               'current_user_type': current_user_type}
    return render(request, 'listofusers/listOfUsers.html', context)


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
                    userid=latestpatientuser
                )

                newPatient.save()
                return redirect('createuser')
        else:
            return HttpResponse("bobo ka")
    else:
        form = CreateUserForm()
        return render(request, 'createusers/createUser.html', {'form': form})


@login_required()
def archiving(request):
    return render(request, 'archiving/archiving.html')


@login_required()
def changeuserofdevice(request):
    patient_device_list = PatientDevice.objects.order_by('device_deviceid').all()
    device_list = Device.objects.order_by('deviceid').all()

    context = {'patient_device_list': patient_device_list,
               'device_list': device_list
               }

    return render(request, 'changeuserofdevice/changeUserOfDevice.html', context)


def viewassignedpatients(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    patient_list = Patient.objects.order_by('userid').filter(doctorid=doctorid)

    context = {'doctorid': doctorid,
               'patient_list': patient_list,
               }
    return render(request, 'viewassignedpatients/viewAssignedPatients.html', context)


def assignedpatientvitals(request, patient_id):
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.filter(patient_patientid_id=patient_id)
    temperature_list = Temperature.objects.filter(patientid__in=patient_device, deviceid__in=patient_device)
    temperature = temperature_list.aggregate(Avg('data'))
    heartrate_list = Heartrate.objects.filter(patientid__in=patient_device, deviceid__in=patient_device)
    heartrate = heartrate_list.aggregate(Avg('data'))
    ecg_list = Ecg.objects.filter(patientid__in=patient_device, deviceid__in=patient_device)
    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature': temperature,
               'heartrate': heartrate,
               'ecg_list': ecg_list
               }

    return render(request, 'patientvitals/patientVitals.html', context)


def changerecordinginterval(request):
    return render(request, 'changerecordinginterval/changeRecordingInterval.html')


def stoprecording(request):
    return render(request, 'stoprecording/stopRecording.html')


def viewcurrentvitals(request):
    return render(request, 'viewcurrentvitals/viewCurrentVitals.html')


def viewhistoryofvitals(request):
    return render(request, 'viewhistoryofvitals/viewHistoryOfVitals.html')


def restrictuseraccess(request):
    return render(request, 'restrictuseraccess/restrictUserAccess.html')


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

    user_list = User.objects.filter(username__contains=search)
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
