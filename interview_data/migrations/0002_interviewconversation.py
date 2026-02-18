# Generated migration for InterviewConversation model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interview_data', '0001_initial'),
        ('interviews', '0002_alter_interview_created_by_alter_interview_recruiter'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterviewConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speaker', models.CharField(choices=[('ai', 'AI Interviewer'), ('candidate', 'Candidate')], max_length=20)),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('interview', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='interviews.interview')),
            ],
            options={
                'db_table': 'interview_conversations',
                'ordering': ['timestamp'],
            },
        ),
    ]
