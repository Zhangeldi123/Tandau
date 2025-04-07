from django.db import models
from django.contrib.auth.models import User
import uuid
import random


class Test(models.Model):
    MODES = (
        ('normal', 'Normal'),
        ('competitive', 'Competitive'),
        ('blitz', 'Blitz Quiz'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in seconds")
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=False)
    mode = models.CharField(max_length=20, choices=MODES, default='normal')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_shuffled_questions(self):
        questions = list(self.questions.all())
        if self.shuffle_questions:
            random.shuffle(questions)
        return questions

    def create_variant(self):
        """Create a new variant of this test with rearranged questions"""
        new_test = Test.objects.create(
            title=f"{self.title} (Variant)",
            description=self.description,
            creator=self.creator,
            time_limit=self.time_limit,
            shuffle_questions=True,
            shuffle_answers=True,
            mode=self.mode
        )

        # Copy all questions and answers
        for question in self.questions.all():
            new_question = Question.objects.create(
                test=new_test,
                text=question.text,
                question_type=question.question_type,
                points=question.points
            )

            for answer in question.answers.all():
                Answer.objects.create(
                    question=new_question,
                    text=answer.text,
                    is_correct=answer.is_correct
                )

        return new_test


class Question(models.Model):
    QUESTION_TYPES = (
        ('single', 'Single Correct Answer'),
        ('multiple', 'Multiple Correct Answers'),
        ('open', 'Open-Ended Question'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.text[:50]}..."

    def get_shuffled_answers(self):
        answers = list(self.answers.all())
        if self.test.shuffle_answers:
            random.shuffle(answers)
        return answers


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text[:50]}..."


class TestSession(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"

    def calculate_score(self):
        """Calculate the score based on the answers provided"""
        total_points = sum(q.points for q in self.test.questions.all())
        earned_points = 0

        for response in self.responses.all():
            if response.is_correct():
                earned_points += response.question.points

        self.score = earned_points
        self.save()
        return self.score


class UserResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    open_response = models.TextField(blank=True, null=True)
    response_time = models.FloatField(help_text="Time taken to answer in seconds", null=True, blank=True)

    def __str__(self):
        return f"Response to {self.question.text[:30]}..."

    def is_correct(self):
        """Check if the response is correct based on question type"""
        if self.question.question_type == 'open':
            # For open-ended questions, we'll need manual grading or AI evaluation
            return None

        elif self.question.question_type == 'single':
            # For single correct answer questions
            correct_answer = self.question.answers.filter(is_correct=True).first()
            selected = self.selected_answers.first()
            return selected == correct_answer

        elif self.question.question_type == 'multiple':
            # For multiple correct answers questions
            correct_answers = set(self.question.answers.filter(is_correct=True))
            selected_answers = set(self.selected_answers.all())
            return correct_answers == selected_answers


class CompetitiveSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='competitive_sessions')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_competitions')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Competition: {self.test.title}"

    def get_participants(self):
        return User.objects.filter(test_sessions__test=self.test,
                                   test_sessions__started_at__gte=self.started_at,
                                   test_sessions__started_at__lte=self.ended_at)

    def get_leaderboard(self):
        """Get the leaderboard for this competitive session"""
        sessions = TestSession.objects.filter(
            test=self.test,
            started_at__gte=self.started_at,
            started_at__lte=self.ended_at,
            status='completed'
        ).select_related('user')

        leaderboard = []
        for session in sessions:
            # Calculate average response time
            avg_time = session.responses.aggregate(models.Avg('response_time'))['response_time__avg'] or 0

            leaderboard.append({
                'user': session.user,
                'score': session.score,
                'completion_time': (session.completed_at - session.started_at).total_seconds(),
                'avg_response_time': avg_time
            })

        # Sort by score (descending) and then by completion time (ascending)
        return sorted(leaderboard, key=lambda x: (-x['score'], x['completion_time']))
