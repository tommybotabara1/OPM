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
from datetime import timedelta
from django.db.models import F, Avg, Min, Max
import time
import serial
from twilio.rest import Client
import random
from django.core.mail import send_mail
from django.core.signing import Signer

signer = Signer()
#broker_ip = "192.168.0.194"
port_number = 1883
tls_certificate = 'opm/static/certificates/cehci_tls_cert.pem'
broker_ip = "192.168.1.19"


from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your OPHM account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        context = {'user': user,
                   }
        return render(request, 'useraccountactivation.html', context)
    else:
        return HttpResponse('Activation link is invalid!')


def index(request):
    logout(request)
    form = LoginForm()
    try:
        del request.session['user_id']
        del request.session['user_type']
        del request.session['home_count']
    except KeyError:
        pass

    return render(request, 'login/index.html', {'form': form})


def invalid_credentials(request):
    form = LoginForm()
    try:
        del request.session['user_id']
        del request.session['user_type']
        del request.session['home_count']
    except KeyError:
        pass

    context = {
        'form': form,
        'error_message': 'Invalid credentials. Try again'
    }
    return render(request, 'login/index.html', context)


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
                request.session['home_count'] = 1
                userdetails = Userdetails.objects.get(auth_user_id=request.session['user_id'])

                if userdetails.usertype.usertypeid == 1 or userdetails.usertype.usertypeid == 2:
                    return redirect('adminauthentication')
                elif userdetails.usertype.usertypeid == 3 or userdetails.usertype.usertypeid == 4:
                    return redirect('home')
            else:
                return redirect('invalid_credentials')
        else:
            return HttpResponse(form.errors)


@login_required()
def adminauthentication(request):
    # Generate OTP password
    chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', '0', 'P', 'Q', 'R', 'S', 'T', 'U',
             'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    otp = ""
    for x in range(6):
        otp = otp + chars[random.randint(0, len(chars)) - 1]
    print(otp)

    userdetails = Userdetails.objects.get(auth_user_id=request.session['user_id'])

    # Your Account Sid and Auth Token from twilio.com/console
    account_sid = "AC54dbed5f1b63313345460f725fce098a"
    auth_token = "c6897746b240e1ecb1475af8b4c66ee0"
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
        body="Your OTP is: " + otp,
        from_='+14065102947',
        to=userdetails.contactno
    )

    request.session['otp'] = otp

    return render(request, 'adminauthentication/adminAuthentication.html', {'otp': otp})


@login_required()
def adminauthenticate(request, otp):
    if otp == request.session['otp']:
        return redirect('home')
    else:
        html = "" \
               "<html>" \
               "<head>" \
               "<title>My Django App</title>" \
               "</head>" \
               "<body>Wrong OTP code. Try again." \
               "<br>" \
               "<a href='/'>Log in page</a>" \
               "</body>" \
               "</html>"
        return HttpResponse(html)


@login_required()
def home(request):
    if request.session['user_id'] is not None:
        userdetails = Userdetails.objects.get(auth_user_id=request.session['user_id'])
        request.session['user_type'] = userdetails.usertype.usertypeid
        context = {'user_id': request.session['user_id'],
                   'user_details': userdetails}

        if userdetails.usertype.usertypeid == 1:
            return render(request, 'home/systemAdminBody.html', context)
        elif userdetails.usertype.usertypeid == 2:
            fivedaysago = datetime.date.today() - timedelta(days=5)
            currentdate = datetime.date.today()
            patient_device_list = PatientDevice.objects.order_by('device_deviceid').all()
            device_list = Device.objects.order_by('deviceid').all()
            patient_list = Patient.objects.filter(userid__auth_user_id__is_active=1)
            newusers = User.objects.order_by(F('date_joined').desc()).filter(date_joined__date__range=[fivedaysago, currentdate])
            allusers = User.objects.order_by(F('last_login').desc()).filter(last_login__date=currentdate)

            context = {'user_id': request.session['user_id'],
                       'user_details': userdetails,
                       'patient_device_list': patient_device_list,
                       'device_list': device_list,
                       'patient_list': patient_list,
                       'newusers': newusers,
                       'allusers': allusers,
                       'usertype': 'admin'
                       }

            return render(request, 'home/adminBody.html', context)
        elif userdetails.usertype.usertypeid == 3:
            doctorid = Doctor.objects.get(userid=request.session['user_id'])
            patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)

            context = {'doctorid': doctorid,
                       'patient_device_list': patient_device_list,
                       'user_id': request.session['user_id'],
                       'user_details': userdetails
                       }
            return render(request, 'home/doctorBody.html', context)
        elif userdetails.usertype.usertypeid == 4:
            patient = Patient.objects.get(userid=request.session['user_id'])
            patient_id = patient.patientid
            currentdate = datetime.date.today()
            patient = Patient.objects.get(patientid=patient_id)
            if not PatientDevice.objects.filter(patient_patientid_id=patient_id, inuse=1).exists():
                patient_device = -1
                patient_object = Patient.objects.get(userid=request.session['user_id'])
                context = {
                    'user_id': request.session['user_id'],
                    'user_details': userdetails,
                    'patient_object': patient_object,
                    'patient': patient,
                    'patient_device': patient_device
                }
                return render(request, 'home/patientBody.html', context)
            else:
                patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
                latest_data = Temperature.objects.defer('data').filter(patientdeviceid=patient_device).order_by(F('timestamp').desc())[:1]
                latest_data = latest_data[0]

            patient_object = Patient.objects.get(userid=request.session['user_id'])

            if request.session['home_count'] == 1:
                daysbeforedeadline = patient_object.deadlinereturndate - currentdate
                if(daysbeforedeadline.days > 5):
                    request.session['home_count'] = 2
            else:
                daysbeforedeadline = ( (patient_object.deadlinereturndate - currentdate) /  (patient_object.deadlinereturndate - currentdate) ) - 1000

            context = {
                       'user_id': request.session['user_id'],
                        'user_details': userdetails,
                       'patient_object': patient_object,
                       'patient': patient,
                       'patient_device': patient_device,
                       'daysbeforedeadline': daysbeforedeadline,
                        'latest_data': latest_data
                       }

            print(patient)

            return render(request, 'home/patientBody.html', context)

    else:
        return redirect('index')


@login_required()
def listofusers(request):
    current_user_type = Userdetails.objects.get(auth_user_id=request.user.id).usertype_id
    user_list = User.objects.order_by('id')
    user_details_list = Userdetails.objects.order_by('userid')
    type = 0
    context = {'user_list': user_list,
               'user_id': request.session['user_id'],
               'user_details_list': user_details_list,
               'type': type,
               'current_user_type': current_user_type}
    return render(request, 'listofusers/listOfUsers.html', context)


@login_required()
def listofdoctors(request):
    current_user_type = Userdetails.objects.get(auth_user_id=request.user.id).usertype_id
    user_list = User.objects.order_by('id').filter(userdetails__usertype__usertypeid=3)
    user_details_list = Userdetails.objects.order_by('userid')
    type = 1
    context = {'user_list': user_list,
               'user_id': request.session['user_id'],
               'user_details_list': user_details_list,
               'type': type,
               'current_user_type': current_user_type}
    return render(request, 'listofusers/listOfUsers.html', context)


@login_required()
def listofpatients(request):
    current_user_type = Userdetails.objects.get(auth_user_id=request.user.id).usertype_id
    user_list = User.objects.order_by('id').filter(userdetails__usertype__usertypeid=4)
    user_details_list = Userdetails.objects.order_by('userid')
    type = 2
    context = {'user_list': user_list,
               'user_id': request.session['user_id'],
               'user_details_list': user_details_list,
               'type': type,
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
            if User.objects.filter(username=request.POST['username']).exists():
                return HttpResponse("Username exists!")

            chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', '0', 'P', 'Q', 'R', 'S', 'T',
                     'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e',
                     'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
            otp = ""
            for x in range(9):
                otp = otp + chars[random.randint(0, len(chars)) - 1]

            try:
                validate_password(otp)
            except ValidationError as e:
                error_message = str(e)
                form = CreateUserForm()
                context = {
                    'form': form,
                    'message': "Create user",
                    'password_validators': password_validators_help_text_html(password_validators=None),
                    'error_message': error_message,
                    'error': 1,
                }
                return render(request, 'createusers/createUser.html', context)

            user = User.objects.create_user(request.POST['username'], request.POST['email'], 'pass123word')
            user.last_name = request.POST['lastname']
            user.first_name = request.POST['firstname']
            user.is_active = False
            user.save()

            user = User.objects.get(username=request.POST['username'])

            usertype = RefUsertype.objects.get(usertypeid=request.POST['usertype'])

            newUserDetail = Userdetails(
                userid=user.id,
                middlename=request.POST['middlename'],
                birthday=request.POST['birthday'],
                contactno=request.POST['contactno'],
                usertype=usertype,
                auth_user_id=User.objects.get(id=user.id),
                sex=request.POST['sex']
            )

            newUserDetail.save()

            current_site = get_current_site(request)
            mail_subject = 'Activate your OPHM account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()

            if request.POST['usertype'] == '3':
                if Doctor.objects.count() == 0:
                    doctorid = 1
                else:
                    doctorid = Doctor.objects.latest('doctorid').doctorid + 1

                latestdoctoruser = Userdetails.objects.latest('userid')
                newDoctor = Doctor(
                    doctorid=doctorid,
                    userid=latestdoctoruser,
                    licensenumber=request.POST['licensenumber']
                )

                newDoctor.save()
                form = CreateUserForm()
                context = {
                    'form': form,
                    'message': "New Doctor User Created. Inform user to check their email to register the account."
                }
                return render(request, 'createusers/createUser.html', context)
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
                    currentdeviceid=0,
                )

                newPatient.save()

                if PatientDoctor.objects.count() == 0:
                    patientdoctorid = 1
                else:
                    patientdoctorid = PatientDoctor.objects.latest('patientdoctorid').patientdoctorid + 1

                newPatientDoctor = PatientDoctor(
                    patientdoctorid=patientdoctorid,
                    patientid=newPatient,
                    doctorid=newPatient.doctorid,
                    restrictmedicalinformationaccess=0,
                    restrictvitalsinformationaccess=0,
                    assigneddoctor=1,
                )

                if Notifications.objects.all().count() == 0:
                    notificationid = 1
                else:
                    notificationid = Notifications.objects.all().count() + 1

                newNotification = Notifications(
                    notificationid=notificationid,
                    notificationdescription="New assigned patient. Patient name: " + newPatient.userid.auth_user_id.first_name + " " + newPatient.userid.auth_user_id.last_name,
                    datetime=datetime.datetime.now(),
                    userid=doctor.userid,
                    viewed=0
                )

                newNotification.save()
                newPatientDoctor.save()
                form = CreateUserForm()
                context = {
                    'form': form,
                    'message': "New Patient User Created. Inform user to check their email to register the account."
                }
                return render(request, 'createusers/createUser.html', context)
        else:
            return HttpResponse("bobo ka")
    else:
        form = CreateUserForm()
        context = {
            'form': form,
            'message': "Create user",
            'password_validators': password_validators_help_text_html(password_validators=None)
        }
        return render(request, 'createusers/createUser.html', context)


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
    patient_list = Patient.objects.filter(doctorid=doctorid)
    patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)
    other_patients_list = PatientDoctor.objects.filter(doctorid=doctorid, assigneddoctor=0)

    context = {'doctorid': doctorid,
               'patient_list': patient_list,
               'patient_device_list': patient_device_list,
               'other_patients_list': other_patients_list,
               }
    return render(request, 'viewassignedpatients/viewAssignedPatients.html', context)


@login_required()
def assignedpatientvitals(request, patient_id):
    currentdate = datetime.date.today()
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
    comments = Comments.objects.filter(patientdeviceid=patient_device, timestamp__date=currentdate)
    temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            currentdate) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            currentdate) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=currentdate)[:1000]

    if not ecg_list.exists():
        pagefrom = 1

        context = {'patient': patient,
                   'patient_device': patient_device,
                   'latest_ecg': -2,
                   'pagefrom': pagefrom,
                   'base_template': 'home/doctorHeaderFooter.html'
                   }

        return render(request, 'patientvitals/patientVitals.html', context)

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
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               'base_template': 'home/doctorHeaderFooter.html',
               'comments': comments,
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
               'pagefrom': pagefrom,
               'base_template': 'home/doctorHeaderFooter.html',
               }

    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def assignedpatientrecords(request, patient_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientdevice = PatientDevice.objects.filter(patient_patientid=patient.patientid)
    patient_medical_history_list = PatientMedicalHistory.objects.filter(patientid=patient_id)
    temperature_records = Temperature.objects.filter(patientdeviceid__in=patientdevice)
    temperature_distinct_date_records = temperature_records.values_list('patientdeviceid', 'timestamp').distinct()

    vitals_dates_list = []
    vitals_patientdeviceid_dates_list = []
    for temperature_data in temperature_distinct_date_records:
        if not vitals_dates_list.__contains__(temperature_data[1].date()):
            vitals_dates_list.append(temperature_data[1].date())
            vitals_patientdeviceid_dates_list.append({
                'date': temperature_data[1].date(),
                'patientdeviceid': temperature_data[0]
            })

    vitals_dates_list_size = vitals_dates_list.__len__()
    context = {'patient': patient,
               'patient_medical_history_list': patient_medical_history_list,
               'vitals_dates_list': vitals_dates_list,
               'vitals_patientdeviceid_dates_list': vitals_patientdeviceid_dates_list,
               'vitals_dates_list_size': vitals_dates_list_size,
               }

    return render(request, 'patientrecords/patientRecords.html', context)


@login_required()
def otherpatientrecords(request, patient_id, access_medicalforms, access_vitalforms):
    patient = Patient.objects.get(patientid=patient_id)
    patientdevice = PatientDevice.objects.filter(patient_patientid=patient.patientid)
    patient_medical_history_list = PatientMedicalHistory.objects.filter(patientid=patient_id)
    temperature_records = Temperature.objects.filter(patientdeviceid__in=patientdevice)
    temperature_distinct_date_records = temperature_records.values_list('patientdeviceid', 'timestamp').distinct()

    vitals_dates_list = []
    vitals_patientdeviceid_dates_list = []
    for temperature_data in temperature_distinct_date_records:
        if not vitals_dates_list.__contains__(temperature_data[1].date()):
            vitals_dates_list.append(temperature_data[1].date())
            vitals_patientdeviceid_dates_list.append({
                'date': temperature_data[1].date(),
                'patientdeviceid': temperature_data[0]
            })

    vitals_dates_list_size = vitals_dates_list.__len__()
    context = {'patient': patient,
               'patient_medical_history_list': patient_medical_history_list,
               'vitals_dates_list': vitals_dates_list,
               'vitals_patientdeviceid_dates_list': vitals_patientdeviceid_dates_list,
               'vitals_dates_list_size': vitals_dates_list_size,
               'access_medicalforms': access_medicalforms,
               'access_vitalrecords': access_vitalforms
               }

    return render(request, 'patientrecords/patientRecords.html', context)


@login_required()
def otherpatientvitalrecord(request, patient_id, access_medicalforms, access_vitalforms, patientdevice_id, date):
    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)
    patient = Patient.objects.get(patientid=patient_device.patient_patientid_id)
    comments = Comments.objects.filter(patientdeviceid=patient_device, timestamp__date=convert_date)
    temperature_list = temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                 timestamp__date=convert_date)

    latest_ecg = ecg_list.latest('timestamp')

    ecg_list = ecg_list.all()[:1000]

    ecg_list_all = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=convert_date)

    ecg_list_batch_values = ecg_list_all.values_list('batchid', flat=True).distinct().order_by()

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

    pagefrom = 4

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               'base_template': 'home/doctorHeaderFooter.html',
               'comments': comments,
               'access_medicalforms': access_medicalforms,
               'access_vitalrecords': access_vitalforms,
               'patient_id': patient_id
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def otherpatientmedicalrecord(request, patient_id, access_medicalforms, access_vitalforms, medical_history_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientmedicalinfo = PatientMedicalHistory.objects.get(patient_medical_historyid=medical_history_id)
    pagefrom = 3
    context = {'patient': patient,
               'patientmedicalinfo': patientmedicalinfo,
               'pagefrom': pagefrom,
               'base_template': 'home/doctorHeaderFooter.html',
               'access_medicalforms': access_medicalforms,
               'access_vitalrecords': access_vitalforms
               }
    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def assignedpatientrecordsmedicalhistory(request, patient_id, medical_history_id):
    patient = Patient.objects.get(patientid=patient_id)
    patientmedicalinfo = PatientMedicalHistory.objects.get(patient_medical_historyid=medical_history_id)
    pagefrom = 2
    context = {'patient': patient,
               'patientmedicalinfo': patientmedicalinfo,
               'pagefrom': pagefrom,
               'base_template': 'home/doctorHeaderFooter.html',
               }
    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def assignedpatientrecordsvitalrecords(request, patientdevice_id, date):
    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)
    patient = Patient.objects.get(patientid=patient_device.patient_patientid_id)
    comments = Comments.objects.filter(patientdeviceid=patient_device, timestamp__date=convert_date)
    temperature_list = temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                  timestamp__date=convert_date)
    latest_ecg = ecg_list.latest('timestamp')


    ecg_list = ecg_list.all()[:1000]

    ecg_list_all = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=convert_date)

    ecg_list_batch_values = ecg_list_all.values_list('batchid', flat=True).distinct().order_by()

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
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               'base_template': 'home/doctorHeaderFooter.html',
               'comments': comments
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def managedevicerecording(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)
    presets_list = Presets.objects.filter(doctorid=doctorid)
    timeList = Time.objects.all()

    context = {
        'doctorid': doctorid.doctorid,
        'patient_device_list': patient_device_list,
        'presets_list': presets_list,
        'time_list': timeList
    }
    return render(request, 'managedevicerecording/manageDeviceRecording.html', context)


@login_required()
def alerts(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    alerts = Alerts.objects.filter(patientdeviceid__patient_patientid__doctorid=doctorid.doctorid, patientdeviceid__inuse=1)

    context = {
        'alerts': alerts
    }

    return render(request, 'alerts/alerts.html', context)

@login_required()
def viewalert(request, alert_id, patientdevice_id, date):
    alert = Alerts.objects.get(alertid=alert_id)
    alert.viewed = 1
    alert.save()

    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)
    patient = Patient.objects.get(patientid=patient_device.patient_patientid_id)
    temperature_list = temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                 timestamp__date=convert_date)
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

    pagefrom = 5

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               'base_template': 'home/doctorHeaderFooter.html',
               'access_medicalforms': 99,
               'access_vitalrecords': 99,
               'patient_id': patient.patientid
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def viewcurrentvitals(request):
    patient = Patient.objects.get(userid=request.session['user_id'])
    patient_id = patient.patientid
    currentdate = datetime.date.today()
    patient = Patient.objects.get(patientid=patient_id)
    patient_device = PatientDevice.objects.get(patient_patientid_id=patient_id, inuse=1)
    temperature_list = temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            currentdate) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            currentdate) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                 timestamp__date=currentdate)[:1000]

    if not ecg_list.exists():
        context = {'patient': patient,
                   'patient_device': patient_device,
                   'latest_ecg': -2,
                   }

        return render(request, 'viewcurrentvitals/viewCurrentVitals.html', context)

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
        current_batch_list = Ecg.objects.order_by(F('timestamp').asc()).filter(
            patientdeviceid=patient_device.patientdeviceid,
            timestamp__date=currentdate, batchid=batch)
        start_time = current_batch_list.first().timestamp
        end_time = current_batch_list.last().timestamp

        ecg_batch_start_end_time.append({
            'batchid': batch,
            'start_time': start_time.time().strftime('%I:%M:%S %p'),
            'end_time': end_time.time().strftime('%I:%M:%S %p'),
        })


    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               }

    return render(request, 'viewcurrentvitals/viewCurrentVitals.html', context)


@login_required()
def viewhistoryofvitals(request):
    patient = Patient.objects.get(userid=request.session['user_id'])
    patientdevice = PatientDevice.objects.filter(patient_patientid=patient.patientid)
    patient_medical_history_list = PatientMedicalHistory.objects.filter(patientid=patient.patientid)
    temperature_records = Temperature.objects.filter(patientdeviceid__in=patientdevice)
    temperature_distinct_date_records = temperature_records.values_list('patientdeviceid', 'timestamp').distinct()

    vitals_dates_list = []
    vitals_patientdeviceid_dates_list = []
    for temperature_data in temperature_distinct_date_records:
        if not vitals_dates_list.__contains__(temperature_data[1].date()):
            vitals_dates_list.append(temperature_data[1].date())
            vitals_patientdeviceid_dates_list.append({
                'date': temperature_data[1].date(),
                'patientdeviceid': temperature_data[0]
            })

    vitals_dates_list_size = vitals_dates_list.__len__()
    context = {'patient': patient,
               'patient_medical_history_list': patient_medical_history_list,
               'vitals_patientdeviceid_dates_list': vitals_patientdeviceid_dates_list,
               'vitals_dates_list_size': vitals_dates_list_size
               }

    return render(request, 'viewhistoryofvitals/viewHistoryOfVitals.html', context)


@login_required()
def viewhistoryofvitalsmediclaform(request, medical_history_id):
    patient = Patient.objects.get(userid=request.session['user_id'])
    patientmedicalinfo = PatientMedicalHistory.objects.get(patient_medical_historyid=medical_history_id)
    pagefrom = 4
    context = {'patient': patient,
               'patientmedicalinfo': patientmedicalinfo,
               'pagefrom': pagefrom,
               'base_template': 'home/patientHeaderFooter.html',
               }
    return render(request, 'patientmedicalinfo/patientMedicalInfo.html', context)


@login_required()
def viewhistoryofvitalvitalrecords(request, patientdevice_id, date):
    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)
    patient = Patient.objects.get(patientid=patient_device.patient_patientid_id)
    comments = Comments.objects.filter(patientdeviceid=patient_device, timestamp__date=convert_date)
    temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")
    ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                 timestamp__date=convert_date)

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

    pagefrom = 3

    context = {'patient': patient,
               'patient_device': patient_device,
               'temperature_list': temperature_list,
               'heartrate_list': heartrate_list,
               'ecg_list': ecg_list,
               'latest_ecg': latest_ecg,
               'pagefrom': pagefrom,
               'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
               'batch_list': batch_list,
               'ecg_batch_start_end_time': ecg_batch_start_end_time,
               'base_template': 'home/patientHeaderFooter.html',
               'comments': comments,
               'access_medicalforms': 99,
               'access_vitalrecords': 99,
               'patient_id': patient.patientid
               }

    return render(request, 'patientvitals/patientVitals.html', context)


@login_required()
def restrictuseraccess(request):
    patient = Patient.objects.get(userid=request.session['user_id'])
    patientDoctorsList = PatientDoctor.objects.filter(patientid=patient)

    doctors = []

    for doctor in patientDoctorsList:
        doctors.append(doctor.doctorid.doctorid)

    doctorList = Doctor.objects.exclude(doctorid__in=doctors)
    assignedDoctor = patient.doctorid

    context = {'patient': patient,
               'patientdoctorlist': patientDoctorsList,
               'doctorlist': doctorList,
               'assigneddoctor': assignedDoctor,
               }

    return render(request, 'restrictuseraccess/restrictUserAccess.html', context)


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
def faqs(request):
    userid = request.session['user_id']
    user_object = Userdetails.objects.get(userid=userid)
    patient_object = Patient.objects.get(userid=userid)
    context = {'user_object': user_object,
               'patient_object': patient_object,
               }
    return render(request, 'faqs/frequentlyAskedQuestions.html', context)


@login_required()
def edituser(request, user_id):
    user = User.objects.get(id=user_id)
    userdetails = Userdetails.objects.get(auth_user_id=user_id)
    doctors = Doctor.objects.all()
    extra = ""


    if userdetails.usertype.usertypeid == 3:
        patient_list = Patient.objects.filter(doctorid=userdetails.doctor_set.get(userid=userdetails.userid))

        if patient_list.count() == 0:
            extra += "No patients assigned"
        else:
            for patient in patient_list:
                extra += patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + " | "

    elif userdetails.usertype.usertypeid == 4:
        patient = Patient.objects.get(patientid=userdetails.patient_set.get(userid=userdetails.userid).patientid)
        doctor = patient.doctorid.userid.auth_user_id.first_name + " " + patient.doctorid.userid.auth_user_id.last_name
        extra += doctor
    else:
        extra = 1

    context = {'user': user,
               'userdetails': userdetails,
               'doctors': doctors,
               'extra': extra
               }
    return render(request, 'edituser/editUser.html', context)



@login_required()
def edituser1(request, user_id):
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


@login_required()
def notifications(request):
    userid = Userdetails.objects.get(userid=request.session['user_id'])
    notifications = Notifications.objects.filter(userid=userid)

    if userid.usertype_id == 2:
        base_template = 'home/adminHeaderFooter.html'
    elif userid.usertype_id == 3:
        base_template = 'home/doctorHeaderFooter.html'
    else:
        base_template = 'home/patientHeaderFooter.html'

    context = {
        'notifications': notifications,
        'base_template': base_template
    }

    return render(request, 'notifications/notifications.html', context)

#########################AJAX############################

@login_required()
def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


@login_required()
def validate_email(request):
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(email__iexact=email).exists()
    }
    return JsonResponse(data)


@login_required()
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


@login_required()
def get_user_details(request):
    userid = request.GET.get('userid', None)

    user_details = Userdetails.objects.get(userid=userid)
    user_details_array = []

    extra = ""
    licensenumber = -1

    if user_details.usertype.usertypeid == 3:
        patient_list = Patient.objects.filter(doctorid=user_details.doctor_set.get(userid=user_details.userid))

        if patient_list.count() == 0:
            extra += "No patients assigned"
        else:
            for patient in patient_list:
                extra += patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + " | "

        licensenumber = Doctor.objects.get(userid=userid).licensenumber

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
        'sex': user_details.sex,
        'usertype': user_details.usertype.usertypeid,
        'extra': extra,
        'licensenumber': licensenumber
    })

    return JsonResponse(user_details_array, safe=False)


@login_required()
def add_device(request):
    macaddress = request.GET.get('macaddress', None)
    if Device.objects.count() == 0:
        deviceid = 1
    else:
        deviceid = Device.objects.latest('deviceid').deviceid + 1

    newDevice = Device(
        deviceid=deviceid,
        macaddress=macaddress,
        status=0,
        borroweddate=datetime.datetime.today(),
        retureneddate=datetime.datetime.today(),
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


@login_required()
def get_patients(request):
    patient_list = Patient.objects.filter(userid__auth_user_id__is_active=1)
    patient_array = []

    for patient in patient_list:
        patient_array.append({
            'patientid': patient.patientid,
            'patientname': patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name
        })
    return JsonResponse(patient_array, safe=False)


@login_required()
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


@login_required()
def search_assigned_patients(request):
    search = request.GET.get('search', None)

    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    patient_device_list = PatientDevice.objects.filter(patient_patientid__doctorid=doctorid, inuse=1)

    patient_list = patient_device_list.filter(Q(patient_patientid__userid__auth_user_id__first_name__contains=search) |
                                              Q(patient_patientid__userid__auth_user_id__last_name__contains=search) |
                                              Q(patient_patientid__userid__auth_user_id__username__contains=search) |
                                              Q(patient_patientid__userid__auth_user_id__email__contains=search) |
                                              Q(patient_patientid__userid__middlename__contains=search) |
                                              Q(patient_patientid__userid__contactno__contains=search)
                                              )
    patient_array=[]


    for patient in patient_list:
        patient_array.append({
            'patientid': patient.patient_patientid.patientid,
            'deviceid': patient.device_deviceid.deviceid,
            'firstname': patient.patient_patientid.userid.auth_user_id.first_name,
            'lastname': patient.patient_patientid.userid.auth_user_id.last_name,
            'middlename': patient.patient_patientid.userid.middlename,
            'contactno': patient.patient_patientid.userid.contactno,
            'email': patient.patient_patientid.userid.auth_user_id.email,
        })

    return JsonResponse(patient_array, safe=False)


@login_required()
def set_patient_to_device(request):
    deviceid = request.GET.get('deviceID', None)
    patientid = request.GET.get('patientID', None)
    returndate = request.GET.get('returnDate', None)
    convert_date = datetime.datetime.strptime(returndate, '%Y-%m-%d')
    macaddress = Device.objects.get(deviceid=deviceid).macaddress

    response = []

    failedresponse = 1

    if PatientDevice.objects.filter(device_deviceid=deviceid, inuse=1).exists():
        if PatientDevice.objects.filter(patient_patientid=patientid, device_deviceid=deviceid, inuse=1).exists():
            response.append({'outcome': "Patient is currently using the device"})
        else:
            response.append({'outcome': "Device is currently in use"})
        return JsonResponse(response, safe=False)
    elif PatientDevice.objects.filter(patient_patientid=patientid, inuse=1).exists():
        response.append({'outcome': "Patient is currently using another device"})
        return JsonResponse(response, safe=False)
    elif PatientDevice.objects.filter(patient_patientid=patientid, device_deviceid=deviceid, inuse=0).exists():
        patientdevice = PatientDevice.objects.get(patient_patientid=patientid, device_deviceid=deviceid, inuse=0)
        patientdevice.inuse = 1
        patientdevice.isrecording = 0
        patientdevice.recordingduration = 120
        patientdevice.mintemperature = 32
        patientdevice.maxtemperature = 40
        patientdevice.minheartrate = 60
        patientdevice.maxheartrate = 100

        device = Device.objects.get(deviceid=deviceid)
        patient = Patient.objects.get(patientid=patientid)
        device.status = 1
        device.borroweddate = datetime.datetime.now()
        patient.currentdeviceid = deviceid
        patient.deadlinereturndate = convert_date

        mqttc = mqtt.Client("Device " + str(deviceid))
        #mqttc.tls_set(tls_certificate)
        try:
            mqttc.connect(broker_ip, port_number)

            mqttc.publish("/devices/" + str(macaddress) + "/patient", patientdevice.patientdeviceid)

            mqttc.publish("/devices/" + str(macaddress) + "/record_duration", 120)
            mqttc.publish("/devices/" + str(macaddress) + "/change_temperature", "32_40")
            mqttc.publish("/devices/" + str(macaddress) + "/change_heartrate", "60_100")
            mqttc.publish("/devices/" + str(macaddress) + "/doctor", patient.doctorid.userid.userid)
            mqttc.publish("/devices/" + str(macaddress) + "/patientName", str(patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name))

            patientdevice.save()
            device.save()
            patient.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newDoctorNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Patient: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + ", is set to Device " + str(
                    device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.doctorid.userid,
                viewed=0
            )
            newDoctorNotification.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newPatientNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Assigned to Device: " + str(device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.userid,
                viewed=0
            )
            newPatientNotification.save()
        except:
            failedresponse = 0

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient is set to device"})

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
            inuse=1,
            isrecording=0,
            recordingduration=120,
            mintemperature=32,
            maxtemperature=40,
            minheartrate=60,
            maxheartrate=100,
        )

        device = Device.objects.get(deviceid=deviceid)
        patient = Patient.objects.get(patientid=patientid)
        device.status = 1
        device.borroweddate = datetime.datetime.now()
        patient.currentdeviceid = deviceid
        patient.deadlinereturndate = convert_date

        mqttc = mqtt.Client("Device " + str(deviceid))
        #mqttc.tls_set(tls_certificate)
        try:
            mqttc.connect(broker_ip, port_number)  # Change

            mqttc.publish("/devices/" + str(macaddress) + "/patient", patientdevice_id)
            mqttc.publish("/devices/" + str(macaddress) + "/record_duration", 120)
            mqttc.publish("/devices/" + str(macaddress) + "/change_temperature", "32_40")
            mqttc.publish("/devices/" + str(macaddress) + "/change_heartrate", "60_100")
            mqttc.publish("/devices/" + str(macaddress) + "/doctor", patient.doctorid.userid.userid)
            mqttc.publish("/devices/" + str(macaddress) + "/patientName", str(patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name))

            newPatientDevice.save()
            device.save()
            patient.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newDoctorNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Patient " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + " is set to Device " + str(device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.doctorid.userid,
                viewed=0
            )
            newDoctorNotification.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newPatientNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Assigned to Device: " + str(device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.userid,
                viewed=0
            )
            newPatientNotification.save()
        except:
            failedresponse = 0

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient is set to a new device"})

        return JsonResponse(response, safe=False)


@login_required()
def stop_recording(request):
    data = request.GET.get('data', None)
    patientdeviceId = request.GET.get('deviceid', None)
    patientdevice = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    deviceId = patientdevice.device_deviceid.deviceid
    macaddress = Device.objects.get(deviceid=deviceId).macaddress
    failedresponse = 1

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    if data == "0":
        description = "The device is recording (started by your assigned doctor)"
    else:
        description = "The device stopped recording (stopped by your assigned doctor)"

    newPatientNotification = Notifications(
        notificationid=notificationid,
        notificationdescription=description,
        datetime=datetime.datetime.now(),
        userid=patientdevice.patient_patientid.userid,
        viewed=0
    )

    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set(tls_certificate)
    try:
        mqttc.connect(broker_ip, port_number)

        mqttc.publish("/devices/" + str(macaddress) + "/stop", data)

        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)

        if data == "0":
            patientdeviceobject.isrecording = 1
        else:
            patientdeviceobject.isrecording = 0

        patientdeviceobject.save()
        newPatientNotification.save()
    except:
        failedresponse = 0

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


@login_required()
def set_recording_duration(request):
    hours = request.GET.get('hours', None)
    minutes = request.GET.get('minutes', None)
    seconds = request.GET.get('seconds', None)

    total_seconds = (int(hours)*60*60)+(int(minutes)*60)+int(seconds)

    patientdeviceId = request.GET.get('deviceid', None)
    patientdevice = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    deviceId = patientdevice.device_deviceid.deviceid
    macaddress = Device.objects.get(deviceid=deviceId).macaddress
    failedresponse = 1

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    newPatientNotification = Notifications(
        notificationid=notificationid,
        notificationdescription="Device Recording Duration is now set to: " + str(total_seconds) + " seconds",
        datetime=datetime.datetime.now(),
        userid=patientdevice.patient_patientid.userid,
        viewed=0
    )
    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set(tls_certificate)
    try:
        mqttc.connect(broker_ip, port_number)

        mqttc.publish("/devices/" + str(macaddress) + "/record_duration", total_seconds)


        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
        patientdeviceobject.recordingduration = total_seconds
        patientdeviceobject.save()
        newPatientNotification.save()
    except:
        failedresponse = 0

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


@login_required()
def set_min_max_temperature(request):
    mintemp = request.GET.get('mintemp', None)
    maxtemp = request.GET.get('maxtemp', None)

    mintemp_maxtemp = mintemp + "_" + maxtemp

    patientdeviceId = request.GET.get('deviceid', None)
    patientdevice = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    deviceId = patientdevice.device_deviceid.deviceid
    macaddress = Device.objects.get(deviceid=deviceId).macaddress
    failedresponse = 1

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    newPatientNotification = Notifications(
        notificationid=notificationid,
        notificationdescription="Device Temperature Thresholds is now set to: Minimum:" + mintemp + "°C; Maximum: " + maxtemp + "°C",
        datetime=datetime.datetime.now(),
        userid=patientdevice.patient_patientid.userid,
        viewed=0
    )

    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set(tls_certificate)
    try:
        mqttc.connect(broker_ip, port_number)

        mqttc.publish("/devices/" + str(macaddress) + "/change_temperature", mintemp_maxtemp)

        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
        patientdeviceobject.mintemperature = mintemp
        patientdeviceobject.maxtemperature = maxtemp
        patientdeviceobject.save()
        newPatientNotification.save()
    except:
        failedresponse = 0

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


@login_required()
def set_min_max_heartrate(request):
    minheartrate = request.GET.get('minheartrate', None)
    maxheartrate = request.GET.get('maxheartrate', None)

    minheartrate_maxheartrate = minheartrate + "_" + maxheartrate

    patientdeviceId = request.GET.get('deviceid', None)
    patientdevice = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    deviceId = patientdevice.device_deviceid.deviceid
    macaddress = Device.objects.get(deviceid=deviceId).macaddress
    failedresponse = 1

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    newPatientNotification = Notifications(
        notificationid=notificationid,
        notificationdescription="Device Heart Rate Thresholds is now set to: Minimum:" + minheartrate + "°C; Maximum: " + maxheartrate + "°C",
        datetime=datetime.datetime.now(),
        userid=patientdevice.patient_patientid.userid,
        viewed=0
    )

    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set(tls_certificate)
    try:
        mqttc.connect(broker_ip, port_number)

        mqttc.publish("/devices/" + str(macaddress) + "/change_heartrate", minheartrate_maxheartrate)

        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
        patientdeviceobject.minheartrate = minheartrate
        patientdeviceobject.maxheartrate = maxheartrate
        patientdeviceobject.save()
        newPatientNotification.save()
    except:
        failedresponse = 0

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


@login_required()
def set_remarks(request):
    remarks = request.GET.get('remarks', None)

    patientdeviceId = request.GET.get('deviceid', None)

    patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    patientdeviceobject.remarks = remarks
    patientdeviceobject.save()

    response = []

    response.append({'response': "Remarks Updated"})

    return JsonResponse(response, safe=False)


@login_required()
def unassign_patient(request):
    deviceid = request.GET.get('deviceID', None)

    is_assigned = PatientDevice.objects.filter(device_deviceid=deviceid, inuse=1).exists()

    macaddress = Device.objects.get(deviceid=deviceid).macaddress

    response = []

    failedresponse = 1

    if is_assigned:
        mqttc = mqtt.Client("Device " + str(deviceid))
        #mqttc.tls_set(tls_certificate)
        try:
            mqttc.connect(broker_ip, port_number)

            mqttc.publish("/devices/" + str(macaddress) + "/patient", 0)

            patientdevice = PatientDevice.objects.get(device_deviceid=deviceid, inuse=1)
            device = Device.objects.get(deviceid=deviceid)
            patient = Patient.objects.get(currentdeviceid=deviceid)
            patientdevice.inuse = 0
            patientdevice.save()
            device.status = 0
            device.returneddate = datetime.datetime.now()
            device.save()
            patient.currentdeviceid = 0
            patient.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newDoctorNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Patient: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + ", is unassigned from Device " + str(device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.doctorid.userid,
                viewed=0
            )
            newDoctorNotification.save()

            if Notifications.objects.all().count() == 0:
                notificationid = 1
            else:
                notificationid = Notifications.objects.all().count() + 1

            newPatientNotification = Notifications(
                notificationid=notificationid,
                notificationdescription="Unassigned from Device: " + str(device.deviceid),
                datetime=datetime.datetime.now(),
                userid=patient.userid,
                viewed=0
            )
            newPatientNotification.save()
        except:
            failedresponse = 0

        if failedresponse == 0:
            response.append({'outcome': "Failed to connect to the device. Try again later."})
        else:
            response.append({'outcome': "Patient unassigned"})

        return JsonResponse(response, safe=False)

    else:
        response.append({'outcome': "No patient assigned"})

        return JsonResponse(response, safe=False)


@login_required()
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

        temperature_records = Temperature.objects.filter(patientdeviceid__in=patientdevice, timestamp__year=convert_date.year, timestamp__month=convert_date.month)
        temperature_distinct_date_records = temperature_records.values_list('patientdeviceid', 'timestamp').distinct()

        vitals_dates_list = []
        vitals_patientdeviceid_dates_list = []
        for temperature_data in temperature_distinct_date_records:
            if not vitals_dates_list.__contains__(temperature_data[1].date()):
                vitals_dates_list.append(temperature_data[1].date())
                vitals_patientdeviceid_dates_list.append({
                    'date': temperature_data[1].date(),
                    'patientdeviceid': temperature_data[0]
                })

        if vitals_dates_list.__len__() != 0:
            for vital_record in vitals_patientdeviceid_dates_list:
                records_list.append({
                    'date': vital_record.get('date').strftime('%B %d, %Y'),
                    'recordtype': 2,
                    'data': vital_record.get('date'),
                    'patientdeviceid': vital_record.get('patientdeviceid'),
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

    return JsonResponse(records_list, safe=False)


@login_required()
def check_device_status(request):
    patientdeviceId = request.GET.get('patientdeviceid', None)
    patientdevicestatus = PatientDevice.objects.get(patientdeviceid=patientdeviceId).isrecording
    duration = PatientDevice.objects.get(patientdeviceid=patientdeviceId).recordingduration
    mintemperature = PatientDevice.objects.get(patientdeviceid=patientdeviceId).mintemperature
    maxtemperature = PatientDevice.objects.get(patientdeviceid=patientdeviceId).maxtemperature
    minheartrate = PatientDevice.objects.get(patientdeviceid=patientdeviceId).minheartrate
    maxheartrate = PatientDevice.objects.get(patientdeviceid=patientdeviceId).maxheartrate
    remarks = PatientDevice.objects.get(patientdeviceid=patientdeviceId).remarks

    status = []

    status.append({
        'status': patientdevicestatus,
        'duration': duration,
        'mintemperature': mintemperature,
        'maxtemperature': maxtemperature,
        'minheartrate': minheartrate,
        'maxheartrate': maxheartrate,
        'remarks': remarks,
    })

    return JsonResponse(status, safe=False)


@login_required()
def get_ecg_batch(request):
    currentBatch = request.GET.get('currentBatch', None)
    patient_device_id = request.GET.get('patientdeviceid', None)
    direction = request.GET.get('direction', None)
    batch = request.GET.get('batch', None)
    date = request.GET.get('date', None)

    if date == "":
        convert_date = datetime.datetime.today()
    else:
        convert_date = datetime.datetime.strptime(date, '%B %d, %Y')

    patient_device = PatientDevice.objects.get(patientdeviceid=patient_device_id)

    if batch == "-1":
        ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid, timestamp__date=convert_date)
    else:
        ecg_list = Ecg.objects.order_by(F('timestamp').asc()).filter(patientdeviceid=patient_device.patientdeviceid,
                                                                     timestamp__date=convert_date, batchid=batch)
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


@login_required()
def update_patient_restrictions(request):
    patient_id = request.GET.get('patient_id', None)
    medicalInformation = request.GET.get('medicalInformation', None)
    vitalRecords = request.GET.get('vitalRecords', None)

    patient = Patient.objects.get(patientid=patient_id)

    patient.restrictmedicalinformationaccess = medicalInformation
    patient.restrictvitalsinformationaccess = vitalRecords

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    description = "Patient: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + ", has: "

    if medicalInformation == 1:
        description += "Restricted you from accessing their Medical Information Records "
    else:
        description += "Allowed you to access their Medical Information Records "

    if vitalRecords == 1:
        description += "& Restricted you from accessing their Vital Records"
    else:
        description += "& Allowed you to access their Vital Records"

    newDoctorNotification = Notifications(
        notificationid=notificationid,
        notificationdescription=description,
        datetime=datetime.datetime.now(),
        userid=patient.doctorid.userid,
        viewed=0
    )
    newDoctorNotification.save()


    patient.save()
    response = []

    response.append({'response': 'Restrictions Updated'})

    return JsonResponse(response, safe=False)


@login_required()
def update_user_account(request):
    user_id = request.GET.get('user_id', None)
    birthday = request.GET.get('birthday', None)
    contactno = request.GET.get('contactno', None)
    email = request.GET.get('email', None)
    password = request.GET.get('password', None)
    repeatpassword = request.GET.get('repeatpassword', None)
    bloodtype = request.GET.get('bloodtype', None)
    sex = request.GET.get('sex', None)

    user = User.objects.get(id=user_id)
    user_details = Userdetails.objects.get(userid=user_id)

    if user_details.usertype.usertypeid == 3:
        user_type = Doctor.objects.get(userid=user_id)
    else:
        user_type = Patient.objects.get(userid=user_id)

    response = []
    error = 0

    error_message = "Missing/Wrong information: \n"
    if birthday == "":
        error_message += "Birthday\n"
        error = 1

    if contactno == "":
        error_message += "Contact number\n"
        error = 1

    if email == "":
        error_message += "Email\n"
        error = 1

    if password == "":
        error_message += "Password\n"
        error = 1

    if repeatpassword == "":
        error_message += "Password\n"
        error = 1

    if password != repeatpassword:
        error_message += "Password and Repeat password is not the same\n"
        error = 1

    if password != "-1":
        try:
            validate_password(password)
            user.set_password(password)
        except ValidationError as e:
            error_message += str(e) + "\n"
            error = 1

    if error == 0:
        user_details.birthday = birthday
        user.email = email
        user_details.contactno = contactno

        if bloodtype != "-1":
            user_type.bloodtype = bloodtype
            user_type.save()

        if sex != "-1":
            user_details.sex = sex


        user_details.save()
        user.save()


        response.append("Account information updated")
    else:
        response.append(error_message)

    return JsonResponse(response, safe=False)


def get_alerts_count(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    alerts = Alerts.objects.filter(patientdeviceid__patient_patientid__doctorid=doctorid.doctorid, viewed=0, patientdeviceid__inuse=1)

    count = []

    count.append(alerts.count())
    return JsonResponse(count, safe=False)


@login_required()
def add_comment(request):
    comment = request.GET.get('comment', None)
    timestamp = request.GET.get('timestamp', None)
    typeofvital = RefTypeofvital.objects.get(typeofvitalid=request.GET.get('typeofvital', None))
    patientdeviceid = PatientDevice.objects.get(patientdeviceid=request.GET.get('patientdeviceid', None))

    if Comments.objects.all().count() == 0:
        commentid = 1
    else:
        commentid = Comments.objects.all().count() + 1

    newComment = Comments(
        commentid=commentid,
        comment=comment,
        patientdeviceid=patientdeviceid,
        timestamp=timestamp,
        typeofvital=typeofvital,
    )
    newComment.save()

    response = []
    response.append("Comment added")
    return JsonResponse(response, safe=False)


@login_required()
def save_configuration(request):
    presetname = request.GET.get('presetname', None)
    doctorid = request.GET.get('doctorid', None)
    recordingduration = request.GET.get('recordingduration', None)
    mintemperature = request.GET.get('mintemperature', None)
    maxtemperature = request.GET.get('maxtemperature', None)
    minheartrate = request.GET.get('minheartrate', None)
    maxheartrate = request.GET.get('maxheartrate', None)


    if Presets.objects.all().count() == 0:
        presetid = 1
    else:
        presetid = Presets.objects.all().count() + 1

    newPreset = Presets(
        presetid=presetid,
        presetname=presetname,
        doctorid=Doctor.objects.get(doctorid=doctorid),
        recordingduration=recordingduration,
        mintemperature=mintemperature,
        maxtemperature=maxtemperature,
        minheartrate=minheartrate,
        maxheartrate=maxheartrate,
    )

    response = []

    if Presets.objects.filter(presetname=presetname, doctorid=newPreset.doctorid).exists():
        response.append("Preset Name already exists!")
    elif Presets.objects.filter(doctorid=newPreset.doctorid, recordingduration=recordingduration, mintemperature=mintemperature, maxtemperature=maxtemperature, minheartrate=minheartrate, maxheartrate=maxheartrate).exists():
        response.append("Configuration preset already exist!")
    else:
        newPreset.save()

    return JsonResponse(response, safe=False)


@login_required()
def check_preset(request):
    presetid = request.GET.get('presetID', None)

    preset = Presets.objects.get(presetid=presetid)

    presetConfigurations = []

    presetConfigurations.append({
        'presetid': preset.presetid,
        'recordingduration': preset.recordingduration,
        'mintemperature': preset.mintemperature,
        'maxtemperature': preset.maxtemperature,
        'minheartrate': preset.minheartrate,
        'maxheartrate': preset.maxheartrate,
    })

    return JsonResponse(presetConfigurations, safe=False)


@login_required()
def load_preset(request):
    minheartrate = request.GET.get('minheartrate', None)
    maxheartrate = request.GET.get('maxheartrate', None)
    mintemp = request.GET.get('mintemperature', None)
    maxtemp = request.GET.get('maxtemperature', None)
    duration = request.GET.get('duration', None)

    minheartrate_maxheartrate = minheartrate + "_" + maxheartrate
    mintemp_maxtemp = mintemp + "_" + maxtemp


    patientdeviceId = request.GET.get('deviceid', None)
    patientdevice = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
    deviceId = patientdevice.device_deviceid.deviceid
    macaddress = Device.objects.get(deviceid=deviceId).macaddress
    failedresponse = 1

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    newPatientNotification = Notifications(
        notificationid=notificationid,
        notificationdescription="Device Configurations Changed. Go to Homepage to check new configurations",
        datetime=datetime.datetime.now(),
        userid=patientdevice.patient_patientid.userid,
        viewed=0
    )

    newPatientNotification.save()

    mqttc = mqtt.Client("Device " + str(deviceId))
    #mqttc.tls_set(tls_certificate)
    try:
        mqttc.connect(broker_ip, port_number)

        mqttc.publish("/devices/" + str(macaddress) + "/change_heartrate", minheartrate_maxheartrate)
        mqttc.publish("/devices/" + str(macaddress) + "/change_temperature", mintemp_maxtemp)
        mqttc.publish("/devices/" + str(macaddress) + "/record_duration", duration)

        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceId)
        patientdeviceobject.minheartrate = minheartrate
        patientdeviceobject.maxheartrate = maxheartrate
        patientdeviceobject.mintemperature = mintemp
        patientdeviceobject.maxtemperature = maxtemp
        patientdeviceobject.recordingduration = duration
        patientdeviceobject.save()
    except:
        failedresponse = 0

    response = []

    if failedresponse == 0:
        response.append({'response': "Failed to connect to the device. Try again later."})
    else:
        response.append({'response': "Published"})

    return JsonResponse(response, safe=False)


@login_required()
def edit_user_account(request):
    user_id = request.GET.get('user_id', None)
    firstname = request.GET.get('firstname', None)
    middlename = request.GET.get('middlename', None)
    lastname = request.GET.get('lastname', None)
    birthday = request.GET.get('birthday', None)
    contactno = request.GET.get('contactno', None)
    email = request.GET.get('email', None)
    password = request.GET.get('password', None)
    repeatpassword = request.GET.get('repeatpassword', None)
    doctor = request.GET.get('doctor', None)
    ifchangedoctor = request.GET.get('ifchangedoctor', None)

    user = User.objects.get(id=user_id)
    user_details = Userdetails.objects.get(userid=user_id)

    response = []
    error = 0

    error_message = "Missing/Wrong information: \n"

    if firstname == "":
        error_message += "First Name\n"
        error = 1

    if middlename == "":
        error_message += "Middle Name\n"
        error = 1

    if lastname == "":
        error_message += "Last Name\n"
        error = 1

    if birthday == "":
        error_message += "Birthday\n"
        error = 1

    if contactno == "":
        error_message += "Contact number\n"
        error = 1

    if email == "":
        error_message += "Email\n"
        error = 1

    if password == "":
        error_message += "Password\n"
        error = 1

    if repeatpassword == "":
        error_message += "Password\n"
        error = 1

    if password != repeatpassword:
        error_message += "Password and Repeat password is not the same\n"
        error = 1

    if password != "-1":
        try:
            validate_password(password)
            user.set_password(password)
        except ValidationError as e:
            error_message += str(e) + "\n"
            error = 1

    if error == 0:
        user.first_name = firstname
        user.last_name = lastname
        user_details.middlename = middlename
        user_details.birthday = birthday
        user.email = email
        user_details.contactno = contactno

        if ifchangedoctor == "0":
            patient = Patient.objects.get(userid=user_details)
            previousDoctor = patient.doctorid
            patient.doctorid = Doctor.objects.get(doctorid=doctor)

            if PatientDoctor.objects.filter(doctorid=doctor, patientid=patient).exists():
                previousassigned = PatientDoctor.objects.get(patientid=patient, assigneddoctor=1)
                previousassigned.delete()
                patientdoctor = PatientDoctor.objects.get(doctorid=doctor, patientid=patient)
                patientdoctor.assigneddoctor = 1
                patientdoctor.save()
            else:
                previousassigned = PatientDoctor.objects.get(patientid=patient, assigneddoctor=1)
                previousassigned.delete()
                if PatientDoctor.objects.count() == 0:
                    patientdoctorid = 1
                else:
                    patientdoctorid = PatientDoctor.objects.latest('patientdoctorid').patientdoctorid + 1

                newPatientDoctor = PatientDoctor(
                    patientdoctorid=patientdoctorid,
                    patientid=patient,
                    doctorid=patient.doctorid,
                    restrictmedicalinformationaccess=0,
                    restrictvitalsinformationaccess=0,
                    assigneddoctor=1,
                )
                newPatientDoctor.save()

            patient.save()

            if patient.doctorid != previousDoctor:
                if Notifications.objects.all().count() == 0:
                    notificationid = 1
                else:
                    notificationid = Notifications.objects.all().count() + 1

                newDoctorNotification = Notifications(
                    notificationid=notificationid,
                    notificationdescription="Patient: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + ", no longer assigned",
                    datetime=datetime.datetime.now(),
                    userid=previousDoctor.userid,
                    viewed=0
                )
                newDoctorNotification.save()

                if Notifications.objects.all().count() == 0:
                    notificationid = 1
                else:
                    notificationid = Notifications.objects.all().count() + 1

                newDoctorNotification = Notifications(
                    notificationid=notificationid,
                    notificationdescription="New assigned patient. Patient name: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name,
                    datetime=datetime.datetime.now(),
                    userid=patient.doctorid.userid,
                    viewed=0
                )

                newDoctorNotification.save()

                if Notifications.objects.all().count() == 0:
                    notificationid = 1
                else:
                    notificationid = Notifications.objects.all().count() + 1

                newPatientNotification = Notifications(
                    notificationid=notificationid,
                    notificationdescription="New assigned doctor. Doctor name: " + patient.doctorid.userid.auth_user_id.first_name + " " + patient.doctorid.userid.auth_user_id.last_name,
                    datetime=datetime.datetime.now(),
                    userid=patient.userid,
                    viewed=0
                )

                newPatientNotification.save()

        user_details.save()
        user.save()

        if Notifications.objects.all().count() == 0:
            notificationid = 1
        else:
            notificationid = Notifications.objects.all().count() + 1
        newNotification = Notifications(
            notificationid=notificationid,
            notificationdescription="Account information was updated by the admin.",
            datetime=datetime.datetime.now(),
            userid=user_details,
            viewed=0
        )

        newNotification.save()

        response.append("Account information updated")
    else:
        response.append(error_message)

    return JsonResponse(response, safe=False)


@login_required()
def user_account_activation_set_password(request):
    user_id = request.GET.get('user_id', None)
    password = request.GET.get('password', None)
    repeatpassword = request.GET.get('repeatpassword', None)

    user = User.objects.get(id=user_id)

    response = []
    error = 0

    error_message = "Missing/Wrong information: \n"

    if password == "":
        error_message += "Password\n"
        error = 1

    if repeatpassword == "":
        error_message += "Password\n"
        error = 1

    if password != repeatpassword:
        error_message += "Password and Repeat password is not the same\n"
        error = 1

    if password != "-1":
        try:
            validate_password(password)
            user.set_password(password)
        except ValidationError as e:
            error_message += str(e) + "\n"
            error = 1

    if error == 0:
        user.is_active = True
        user.save()
        response.append("Account activated")
    else:
        response.append(error_message)
    return JsonResponse(response, safe=False)


@login_required()
def summary(request):
    patientdevice_id = request.GET.get('patientDeviceID', None)
    date = request.GET.get('date', None)

    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)
    patient = Patient.objects.get(patientid=patient_device.patient_patientid_id)
    temperature_list = Temperature.objects.raw(
        "SELECT temperatureID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM temperature WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")

    temperature_data_array = []
    temperature_timestamp_array = []
    for temperature in temperature_list:
        temperature_data_array.append(float(temperature.data))
        temperature_timestamp_array.append(temperature.timestamp)

    if temperature_data_array.__len__() != 0:
        latest_temperature = temperature_data_array[temperature_data_array.__len__() - 1]
        latest_temperature_time = temperature_timestamp_array[temperature_timestamp_array.__len__() - 1]
        average_temperature = sum(temperature_data_array) / len(temperature_data_array)

        min_temperature = min(temperature_data_array)
        min_temperature_index = temperature_data_array.index(min_temperature)
        min_temperature_time = temperature_timestamp_array[min_temperature_index].time()

        max_temperature = max(temperature_data_array)
        max_temperature_index = temperature_data_array.index(max_temperature)
        max_temperature_time = temperature_timestamp_array[max_temperature_index].time()
    else:
        latest_temperature = "N/A"
        latest_temperature_time = "N/A"
        average_temperature = "N/A"

        min_temperature = "N/A"
        min_temperature_index = "N/A"
        min_temperature_time = "N/A"

        max_temperature = "N/A"
        max_temperature_index = "N/A"
        max_temperature_time = "N/A"

    heartrate_list = Heartrate.objects.raw(
        "SELECT heartrateID, patientDeviceID, timestamp, CONVERT(AES_DECRYPT(data, UNHEX('e9fe29f77fd087f0f50a1e186c44d17c')) using utf8) as 'data', batchID FROM heartrate WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "') ORDER BY timestamp ASC;")

    heartrate_data_array = []
    heartrate_timestamp_array = []
    for heartrate in heartrate_list:
        heartrate_data_array.append(float(heartrate.data))
        heartrate_timestamp_array.append(heartrate.timestamp)

    if heartrate_data_array.__len__() != 0:
        latest_heartrate = heartrate_data_array[heartrate_data_array.__len__() - 1]

        average_heartrate = sum(heartrate_data_array) / len(heartrate_data_array)

        min_heartrate = min(heartrate_data_array)
        min_heartrate_index = heartrate_data_array.index(min_heartrate)
        min_heartrate_time = heartrate_timestamp_array[min_heartrate_index].time()

        max_heartrate = max(heartrate_data_array)
        max_heartrate_index = heartrate_data_array.index(max_heartrate)
        max_heartrate_time = heartrate_timestamp_array[max_heartrate_index].time()
    else:
        latest_heartrate = "N/A"

        average_heartrate = "N/A"

        min_heartrate = "N/A"
        min_heartrate_index = "N/A"
        min_heartrate_time = "N/A"

        max_heartrate = "N/A"
        max_heartrate_index = "N/A"
        max_heartrate_time = "N/A"

    batch_count = Ecg.objects.raw(
        "SELECT ecgID, COUNT(DISTINCT(batchID)) as 'batchCount' FROM ecg WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "');")

    details = []

    details.append({
       'name': patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name,
       'device': patient_device.device_deviceid_id,
       'average_temperature': average_temperature,
       'latest_temperature': latest_temperature,
       'average_heartrate': average_heartrate,
       'latest_heartrate': latest_heartrate,
       'last_recorded_time': latest_temperature_time.time(),
       'date': datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
       'batch_count': batch_count[0].batchCount,
       'min_temperature': min_temperature,
       'max_temperature': max_temperature,
       'min_heartrate': min_heartrate,
       'max_heartrate': max_heartrate,
       'min_temperature_time': min_temperature_time,
       'max_temperature_time': max_temperature_time,
       'min_heartrate_time': min_heartrate_time,
       'max_heartrate_time': max_heartrate_time,
    })

    return JsonResponse(details, safe=False)


@login_required()
def add_new_doctor_restriction(request):
    patient_id = request.GET.get('patient_id', None)
    doctor_id = request.GET.get('doctor_id', None)
    medicalInformation = request.GET.get('medicalInformation', None)
    vitalRecords = request.GET.get('vitalRecords', None)

    patient = Patient.objects.get(patientid=patient_id)
    doctor = Doctor.objects.get(doctorid=doctor_id)

    if PatientDoctor.objects.count() == 0:
        patientdoctirid = 1
    else:
        patientdoctirid = PatientDoctor.objects.latest('patientdoctorid').patientdoctorid + 1

    newPatientDoctor = PatientDoctor(
        patientdoctorid=patientdoctirid,
        patientid=patient,
        doctorid=doctor,
        restrictmedicalinformationaccess=medicalInformation,
        restrictvitalsinformationaccess=vitalRecords,
        assigneddoctor=0,
    )
    newPatientDoctor.save()

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    description = "Patient: " + patient.userid.auth_user_id.first_name + " " + patient.userid.auth_user_id.last_name + ", Allowed you to view their: "

    if medicalInformation == 0:
        description += "Medical Information Records"
        if vitalRecords == 0:
            description += "& Vital Records"
    else:
        description += "Vital Records"

    newDoctorNotification = Notifications(
        notificationid=notificationid,
        notificationdescription=description,
        datetime=datetime.datetime.now(),
        userid=doctor.userid,
        viewed=0
    )
    newDoctorNotification.save()

    response = []

    response.append({'response': 'New Doctor Restrictions Created'})

    return JsonResponse(response, safe=False)


@login_required()
def edit_doctor_restriction(request):
    patientDoctorID = request.GET.get('patientDoctorID', None)
    medicalInformation = request.GET.get('medicalInformation', None)
    vitalRecords = request.GET.get('vitalRecords', None)

    patient_doctor = PatientDoctor.objects.get(patientdoctorid=patientDoctorID)

    patient_doctor.restrictmedicalinformationaccess = medicalInformation
    patient_doctor.restrictvitalsinformationaccess = vitalRecords

    patient_doctor.save()

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    description = "Patient: " + patient_doctor.patientid.userid.auth_user_id.first_name + " " + patient_doctor.patientid.userid.auth_user_id.last_name + ", has: "

    if medicalInformation == 1:
        description += "Restricted you from accessing their Medical Information Records "
    else:
        description += "Allowed you to access their Medical Information Records "

    if vitalRecords == 1:
        description += "& Restricted you from accessing their Vital Records"
    else:
        description += "& Allowed you to access their Vital Records"

    newDoctorNotification = Notifications(
        notificationid=notificationid,
        notificationdescription=description,
        datetime=datetime.datetime.now(),
        userid=patient_doctor.doctorid.userid,
        viewed=0
    )
    newDoctorNotification.save()

    response = []

    response.append({'response': 'Restrictions Updated'})

    return JsonResponse(response, safe=False)


def remove_doctor_restriction(request):
    patientDoctorID = request.GET.get('patientDoctorID', None)
    patient_doctor = PatientDoctor.objects.get(patientdoctorid=patientDoctorID)

    if Notifications.objects.all().count() == 0:
        notificationid = 1
    else:
        notificationid = Notifications.objects.all().count() + 1

    newDoctorNotification = Notifications(
        notificationid=notificationid,
        notificationdescription="Patient: " + patient_doctor.patientid.userid.auth_user_id.first_name + " " + patient_doctor.patientid.userid.auth_user_id.last_name + ", has Restricted you from accessing their Medical and Vital Records",
        datetime=datetime.datetime.now(),
        userid=patient_doctor.doctorid.userid,
        viewed=0
    )
    newDoctorNotification.save()

    patient_doctor.delete()
    response = []

    response.append({'response': 'Restrictions Removed'})

    return JsonResponse(response, safe=False)


@login_required()
def get_notification_count(request):
    userid = Userdetails.objects.get(userid=request.session['user_id'])
    notifications = Notifications.objects.filter(userid=userid, viewed=0)

    count = []

    count.append(notifications.count())
    return JsonResponse(count, safe=False)


@login_required()
def view_notifications(request):
    userid = Userdetails.objects.get(userid=request.session['user_id'])
    notifications = Notifications.objects.filter(userid=userid, viewed=0)

    for notification in notifications:
        notification.viewed = 1
        notification.save()

    count = []

    count.append(0)
    return JsonResponse(count, safe=False)


@login_required()
def view_alerts(request):
    doctorid = Doctor.objects.get(userid=request.session['user_id'])
    alerts = Alerts.objects.filter(patientdeviceid__patient_patientid__doctorid=doctorid.doctorid, patientdeviceid__inuse=1)

    for alert in alerts:
        alert.viewed = 1
        alert.save()

    count = []

    count.append(0)
    return JsonResponse(count, safe=False)


@login_required()
def check_deadline(request):
    patientdeviceid = request.GET.get('patientdeviceid', None)
    currentdate = datetime.date.today()
    patientid = PatientDevice.objects.get(patientdeviceid=patientdeviceid).patient_patientid.patientid
    patient_object = Patient.objects.get(patientid=patientid)
    daysbeforedeadline = patient_object.deadlinereturndate - currentdate

    details = []

    details.append({
        'daysbeforedeadline': daysbeforedeadline.days,
        'dateofdeadline': patient_object.deadlinereturndate.strftime('%B %d, %Y'),
    })

    return JsonResponse(details, safe=False)


@login_required()
def get_schedule(request):
    patientdeviceid = request.GET.get('patientdeviceid', None)
    patientschedule = PatientSchedule.objects.filter(patientdeviceid=patientdeviceid).order_by('dayid')
    scheduleList = []

    if patientschedule.exists():
        days = patientschedule.values('dayid').distinct()

        for day in days:
            dayobject = Day.objects.get(dayid=day['dayid'])
            patientscheduledaytime = PatientSchedule.objects.filter(patientdeviceid=patientdeviceid, dayid=dayobject).order_by('timeid')
            times = ""
            scheduleids = ""
            for patientscheduletime in patientscheduledaytime:
                times += str(patientscheduletime.timeid.actualtime) + " | "
                scheduleids += str(patientscheduletime.patientscheduleid) + ","
            scheduleList.append({
                'dayData': dayobject.actualday,
                'timesData': times,
                'scheduleids': scheduleids,
            })
    else:
        scheduleList.append({
            'patientscheduleid': -999
        })


    return JsonResponse(scheduleList, safe=False)


@login_required()
def add_schedule(request):
    patientdeviceid = request.GET.get('patientdeviceid', None)
    time = request.GET.get('time', None)
    days = request.GET.get('days', None)

    daysArray = days.split(" ")

    response = []

    for day in daysArray:
        if PatientSchedule.objects.all().count() == 0:
            patientscheduleid = 1
        else:
            patientscheduleid = PatientSchedule.objects.all().count() + 1

        timeid = Time.objects.get(timeid=time)
        dayid = Day.objects.get(dayid=day)
        patientdeviceobject = PatientDevice.objects.get(patientdeviceid=patientdeviceid)

        if PatientSchedule.objects.filter(patientdeviceid=patientdeviceobject, timeid=timeid, dayid=dayid).exists():
            response.append("Schedule: " + dayid.actualday + " " + timeid.actualtime + " already exists.")
        else:
            newSchedule = PatientSchedule(
                patientscheduleid=patientscheduleid,
                patientdeviceid=patientdeviceobject,
                timeid=timeid,
                dayid=dayid,
                earlyalert=0,
                beforerecordalert=0,
                recordalert=0,
                latealert=0,
                lastalert=0,
            )
            newSchedule.save()

    if response.__len__() == 0:
        response.append("Schedule created")

    return JsonResponse(response, safe=False)


@login_required()
def get_specific_schedule(request):
    scheduleid = request.GET.get('scheduleid', None)

    patientschedule = PatientSchedule.objects.get(patientscheduleid=scheduleid)

    scheduleDayList = []

    scheduleDayList.append({
        'scheduleid': patientschedule.patientscheduleid,
        'dayData': patientschedule.dayid.actualday,
        'timeData': patientschedule.timeid.actualtime
    })

    return JsonResponse(scheduleDayList, safe=False)


@login_required()
def remove_schedule(request):
    scheduleid = request.GET.get('scheduleid', None)

    patientschedule = PatientSchedule.objects.get(patientscheduleid=scheduleid)

    patientschedule.delete()

    response = []
    response.append("Schedule updated")

    return JsonResponse(response, safe=False)


def testing(request, patientdevice_id, date):
    convert_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    patient_device = PatientDevice.objects.get(patientdeviceid=patientdevice_id)

    batch_count = Ecg.objects.raw("SELECT ecgID, COUNT(DISTINCT(batchID)) as 'batchCount' FROM ecg WHERE (patientDeviceID = " + str(
            patient_device.patientdeviceid) + " AND DATE(timestamp) = '" + str(
            convert_date.date()) + "');")


    print(batch_count[0].batchCount)
    context={
        'testing': batch_count,
    }

    return render(request, 'testing.html', context)