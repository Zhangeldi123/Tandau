
from django.contrib import admin
from django.urls import path,include
from quiz.views import HomeView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('quiz.urls')),
    path('', HomeView.as_view(), name='home'),
]