from django.contrib import admin
from .models import Test, Question, Answer, TestSession, UserResponse, CompetitiveSession


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('text', 'is_correct')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ('text', 'question_type', 'points', 'order')
    classes = ['collapse']


class UserResponseInline(admin.TabularInline):
    model = UserResponse
    extra = 0
    readonly_fields = ('question', 'open_response', 'response_time', 'get_selected_answers')
    fields = ('question', 'open_response', 'response_time', 'get_selected_answers')
    can_delete = False

    def get_selected_answers(self, obj):
        return ", ".join([answer.text for answer in obj.selected_answers.all()])

    get_selected_answers.short_description = 'Selected Answers'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'mode', 'time_limit', 'created_at', 'is_active', 'question_count')
    list_filter = ('mode', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'creator__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'creator')
        }),
        ('Settings', {
            'fields': ('time_limit', 'shuffle_questions', 'shuffle_answers', 'mode', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()

    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'test', 'question_type', 'points', 'order', 'answer_count')
    list_filter = ('question_type', 'test')
    search_fields = ('text', 'test__title')
    inlines = [AnswerInline]

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Question'

    def answer_count(self, obj):
        return obj.answers.count()

    answer_count.short_description = 'Answers'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question_preview', 'is_correct')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('text', 'question__text')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Answer'

    def question_preview(self, obj):
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text

    question_preview.short_description = 'Question'


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'user', 'started_at', 'completed_at', 'status', 'score')
    list_filter = ('status', 'started_at')
    search_fields = ('test__title', 'user__username')
    readonly_fields = ('started_at', 'score')
    inlines = [UserResponseInline]

    fieldsets = (
        (None, {
            'fields': ('test', 'user', 'status', 'score')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_user', 'question_preview', 'response_time', 'is_correct_display')
    list_filter = ('session__status', 'session__test')
    search_fields = ('session__user__username', 'question__text')
    readonly_fields = ('session', 'question', 'selected_answers', 'open_response', 'response_time')

    def session_user(self, obj):
        return obj.session.user.username

    session_user.short_description = 'User'

    def question_preview(self, obj):
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text

    question_preview.short_description = 'Question'

    def is_correct_display(self, obj):
        result = obj.is_correct()
        if result is None:
            return 'Needs Review'
        return 'Correct' if result else 'Incorrect'

    is_correct_display.short_description = 'Correct?'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CompetitiveSession)
class CompetitiveSessionAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'test', 'created_by', 'created_at', 'started_at', 'ended_at', 'is_active', 'participant_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('test__title', 'created_by__username')
    readonly_fields = ('created_at', 'participant_count')

    fieldsets = (
        (None, {
            'fields': ('test', 'created_by', 'is_active')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'ended_at')
        }),
    )

    def participant_count(self, obj):
        if obj.started_at and obj.ended_at:
            return obj.get_participants().count()
        return 0

    participant_count.short_description = 'Participants'

