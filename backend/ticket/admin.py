from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django import forms
from django.http import HttpResponseRedirect
from .models import (
    Department, Category, Ticket, TicketDiscussion,
    TicketStatusHistory, ChangeRequestWorkflow, DepartmentTransfer
)


class DepartmentAdminForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    form = DepartmentAdminForm
    list_display = ('name', 'is_branch', 'sla_hours', 'ticket_count', 'active_tickets')
    list_filter = ('is_branch',)
    search_fields = ('name', 'description')
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            ticket_count=Count('tickets'),
            active_tickets_count=Count('tickets',
                                       filter=Q(tickets__current_status__in=['Open', 'In Progress', 'Reopened']))
        )

    def ticket_count(self, obj):
        return obj.ticket_count

    ticket_count.short_description = 'Total Tickets'

    def active_tickets(self, obj):
        return obj.active_tickets_count

    active_tickets.short_description = 'Active Tickets'


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('name', 'category_type', 'is_active', 'ticket_count')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            ticket_count=Count('ticket')
        )

    def ticket_count(self, obj):
        return obj.ticket_count

    ticket_count.short_description = 'Tickets'


class TicketDiscussionForm(forms.ModelForm):
    class Meta:
        model = TicketDiscussion
        fields = ['message', 'message_type', 'is_internal']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your message here...'}),
        }


class TicketDiscussionInline(admin.TabularInline):
    model = TicketDiscussion
    form = TicketDiscussionForm
    fields = ('message', 'message_type', 'is_internal', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')
    extra = 1
    max_num = 10

    def message_preview(self, obj):
        preview = obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
        return format_html('<span title="{}">{}</span>', obj.message, preview)

    message_preview.short_description = 'Message'


class TicketStatusHistoryInline(admin.TabularInline):
    model = TicketStatusHistory
    fields = ('old_status', 'new_status', 'changed_by', 'changed_at', 'notes_preview')
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at', 'notes_preview')
    extra = 0
    max_num = 10

    def notes_preview(self, obj):
        if obj.notes:
            preview = obj.notes[:50] + "..." if len(obj.notes) > 50 else obj.notes
            return format_html('<span title="{}">{}</span>', obj.notes, preview)
        return "-"

    notes_preview.short_description = 'Notes'

    def has_add_permission(self, request, obj=None):
        return False


class DepartmentTransferInline(admin.TabularInline):
    model = DepartmentTransfer
    fields = ('from_department', 'to_department', 'transferred_by', 'transferred_at', 'notes_preview')
    readonly_fields = ('from_department', 'to_department', 'transferred_by', 'transferred_at', 'notes_preview')
    extra = 0
    max_num = 5

    def notes_preview(self, obj):
        if obj.notes:
            preview = obj.notes[:50] + "..." if len(obj.notes) > 50 else obj.notes
            return format_html('<span title="{}">{}</span>', obj.notes, preview)
        return "-"

    notes_preview.short_description = 'Notes'

    def has_add_permission(self, request, obj=None):
        return False


class ChangeRequestWorkflowInline(admin.TabularInline):
    model = ChangeRequestWorkflow
    fields = ('workflow_step', 'assigned_to', 'status', 'due_date', 'completed_at')
    readonly_fields = ('completed_at',)
    extra = 1
    max_num = 10


class TicketAdminForm(forms.ModelForm):
    # Add a field for sending ticket to department (for transfer functionality)
    send_to_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Transfer to Department",
        help_text="Select a department to transfer this ticket to"
    )
    transfer_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Transfer Notes",
        help_text="Reason for transferring this ticket"
    )

    # Add a discussion field for quick replies
    quick_reply = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a quick reply to this ticket...'}),
        required=False,
        label="Quick Reply"
    )
    quick_reply_internal = forms.BooleanField(
        required=False,
        label="Internal Note",
        help_text="Mark this reply as internal (visible only to staff)"
    )

    class Meta:
        model = Ticket
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default values
        self.fields['request_type'].initial = 'General'
        self.fields['urgency_level'].initial = 'Medium'

        # Set the label for department field
        self.fields['department'].label = "Your Department Name"

        # If it's a new ticket, set created_by to current user
        if not self.instance.pk:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # This will be handled in the view

    def clean(self):
        cleaned_data = super().clean()
        send_to_department = cleaned_data.get('send_to_department')
        transfer_notes = cleaned_data.get('transfer_notes')

        # Validate transfer fields
        if send_to_department and not transfer_notes:
            raise forms.ValidationError({
                'transfer_notes': 'Transfer notes are required when transferring a ticket.'
            })

        return cleaned_data


class PriorityFilter(admin.SimpleListFilter):
    title = 'priority'
    parameter_name = 'ticket_priority'

    def lookups(self, request, model_admin):
        return [
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'critical':
            return queryset.filter(ticket_priority='Critical')
        if self.value() == 'high':
            return queryset.filter(ticket_priority='High')
        if self.value() == 'medium':
            return queryset.filter(ticket_priority='Medium')
        if self.value() == 'low':
            return queryset.filter(ticket_priority='Low')
        return queryset


class SLAStatusFilter(admin.SimpleListFilter):
    title = 'SLA status'
    parameter_name = 'sla_status'

    def lookups(self, request, model_admin):
        return [
            ('overdue', 'Overdue'),
            ('due_soon', 'Due Soon (Next 24h)'),
            ('on_track', 'On Track'),
            ('no_sla', 'No SLA Set'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'overdue':
            return queryset.filter(sla_due_date__lt=now)
        if self.value() == 'due_soon':
            tomorrow = now + timezone.timedelta(hours=24)
            return queryset.filter(sla_due_date__gte=now, sla_due_date__lte=tomorrow)
        if self.value() == 'on_track':
            return queryset.filter(sla_due_date__gt=now + timezone.timedelta(hours=24))
        if self.value() == 'no_sla':
            return queryset.filter(sla_due_date__isnull=True)
        return queryset


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = (
        'ticket_number', 'title_preview', 'department', 'current_status',
        'priority_display', 'assigned_to', 'created_at', 'sla_due_date',
        'sla_status', 'action_buttons'
    )

    list_filter = (
        'department', 'current_status', PriorityFilter, SLAStatusFilter,
        'issue_type', 'request_type', 'urgency_level', 'created_at'
    )

    search_fields = (
        'ticket_number', 'title', 'description', 'identifier',
        'created_by__username', 'assigned_to__username'
    )

    readonly_fields = (
        'ticket_number', 'created_at', 'updated_at', 'closed_at',
        'originating_department', 'transferred_from', 'sla_breached'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'ticket_number', 'title', 'description', 'identifier',
            )
        }),
        ('Classification & Priority', {
            'fields': (
                'ticket_priority', 'department', 'current_status',
                'request_type', 'category', 'issue_type', 'urgency_level'
            )
        }),
        ('Assignment and Workflow', {
            'fields': (
                'assigned_to', 'estimated_effort_hours', 'business_impact'
            )
        }),
        ('SLA Management', {
            'fields': (
                'sla_due_date', 'sla_breached', 'closed_at'
            )
        }),
        ('Department Transfer', {
            'fields': (
                'send_to_department', 'transfer_notes',
                'originating_department', 'transferred_from'
            )
        }),
        ('Memo', {
            'fields': (
                'memo_required', 'memo'
            )
        }),
        ('Quick Reply', {
            'fields': (
                'quick_reply', 'quick_reply_internal'
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        TicketDiscussionInline,
        TicketStatusHistoryInline,
        DepartmentTransferInline,
        ChangeRequestWorkflowInline,
    ]

    list_per_page = 50
    list_select_related = ('department', 'assigned_to', 'created_by')
    date_hierarchy = 'created_at'
    actions = ['transfer_tickets', 'assign_tickets', 'close_tickets', 'reopen_tickets']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'department', 'assigned_to', 'created_by', 'category'
        ).prefetch_related('discussions', 'status_history', 'transfers')

    def get_form(self, request, obj=None, **kwargs):
        """
        Override to pass the request object to the form for current user context
        """
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    def save_model(self, request, obj, form, change):
        # Set created_by to current user for new tickets
        if not change:
            obj.created_by = request.user

        # Handle quick reply
        quick_reply = form.cleaned_data.get('quick_reply')
        if quick_reply:
            TicketDiscussion.objects.create(
                ticket=obj,
                message=quick_reply,
                message_type='text',
                created_by=request.user,
                is_internal=form.cleaned_data.get('quick_reply_internal', False)
            )

        # Handle department transfer
        send_to_department = form.cleaned_data.get('send_to_department')
        transfer_notes = form.cleaned_data.get('transfer_notes')

        if send_to_department and send_to_department != obj.department:
            # Perform the transfer
            obj.transfer_to_department(send_to_department, transfer_notes, request.user)

        # Track status changes
        if change and 'current_status' in form.changed_data:
            original_status = Ticket.objects.get(pk=obj.pk).current_status
            if original_status != obj.current_status:
                TicketStatusHistory.objects.create(
                    ticket=obj,
                    old_status=original_status,
                    new_status=obj.current_status,
                    changed_by=request.user,
                    notes=f"Status changed via admin"
                )

        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        """
        Set initial data for new ticket form
        """
        initial = super().get_changeform_initial_data(request)
        initial['request_type'] = 'General'
        initial['urgency_level'] = 'Medium'
        initial['created_by'] = request.user
        return initial

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Customize the change form rendering
        """
        if add and not obj:
            # For new tickets, set the current user as created_by
            context['adminform'].form.fields['created_by'].initial = request.user

            # Try to set user's department as default if available
            if hasattr(request.user, 'department'):
                context['adminform'].form.fields['department'].initial = request.user.department

        return super().render_change_form(request, context, add, change, form_url, obj)

    def title_preview(self, obj):
        preview = obj.title[:60] + "..." if len(obj.title) > 60 else obj.title
        return format_html('<span title="{}">{}</span>', obj.title, preview)

    title_preview.short_description = 'Title'

    def priority_display(self, obj):
        priority_colors = {
            'Critical': 'red',
            'High': 'orange',
            'Medium': 'blue',
            'Low': 'green'
        }
        color = priority_colors.get(obj.ticket_priority, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.ticket_priority
        )

    priority_display.short_description = 'Priority'

    def sla_status(self, obj):
        if not obj.sla_due_date:
            return format_html('<span style="color: gray;">No SLA</span>')

        now = timezone.now()
        if obj.sla_due_date < now:
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        elif (obj.sla_due_date - now).total_seconds() < 24 * 3600:  # Less than 24 hours
            return format_html('<span style="color: orange; font-weight: bold;">DUE SOON</span>')
        else:
            return format_html('<span style="color: green;">ON TRACK</span>')

    sla_status.short_description = 'SLA Status'

    def action_buttons(self, obj):
        buttons = []
        if obj.current_status != 'Closed':
            close_url = reverse('admin:tickets_ticket_close', args=[obj.pk])
            buttons.append(
                f'<a href="{close_url}" class="button" style="background-color: #dc3545; color: white; padding: 2px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Close</a>'
            )

        if obj.current_status in ['Closed', 'Resolved']:
            reopen_url = reverse('admin:tickets_ticket_reopen', args=[obj.pk])
            buttons.append(
                f'<a href="{reopen_url}" class="button" style="background-color: #28a745; color: white; padding: 2px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Reopen</a>'
            )

        transfer_url = reverse('admin:tickets_ticket_transfer', args=[obj.pk])
        buttons.append(
            f'<a href="{transfer_url}" class="button" style="background-color: #17a2b8; color: white; padding: 2px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Transfer</a>'
        )

        return format_html(' '.join(buttons))

    action_buttons.short_description = 'Actions'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:pk>/close/', self.admin_site.admin_view(self.close_ticket), name='tickets_ticket_close'),
            path('<uuid:pk>/reopen/', self.admin_site.admin_view(self.reopen_ticket), name='tickets_ticket_reopen'),
            path('<uuid:pk>/transfer/', self.admin_site.admin_view(self.transfer_ticket),
                 name='tickets_ticket_transfer'),
        ]
        return custom_urls + urls

    def close_ticket(self, request, pk):
        from django.shortcuts import redirect
        ticket = Ticket.objects.get(pk=pk)
        ticket.current_status = 'Closed'
        ticket.closed_at = timezone.now()
        ticket.save()

        TicketStatusHistory.objects.create(
            ticket=ticket,
            old_status=ticket.current_status,
            new_status='Closed',
            changed_by=request.user,
            notes="Ticket closed via admin"
        )

        self.message_user(request, f"Ticket {ticket.ticket_number} has been closed.")
        return redirect(reverse('admin:tickets_ticket_changelist'))

    def reopen_ticket(self, request, pk):
        from django.shortcuts import redirect
        ticket = Ticket.objects.get(pk=pk)
        ticket.current_status = 'Reopened'
        ticket.closed_at = None
        ticket.save()

        TicketStatusHistory.objects.create(
            ticket=ticket,
            old_status='Closed',
            new_status='Reopened',
            changed_by=request.user,
            notes="Ticket reopened via admin"
        )

        self.message_user(request, f"Ticket {ticket.ticket_number} has been reopened.")
        return redirect(reverse('admin:tickets_ticket_changelist'))

    def transfer_ticket(self, request, pk):
        from django.shortcuts import render, redirect
        ticket = Ticket.objects.get(pk=pk)

        if request.method == 'POST':
            form = TicketTransferForm(request.POST)
            if form.is_valid():
                new_department = form.cleaned_data['department']
                transfer_notes = form.cleaned_data['notes']

                ticket.transfer_to_department(new_department, transfer_notes, request.user)

                self.message_user(
                    request,
                    f"Ticket {ticket.ticket_number} transferred to {new_department.name}."
                )
                return redirect(reverse('admin:tickets_ticket_changelist'))
        else:
            form = TicketTransferForm()

        context = {
            'title': f'Transfer Ticket {ticket.ticket_number}',
            'form': form,
            'ticket': ticket,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tickets/ticket_transfer.html', context)

    # Bulk actions
    def transfer_tickets(self, request, queryset):
        from django.shortcuts import render
        if 'apply' in request.POST:
            form = TicketTransferForm(request.POST)
            if form.is_valid():
                department = form.cleaned_data['department']
                notes = form.cleaned_data['notes']

                for ticket in queryset:
                    ticket.transfer_to_department(department, notes, request.user)

                self.message_user(
                    request,
                    f"Successfully transferred {queryset.count()} tickets to {department.name}."
                )
                return redirect(reverse('admin:tickets_ticket_changelist'))

        form = TicketTransferForm()
        context = {
            'title': 'Transfer Selected Tickets',
            'tickets': queryset,
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tickets/bulk_transfer.html', context)

    transfer_tickets.short_description = "Transfer selected tickets to another department"

    def assign_tickets(self, request, queryset):
        # Implementation for bulk assignment
        pass

    def close_tickets(self, request, queryset):
        updated = queryset.update(current_status='Closed', closed_at=timezone.now())
        self.message_user(request, f"Successfully closed {updated} tickets.")

    def reopen_tickets(self, request, queryset):
        updated = queryset.update(current_status='Reopened', closed_at=None)
        self.message_user(request, f"Successfully reopened {updated} tickets.")


class TicketTransferForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)


@admin.register(TicketDiscussion)
class TicketDiscussionAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'message_preview', 'message_type', 'created_by', 'created_at', 'is_internal')
    list_filter = ('message_type', 'is_internal', 'created_at')
    search_fields = ('message', 'ticket__ticket_number', 'created_by__username')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    list_per_page = 20

    def message_preview(self, obj):
        preview = obj.message[:80] + "..." if len(obj.message) > 80 else obj.message
        return format_html('<span title="{}">{}</span>', obj.message, preview)

    message_preview.short_description = 'Message'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TicketStatusHistory)
class TicketStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('old_status', 'new_status', 'changed_at')
    search_fields = ('ticket__ticket_number', 'changed_by__username')
    readonly_fields = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at', 'notes')
    list_per_page = 20

    def has_add_permission(self, request):
        return False


@admin.register(ChangeRequestWorkflow)
class ChangeRequestWorkflowAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'workflow_step', 'assigned_to', 'status', 'due_date', 'completed_at')
    list_filter = ('status', 'due_date')
    search_fields = ('ticket__ticket_number', 'workflow_step', 'assigned_to__username')
    list_editable = ('status',)
    list_per_page = 20


@admin.register(DepartmentTransfer)
class DepartmentTransferAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'from_department', 'to_department', 'transferred_by', 'transferred_at')
    list_filter = ('from_department', 'to_department', 'transferred_at')
    search_fields = ('ticket__ticket_number', 'transferred_by__username')
    readonly_fields = ('ticket', 'from_department', 'to_department', 'transferred_by', 'transferred_at')
    list_per_page = 20

    def has_add_permission(self, request):
        return False