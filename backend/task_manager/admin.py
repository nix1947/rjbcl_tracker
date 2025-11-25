from django.conf import settings
from django.contrib import admin
from .models import Task, TaskDiscussion
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskDiscussionInline(admin.TabularInline):
    model = TaskDiscussion
    extra = 1
    readonly_fields = ('user', 'created_at')

    # Exclude user from the form since we'll set it automatically
    exclude = ('user',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Only show title and description in the form
    fields = ('title', 'deadline', 'status', 'description', 'assigned_to', 'document')

    list_filter = ('status', 'deadline', 'department', 'assigned_to')

    # Inline comments
    inlines = [TaskDiscussionInline]

    list_display = ('title', 'department', 'status', 'created_by', 'assigned_users')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser or getattr(request.user, 'is_it_dept', False) or getattr(request.user, 'is_global',
                                                                                              False):
            return qs

        if hasattr(request.user, 'department'):
            return qs.filter(department=request.user.department)

        return qs.none()

    def save_model(self, request, obj, form, change):
        # Set the creator on first save
        if not obj.pk:
            obj.created_by = request.user

            # Auto-assign department from logged-in user
            if hasattr(request.user, "department"):
                obj.department = request.user.department

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Automatically set the user for TaskDiscussion inline entries
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TaskDiscussion) and not instance.pk:
                instance.user = request.user
            instance.save()
        formset.save_m2m()

    def has_delete_permission(self, request, obj=None):
        """
        Only allow deletion if the current user is the owner.
        """
        if obj is None:
            # This is for the list view (bulk delete)
            return True
        return obj.created_by == request.user

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Limit assigned_to choices to users from current user's department
        """
        if db_field.name == 'assigned_to':
            if hasattr(request.user, 'department'):
                kwargs['queryset'] = User.objects.filter(department=request.user.department)
            else:
                kwargs['queryset'] = User.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def assigned_users(self, obj):
        # Show all assigned users as comma-separated string
        return ", ".join([user.username for user in obj.assigned_to.all()])

    assigned_users.short_description = 'Assigned Users'