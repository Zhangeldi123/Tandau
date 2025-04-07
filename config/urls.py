from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/quiz/', include('quiz.urls')),
    path('api/users/', include('users.urls')),
]
