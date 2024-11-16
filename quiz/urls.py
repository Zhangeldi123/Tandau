from django.urls import path
from .views import RegistrationView,LoginView,QuestionListView

urlpatterns=[
    path("register/", RegistrationView.as_view(),name='register'),
    path("login/", LoginView.as_view(),name='login'),
    path("questionlist/", QuestionListView.as_view(),name='QuestionList')
]