from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Achievement, UserAchievement, FriendRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    friends_count = serializers.SerializerMethodField()
    achievements_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'avatar', 'rating', 'tests_taken',
                  'tests_created', 'friends_count', 'achievements_count']

    def get_friends_count(self, obj):
        return obj.friends.count()

    def get_achievements_count(self, obj):
        return obj.achievements.count()


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'icon']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'earned_at']


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'from_user', 'status', 'created_at', 'updated_at']

    def validate_to_user(self, value):
        request = self.context.get('request')
        if request and request.user:
            # Check if the user is trying to add themselves
            if value == request.user:
                raise serializers.ValidationError("You cannot send a friend request to yourself.")

            # Check if a request already exists
            if FriendRequest.objects.filter(from_user=request.user, to_user=value).exists():
                raise serializers.ValidationError("A friend request to this user already exists.")

            # Check if they're already friends
            if request.user.profile.friends.filter(user=value).exists():
                raise serializers.ValidationError("You are already friends with this user.")

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['from_user'] = request.user
        return super().create(validated_data)


class FriendSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'avatar', 'rating']