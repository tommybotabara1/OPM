from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('loginuser/', views.loginuser, name='loginuser'),
    path('home/', views.home, name='home'),
    path('listofusers/', views.listofusers, name='listofusers'),
    path('createuser/', views.createuser, name='createuser'),
    path('archiving/', views.archiving, name='archiving'),
    path('changeuserofdevice/', views.changeuserofdevice, name='changeuserofdevice'),
    path('viewassignedpatients/', views.viewassignedpatients, name='viewassignedpatients'),
    path('changerecordinginterval/', views.changerecordinginterval, name='changerecordinginterval'),
    path('stoprecording/', views.stoprecording, name='stoprecording'),
    path('viewcurrentvitals/', views.viewcurrentvitals, name='viewcurrentvitals'),
    path('viewhistoryofvitals/', views.viewhistoryofvitals, name='viewhistoryofvitals'),
    path('restrictuseraccess/', views.restrictuseraccess, name='restrictuseraccess'),
    path('viewassignedpatients/<int:patient_id>/vitals/', views.assignedpatientvitals, name='patientvitals'),
    path('listofusers/<int:user_id>/edituser/', views.edituser, name='edituser'),
    path('ajax/validate_username/', views.validate_username, name='validate_username'),
    path('ajax/search_user/', views.search_user, name='search_user'),
    path('ajax/add_device/', views.add_device, name='add_device'),
]

