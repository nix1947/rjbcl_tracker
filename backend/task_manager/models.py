from django.db import models
from tinymce.models import HTMLField

from rjbcl.common_data import default_deadline
from rjbcl.validators import file_size

from ticket.models import Department
from django.conf import  settings

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField(help_text="Task title or To Do title",  max_length=255)
    deadline = models.DateField(help_text="Time to complete the task", default=default_deadline)

    # Rich text description
    description = HTMLField(help_text="Task Description", blank=True, null=True)

    document = models.FileField(
        upload_to="task_manager/document",
        blank=True,
        validators=[file_size],
        null=True,
        help_text="Task Details document pdf or word max 5 MB"
    )

    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TaskDiscussion(models.Model):
    """
    Threaded / Nested comments for discussion.
    Only task owner can delete these.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Rich text comment
    comment = HTMLField()


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.task}"
