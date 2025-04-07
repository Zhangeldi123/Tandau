from rest_framework import serializers
from .models import Test, Question, Answer, TestSession, UserResponse, CompetitiveSession
from django.contrib.auth.models import User


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # Hide correct answers in responses
        }


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'order', 'answers']


class TestSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'creator', 'created_at', 'updated_at',
                  'time_limit', 'shuffle_questions', 'shuffle_answers', 'mode',
                  'is_active', 'questions_count']
        read_only_fields = ['creator', 'created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def create(self, validated_data):
        # Set the creator to the current user
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class TestDetailSerializer(TestSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(TestSerializer.Meta):
        fields = TestSerializer.Meta.fields + ['questions']


class QuestionCreateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order', 'answers']

    def validate_answers(self, answers):
        """Validate that the correct number of answers are marked as correct"""
        question_type = self.initial_data.get('question_type')
        correct_answers = [a for a in answers if a.get('is_correct', False)]

        if question_type == 'single' and len(correct_answers) != 1:
            raise serializers.ValidationError("Single-choice questions must have exactly one correct answer")

        if question_type == 'multiple' and not correct_answers:
            raise serializers.ValidationError("Multiple-choice questions must have at least one correct answer")

        return answers

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question


class UserResponseSerializer(serializers.ModelSerializer):
    selected_answer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = UserResponse
        fields = ['id', 'question', 'selected_answer_ids', 'open_response', 'response_time']
        read_only_fields = ['id']

    def create(self, validated_data):
        selected_answer_ids = validated_data.pop('selected_answer_ids', [])
        response = UserResponse.objects.create(**validated_data)

        if selected_answer_ids:
            answers = Answer.objects.filter(id__in=selected_answer_ids)
            response.selected_answers.set(answers)

        return response


class TestSessionSerializer(serializers.ModelSerializer):
    responses = UserResponseSerializer(many=True, read_only=True)

    class Meta:
        model = TestSession
        fields = ['id', 'test', 'user', 'started_at', 'completed_at', 'status', 'score', 'responses']
        read_only_fields = ['id', 'user', 'started_at', 'completed_at', 'status', 'score']

    def create(self, validated_data):
        # Set the user to the current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CompetitiveSessionSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = CompetitiveSession
        fields = ['id', 'test', 'created_by', 'created_at', 'started_at',
                  'ended_at', 'is_active', 'participants_count']
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_participants_count(self, obj):
        if obj.started_at and obj.ended_at:
            return obj.get_participants().count()
        return 0

    def create(self, validated_data):
        # Set the created_by to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class LeaderboardEntrySerializer(serializers.Serializer):
    user = serializers.StringRelatedField()
    score = serializers.IntegerField()
    completion_time = serializers.FloatField()
    avg_response_time = serializers.FloatField()
