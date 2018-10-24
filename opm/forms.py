from django import forms

from .models import Userdetails, Doctor, Patient, RefUsertype
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    username = forms.CharField(max_length=45)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Userdetails
        fields = ('username', 'password')

class CreateUserForm(forms.Form):

    USERTYPE_CHOICES=[]

    USERTYPE_CHOICES.extend([(3, 'Doctor'),(4, 'Patient')])

    DOCTOR_CHOICES=[]

    for doctor in Doctor.objects.all():
        DOCTOR_CHOICES.extend([(doctor.doctorid, doctor.userid.auth_user_id.first_name + " " + doctor.userid.auth_user_id.last_name)])

    if Doctor.objects.all().count() == 0:
        DOCTOR_CHOICES.extend([(-1, "No doctor users!")])

    username = forms.CharField(max_length=45)
    firstname = forms.CharField(max_length=45, widget=forms.TextInput(attrs={'placeholder': 'ex: Juan', "onChange":'show()'}))
    middlename = forms.CharField(max_length=45, widget=forms.TextInput(attrs={'placeholder': 'ex: Flores'}))
    lastname = forms.CharField(max_length=45, widget=forms.TextInput(attrs={'placeholder': 'ex: Dela Cruz'}))
    password = forms.CharField(widget=forms.PasswordInput)
    repeatPassword = forms.CharField(widget=forms.PasswordInput)
    email = forms.CharField(widget=forms.EmailInput)
    birthday = forms.DateField(widget=forms.DateInput(attrs={'placeholder': 'ex: 1998-05-27'}))
    contactno = forms.CharField(max_length=45, widget=forms.NumberInput)
    usertype= forms.ChoiceField(widget=forms.RadioSelect(attrs={"onChange":'show()'}), choices=USERTYPE_CHOICES)
    doctorid = forms.ChoiceField(choices=DOCTOR_CHOICES, widget=forms.Select(attrs={"class": 'browser-default col s7'}))


class EditUserForm(forms.Form):

    def __init__(self, user):
        self.userid =  user.id
        super(EditUserForm, self).__init__()
        edit_user = User.objects.get(id=user.id)
        self.fields['username'].initial = edit_user.username
        self.fields['username'].widget = forms.TextInput(attrs={'disabled':'disabled'})
        self.fields['firstname'].initial = edit_user.first_name
        self.fields['lastname'].initial = edit_user.last_name
        self.fields['email'].initial = edit_user.email
        edit_user_details = Userdetails.objects.get(auth_user_id=user.id)
        self.fields['middlename'].initial = edit_user_details.middlename
        self.fields['birthday'].initial = edit_user_details.birthday
        self.fields['contactno'].initial = edit_user_details.contactno

        DOCTOR_CHOICES = []

        doctor_list = Doctor.objects.exclude(userid=user.id)

        for doctor in doctor_list:
            DOCTOR_CHOICES.extend(
                [(doctor.doctorid, doctor.userid.auth_user_id.first_name + " " + doctor.userid.auth_user_id.last_name)])

        if Doctor.objects.all().count() == 0:
            DOCTOR_CHOICES.extend([(-1, "No doctor users!")])

        self.fields['doctorid'].choices = DOCTOR_CHOICES


    USERTYPE_CHOICES = []

    USERTYPE_CHOICES.extend([(3, 'Doctor'), (4, 'Patient')])



    username = forms.CharField(max_length=45)
    firstname = forms.CharField(max_length=45,
                                widget=forms.TextInput(attrs={'placeholder': 'ex: Juan', "onChange": 'show()'}))
    middlename = forms.CharField(max_length=45, widget=forms.TextInput(attrs={'placeholder': 'ex: Flores'}))
    lastname = forms.CharField(max_length=45, widget=forms.TextInput(attrs={'placeholder': 'ex: Dela Cruz'}))
    password = forms.CharField(widget=forms.PasswordInput)
    repeatPassword = forms.CharField(widget=forms.PasswordInput)
    email = forms.CharField(widget=forms.EmailInput)
    birthday = forms.DateField(widget=forms.DateInput(attrs={'placeholder': 'ex: 1998-05-27'}))
    contactno = forms.CharField(max_length=45, widget=forms.NumberInput)
    usertype = forms.ChoiceField(widget=forms.RadioSelect(attrs={"onChange": 'show()'}), choices=USERTYPE_CHOICES)
    doctorid = forms.ChoiceField(widget=forms.Select(attrs={"class": 'browser-default col s7'}))