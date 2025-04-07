from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken


from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import UserProfile, Achievement, UserAchievement, FriendRequest
from .serializers import (
    UserSerializer, UserProfileSerializer, AchievementSerializer,
    UserAchievementSerializer, FriendRequestSerializer, FriendSerializer,
    SignupSerializer  # We'll create this serializer
)
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Register a new user",
    description="Creates a new user account with the provided information and returns an authentication token.",
    request=SignupSerializer,
    responses={201: UserProfileSerializer},  # or a custom response serializer
    tags=["auth"]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        # Get user profile data
        profile_serializer = UserProfileSerializer(user.profile)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'profile': profile_serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get authentication token",
    description="Returns an authentication token for the provided username and password.",
    tags=["auth"]
)
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Get user profile data
        profile_serializer = UserProfileSerializer(user.profile)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'profile': profile_serializer.data
        })


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Get user profile data
        profile_serializer = UserProfileSerializer(user.profile)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'profile': profile_serializer.data
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Allow searching for users"""
        queryset = User.objects.all()
        search = self.request.query_params.get('search')

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's data"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Allow users to see all profiles but only edit their own"""
        return UserProfile.objects.all()

    def get_permissions(self):
        """Only allow users to update their own profile"""
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        """Only allow users to update their own profile"""
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile"""
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def achievements(self, request, pk=None):
        """Get a user's achievements"""
        profile = self.get_object()
        achievements = UserAchievement.objects.filter(user=profile)
        serializer = UserAchievementSerializer(achievements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def friends(self, request, pk=None):
        """Get a user's friends"""
        profile = self.get_object()
        serializer = FriendSerializer(profile.friends.all(), many=True)
        return Response(serializer.data)


class FriendRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get friend requests for the current user"""
        return FriendRequest.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a friend request"""
        friend_request = self.get_object()

        # Check if the user is the recipient
        if friend_request.to_user != request.user:
            return Response(
                {"detail": "You cannot accept this friend request."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Accept the request
        if friend_request.accept():
            return Response(
                {"detail": "Friend request accepted successfully."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"detail": "This friend request cannot be accepted."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a friend request"""
        friend_request = self.get_object()

        # Check if the user is the recipient
        if friend_request.to_user != request.user:
            return Response(
                {"detail": "You cannot reject this friend request."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Reject the request
        if friend_request.reject():
            return Response(
                {"detail": "Friend request rejected successfully."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"detail": "This friend request cannot be rejected."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def received(self, request):
        """Get friend requests received by the current user"""
        requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get friend requests sent by the current user"""
        requests = FriendRequest.objects.filter(from_user=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
