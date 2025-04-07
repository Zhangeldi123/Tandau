from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Achievement, UserAchievement, FriendRequest


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fk_name = 'user'


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    readonly_fields = ('earned_at',)


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rating', 'get_tests_taken')

    def get_rating(self, obj):
        return obj.profile.rating

    get_rating.short_description = 'Rating'

    def get_tests_taken(self, obj):
        return obj.profile.tests_taken

    get_tests_taken.short_description = 'Tests Taken'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'tests_taken', 'tests_created', 'friend_count')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'friends')
    inlines = [UserAchievementInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'bio', 'avatar')
        }),
        ('Statistics', {
            'fields': ('rating', 'tests_taken', 'tests_created')
        }),
        ('Friends', {
            'fields': ('friends',),
            'classes': ('collapse',)
        }),
    )

    def friend_count(self, obj):
        return obj.friends.count()

    friend_count.short_description = 'Friends'

    def has_add_permission(self, request):
        return False


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon', 'user_count')
    search_fields = ('name', 'description')

    def user_count(self, obj):
        return UserAchievement.objects.filter(achievement=obj).count()

    user_count.short_description = 'Users'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'earned_at')
    list_filter = ('achievement', 'earned_at')
    search_fields = ('user__user__username', 'achievement__name')
    readonly_fields = ('earned_at',)


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    readonly_fields = ('created_at', 'updated_at')

    actions = ['accept_requests', 'reject_requests']

    def accept_requests(self, request, queryset):
        count = 0
        for friend_request in queryset.filter(status='pending'):
            if friend_request.accept():
                count += 1
        self.message_user(request, f"{count} friend requests were accepted successfully.")

    accept_requests.short_description = "Accept selected friend requests"

    def reject_requests(self, request, queryset):
        count = 0
        for friend_request in queryset.filter(status='pending'):
            if friend_request.reject():
                count += 1
        self.message_user(request, f"{count} friend requests were rejected successfully.")

    reject_requests.short_description = "Reject selected friend requests"
