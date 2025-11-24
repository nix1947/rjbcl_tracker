from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import MemoRecord


@admin.register(MemoRecord)
class MemoRecordAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date_of_record',
        'memo_document_link',
        'memo_type',
        'created_department',
        'related_department',
        'is_final',
    )

    list_filter = (
        'memo_type',
        'fy_title',
        'created_department',
        'related_department',
    )

    search_fields = ('title', 'description', 'related_department', 'created_department', 'is_final')
    readonly_fields = ('created_by',)

    fieldsets = (
        ('मेमोको प्रकार र मिति (Memo Type & Date)', {
            'fields': ('memo_type', 'fy_title', 'date_of_record'),
        }),
        ('मेमो विवरण (Memo Details)', {
            'fields': ('title', 'description', 'memo_document', 'is_final'),
        }),
        ('सम्बन्धित विभाग लाई पठाउने (Related Department)', {
            'fields': ('related_department',),
        }),

    )

    def has_change_permission(self, request, obj=None):
        """Allow editing only for creator, IT dept, or global users"""


        if not obj:
            return super().has_change_permission(request, obj)

        # Superuser/global permission
        if request.user.is_superuser:
            return True

        # Check if user is creator
        if obj.created_by == request.user:
            return True

        # Check if user is IT department
        try:
            if hasattr(request.user, 'is_it_dept') and request.user.is_it_dept:
                return True
        except AttributeError:
            pass

        # Check if user has global permission flag
        try:
            if hasattr(request.user, 'is_global') and request.user.is_global:
                return True
        except AttributeError:
            pass

        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for creator, IT dept, or global users"""
        if not obj:
            return super().has_delete_permission(request, obj)

        # Superuser/global permission
        if request.user.is_superuser:
            return True

        # Check if user is creator
        if obj.created_by == request.user:
            return True

        # Check if user is IT department
        try:
            if hasattr(request.user, 'is_it_dept') and request.user.is_it_dept:
                return True
        except AttributeError:
            pass

        # Check if user has global permission flag
        try:
            if hasattr(request.user, 'is_global') and request.user.is_global:
                return True
        except AttributeError:
            pass

        return False

    def get_readonly_fields(self, request, obj=None):
        """Lock all fields if is_final is True (except for superusers)"""
        fields = super().get_readonly_fields(request, obj)

        if obj and obj.is_final and not request.user.is_superuser:
            return [f.name for f in self.model._meta.fields] + ['memo_document_link']

        return fields

    def save_model(self, request, obj, form, change):
        """Set created_by and lock created_department on creation"""
        if not obj.pk:
            obj.created_by = request.user

            try:
                obj.created_department = request.user.department
            except AttributeError:
                pass

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filter to show memos where user's department is creator OR related"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        try:
            user_department = request.user.department
            return qs.filter(
                Q(created_department=user_department) |
                Q(related_department=user_department)
            ).distinct()
        except AttributeError:
            return qs.none()

    def memo_document_link(self, obj):
        """Display clickable download link for memo document"""
        if obj.memo_document:
            return format_html(
                '<a href="{}" target="_blank">Download File</a>',
                obj.memo_document.url
            )
        return "N/A"

    memo_document_link.short_description = "फाइल"