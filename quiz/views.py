from django.contrib.auth import authenticate
from django.core.serializers import serialize
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status,permissions
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from . import models,serializers

def get_tokens(user):
    refresh_token = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh_token),
        'access' : str(refresh_token.access_token)
    }

class RegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_tokens(user)
            return Response({
                'token':token,
                'msg':'Registration success'
            },status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data.get("email")
            password = serializer.data.get("password")
            user = authenticate(email=email,password=password)
            if user:
                token = get_tokens(user)
                return Response({
                    'token':token,
                    'msg': "Login Success",
                    'email': user.email,
                },status=status.HTTP_200_OK)
            else:
                return Response({
                    'errors':'email or password is incorrect'
                },status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        valid_questions =  models.Questions.objects.filter(is_active=True)
        serializer = serializers.QuestionListSerializer(valid_questions, many=True)

        return Response({
            'count':valid_questions.count(),
            'data':serializer.data
        },status=status.HTTP_200_OK)