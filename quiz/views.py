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
    """
    Returns all the questions list in a get method
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        valid_questions =  models.Questions.objects.filter(is_active=True)
        serializer = serializers.QuestionListSerializer(valid_questions, many=True)

        return Response({
            'Total num. of Questions':valid_questions.count(),
            'All questions':serializer.data
        },status=status.HTTP_200_OK)

class QuestionDetailView(APIView):
    """
    Returns a question details with get method
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request,pk):
        try:
            question = models.Questions.objects.get(pk=pk,is_active=True)
            serializer = serializers.QuestionDetailSerializer(question)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except models.Questions.DoesNotExist:
            return Response(
            {'error':'Question not found'},status=status.HTTP_404_NOT_FOUND
            )

class SubmitAnswerView(APIView):
    """
    User answer submission, Validate answer correctness, save submitted answer
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = serializers.AnswerSubmissionSerializer(data=request.data)
        print(serializer)

        if serializer.is_valid():
            # Check user has submitted the answer previously
            question = serializer.validated_data['question']
            selected_answer = serializer.validated_data['selected_answer']

            if models.UserSolutions.objects.filter(user=request.user,question=question).exists():
                return Response(
                {"error": "You have already answered this question."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check the submitted answer is correct or not
            is_correct = selected_answer.is_correct
            serializer.save(user=request.user,is_correct=is_correct)

            return Response(
                {
                    'msg':'Solution submitted successfully.',
                    'is_correct':is_correct,
                },status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPracticeHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        history = models.UserSolutions.objects.filter(user=request.user).distinct('question')
        no_correct_answers = history.filter(is_correct=True).count()
        serializer = serializers.UserHistorySerializer(history, many=True)
        # correct_answered =
        return Response({
            'Num of questions attempted':history.count(),
            'no_correct_answers':no_correct_answers,
            'question data':serializer.data
        },status=status.HTTP_200_OK)