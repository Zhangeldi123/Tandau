from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestViewSet, TestSessionViewSet, CompetitiveSessionViewSet

router = DefaultRouter()
router.register(r'tests', TestViewSet, basename='test')
router.register(r'sessions', TestSessionViewSet, basename='test-session')
router.register(r'competitive', CompetitiveSessionViewSet, basename='competitive-session')

urlpatterns = [
    path('', include(router.urls)),
]
