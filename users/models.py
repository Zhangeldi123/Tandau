from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    rating = models.IntegerField(default=0)
    tests_taken = models.IntegerField(default=0)
    tests_created = models.IntegerField(default=0)
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)

    def __str__(self):
        return self.user.username

    def update_rating(self):
        """Update user rating based on test performance"""
        from quiz.models import TestSession

        # Get all completed test sessions
        sessions = TestSession.objects.filter(user=self.user, status='completed')

        if sessions.count() > 0:
            # Calculate average score percentage
            total_score = 0
            total_possible = 0

            for session in sessions:
                score = session.calculate_score()
                total_score += score
                total_possible += sum(q.points for q in session.test.questions.all())

            if total_possible > 0:
                # Rating is percentage of correct answers * 10
                self.rating = int((total_score / total_possible) * 1000)
                self.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    instance.profile.save()


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievements/', blank=True, null=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.user.username} - {self.achievement.name}"


class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def accept(self):
        """Accept the friend request and add both users as friends"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.save()

            # Add both users as friends
            from_profile = self.from_user.profile
            to_profile = self.to_user.profile

            from_profile.friends.add(to_profile)

            return True
        return False

    def reject(self):
        """Reject the friend request"""
        if self.status == 'pending':
            self.status = 'rejected'
            self.save()
            return True
        return False
