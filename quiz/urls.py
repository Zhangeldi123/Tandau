from django.urls import path
from .views import *

urlpatterns=[
    path("register/", RegistrationView.as_view(),name='register'),
    path("login/", LoginView.as_view(),name='login'),
    path("questionlist/", QuestionListView.as_view(),name='QuestionList'),
    path("question-detail/<int:pk>",QuestionDetailView.as_view(),name="QuestionDetail"),
    path("submit-answer/",SubmitAnswerView.as_view(),name="SubmitAnswer"),
    path("user_history/",UserPracticeHistoryView.as_view(),name="UserPracticeHistory"),
]