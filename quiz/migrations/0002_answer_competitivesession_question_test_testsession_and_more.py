# Generated by Django 5.2 on 2025-04-07 07:18

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('is_correct', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CompetitiveSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_competitions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('question_type', models.CharField(choices=[('single', 'Single Correct Answer'), ('multiple', 'Multiple Correct Answers'), ('open', 'Open-Ended Question')], max_length=20)),
                ('points', models.IntegerField(default=1)),
                ('order', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('time_limit', models.IntegerField(blank=True, help_text='Time limit in seconds', null=True)),
                ('shuffle_questions', models.BooleanField(default=False)),
                ('shuffle_answers', models.BooleanField(default=False)),
                ('mode', models.CharField(choices=[('normal', 'Normal'), ('competitive', 'Competitive'), ('blitz', 'Blitz Quiz')], default='normal', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_tests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TestSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('expired', 'Expired')], default='in_progress', max_length=20)),
                ('score', models.IntegerField(blank=True, null=True)),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='quiz.test')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('open_response', models.TextField(blank=True, null=True)),
                ('response_time', models.FloatField(blank=True, help_text='Time taken to answer in seconds', null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='choices',
            name='question',
        ),
        migrations.RemoveField(
            model_name='usersolutions',
            name='selected_answer',
        ),
        migrations.RemoveField(
            model_name='questions',
            name='category',
        ),
        migrations.RemoveField(
            model_name='usersolutions',
            name='question',
        ),
        migrations.DeleteModel(
            name='Users',
        ),
        migrations.RemoveField(
            model_name='usersolutions',
            name='user',
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='quiz.question'),
        ),
        migrations.AddField(
            model_name='question',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quiz.test'),
        ),
        migrations.AddField(
            model_name='competitivesession',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competitive_sessions', to='quiz.test'),
        ),
        migrations.AddField(
            model_name='userresponse',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.question'),
        ),
        migrations.AddField(
            model_name='userresponse',
            name='selected_answers',
            field=models.ManyToManyField(blank=True, to='quiz.answer'),
        ),
        migrations.AddField(
            model_name='userresponse',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='quiz.testsession'),
        ),
        migrations.DeleteModel(
            name='Choices',
        ),
        migrations.DeleteModel(
            name='Question_Category',
        ),
        migrations.DeleteModel(
            name='Questions',
        ),
        migrations.DeleteModel(
            name='UserSolutions',
        ),
    ]
