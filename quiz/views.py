from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
import os
import random
from openai import OpenAI
from .models import (
    Test, Question, Answer, TestSession,
    UserResponse, CompetitiveSession
)
from .serializers import (
    TestSerializer, TestDetailSerializer, QuestionCreateSerializer,
    TestSessionSerializer, UserResponseSerializer, CompetitiveSessionSerializer,
    LeaderboardEntrySerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.creator == request.user


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestDetailSerializer
        return TestSerializer

    def get_queryset(self):
        """Filter tests based on query parameters"""
        queryset = Test.objects.all()

        # Filter by creator
        creator = self.request.query_params.get('creator')
        if creator:
            queryset = queryset.filter(creator__username=creator)

        # Filter by mode
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(mode=mode)

        # Filter by active status
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)

        return queryset

    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        """Add a question to a test"""
        test = self.get_object()

        # Check if the user is the creator of the test
        if test.creator != request.user:
            return Response(
                {"detail": "You do not have permission to add questions to this test."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create the serializer with the test
        serializer = QuestionCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(test=test)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_variant(self, request, pk=None):
        """Create a variant of this test with rearranged questions"""
        test = self.get_object()

        # Check if the user is the creator of the test
        if test.creator != request.user:
            return Response(
                {"detail": "You do not have permission to create variants of this test."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create the variant
        variant = test.create_variant()
        serializer = TestSerializer(variant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def generate_blitz(self, request, pk=None):
        """Generate a blitz quiz using ChatGPT based on this test"""
        test = self.get_object()

        # Check if the user is the creator of the test
        if test.creator != request.user:
            return Response(
                {"detail": "You do not have permission to generate quizzes from this test."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if OpenAI API key is configured
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return Response(
                {"detail": "OpenAI API key is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            # Get the topic from the test title and description
            topic = f"{test.title}. {test.description}"

            client = OpenAI(
                api_key="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",
                base_url="https://openrouter.ai/api/v1"
            )

            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates quiz questions."},
                    {"role": "user", "content": f"Generate 20 multiple-choice questions about {topic}. "
                                                f"For each question, provide 4 options and indicate the correct answer. "
                                                f"Format as JSON with structure: "
                                                f"[{{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct\": \"A\"}}] "
                                                f"Return only the JSON array."}
                ]
            )

            generated_content = response.choices[0].message.content
            import json
            try:
                questions_data = json.loads(generated_content)
            except json.JSONDecodeError:
                # If the response isn't valid JSON, try to extract it
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', generated_content, re.DOTALL)
                if json_match:
                    questions_data = json.loads(json_match.group(0))
                else:
                    return Response(
                        {"detail": "Failed to parse generated questions."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Create a new blitz quiz
            blitz_quiz = Test.objects.create(
                title=f"Blitz Quiz: {test.title}",
                description=f"Auto-generated blitz quiz based on {test.title}",
                creator=request.user,
                time_limit=600,  # 10 minutes
                shuffle_questions=True,
                shuffle_answers=True,
                mode='blitz'
            )

            # Add the generated questions
            for i, q_data in enumerate(questions_data[:20]):  # Limit to 20 questions
                question = Question.objects.create(
                    test=blitz_quiz,
                    text=q_data['question'],
                    question_type='single',
                    points=1,
                    order=i
                )

                # Add the options
                for j, option_text in enumerate(q_data['options']):
                    is_correct = q_data['correct'] == chr(65 + j)  # Convert A, B, C, D to index
                    Answer.objects.create(
                        question=question,
                        text=option_text,
                        is_correct=is_correct
                    )

            serializer = TestSerializer(blitz_quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"detail": f"Error generating quiz: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own test sessions"""
        return TestSession.objects.filter(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Start a new test session"""
        test_id = request.data.get('test')
        try:
            test = Test.objects.get(pk=test_id)
        except Test.DoesNotExist:
            return Response(
                {"detail": "Test not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if there's already an in-progress session for this test
        existing_session = TestSession.objects.filter(
            user=request.user,
            test=test,
            status='in_progress'
        ).first()

        if existing_session:
            serializer = self.get_serializer(existing_session)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create a new session
        session = TestSession.objects.create(
            user=request.user,
            test=test,
            status='in_progress'
        )

        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_response(self, request, pk=None):
        """Submit a response to a question in the test"""
        session = self.get_object()

        # Check if the session is still in progress
        if session.status != 'in_progress':
            return Response(
                {"detail": "This test session is no longer active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the response
        serializer = UserResponseSerializer(data=request.data)
        if serializer.is_valid():
            # Check if the question belongs to the test
            question_id = serializer.validated_data['question'].id
            if not session.test.questions.filter(id=question_id).exists():
                return Response(
                    {"detail": "This question does not belong to the current test."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if there's already a response for this question
            if UserResponse.objects.filter(session=session, question_id=question_id).exists():
                return Response(
                    {"detail": "You have already answered this question."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save the response
            serializer.save(session=session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete the test session and calculate the score"""
        session = self.get_object()

        # Check if the session is still in progress
        if session.status != 'in_progress':
            return Response(
                {"detail": "This test session is already completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark as completed
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()

        # Calculate the score
        score = session.calculate_score()

        # Update user profile stats
        profile = request.user.profile
        profile.tests_taken += 1
        profile.update_rating()

        return Response({
            "detail": "Test completed successfully.",
            "score": score,
            "total": sum(q.points for q in session.test.questions.all())
        }, status=status.HTTP_200_OK)


class CompetitiveSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CompetitiveSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return all active competitive sessions and ones created by the user"""
        return CompetitiveSession.objects.filter(
            is_active=True
        ) | CompetitiveSession.objects.filter(
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start the competitive session"""
        competitive_session = self.get_object()

        # Check if the user is the creator
        if competitive_session.created_by != request.user:
            return Response(
                {"detail": "Only the creator can start this competitive session."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if it's already started
        if competitive_session.started_at:
            return Response(
                {"detail": "This competitive session has already started."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Start the session
        competitive_session.started_at = timezone.now()
        competitive_session.save()

        return Response({
            "detail": "Competitive session started successfully.",
            "started_at": competitive_session.started_at
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End the competitive session"""
        competitive_session = self.get_object()

        # Check if the user is the creator
        if competitive_session.created_by != request.user:
            return Response(
                {"detail": "Only the creator can end this competitive session."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if it's started
        if not competitive_session.started_at:
            return Response(
                {"detail": "This competitive session has not been started yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if it's already ended
        if competitive_session.ended_at:
            return Response(
                {"detail": "This competitive session has already ended."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # End the session
        competitive_session.ended_at = timezone.now()
        competitive_session.is_active = False
        competitive_session.save()

        return Response({
            "detail": "Competitive session ended successfully.",
            "ended_at": competitive_session.ended_at
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get the leaderboard for this competitive session"""
        competitive_session = self.get_object()

        # Check if the session has started
        if not competitive_session.started_at:
            return Response(
                {"detail": "This competitive session has not started yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the leaderboard
        leaderboard = competitive_session.get_leaderboard()
        serializer = LeaderboardEntrySerializer(leaderboard, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a competitive session by creating a test session"""
        competitive_session = self.get_object()

        # Check if the session is active and has started
        if not competitive_session.is_active or not competitive_session.started_at:
            return Response(
                {"detail": "This competitive session is not active or has not started."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if it has ended
        if competitive_session.ended_at:
            return Response(
                {"detail": "This competitive session has already ended."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a test session for the user
        test_session = TestSession.objects.create(
            user=request.user,
            test=competitive_session.test,
            status='in_progress'
        )

        serializer = TestSessionSerializer(test_session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
