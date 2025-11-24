from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from .models import ChangeRequest, RequestHistory, RequestComment, RequestAttachment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class RequestHistoryInline(admin.TabularInline):
    """Inline history display"""
    model = RequestHistory
    extra = 0
    can_delete = False
    fields = ('timestamp', 'action', 'performed_by', 'field_changed', 'old_value', 'new_value', 'notes')
    readonly_fields = ('timestamp', 'action', 'performed_by', 'field_changed', 'old_value', 'new_value', 'notes')

    def has_add_permission(self, request, obj=None):
        return False


class RequestCommentInline(admin.TabularInline):
    """Inline comments"""
    model = RequestComment
    extra = 1
    fields = ('user', 'comment', 'is_internal', 'created_at')
    readonly_fields = ('created_at',)


class RequestAttachmentInline(admin.TabularInline):
    """Inline attachments"""
    model = RequestAttachment
    extra = 1
    fields = ('file', 'description', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_number',
        'download_pdf_button',
        'title_short',
        'status_badge',
        'priority_badge',
        'from_department',
        'to_department',
        'category',
        'requested_by',
        'assigned_to',
        'submitted_at',
        'days_open'
    )

    list_filter = (
        'status',
        'priority',
        'change_type',
        'category',
        'from_department',
        'to_department',
        'impact_assessment',
        'risk_level',
        'submitted_at',
        'created_at'
    )

    search_fields = (
        'request_number',
        'title',
        'description',
        'reference_number',
        'requested_by__username',
        'requested_by__first_name',
        'requested_by__last_name'
    )

    readonly_fields = (
        'request_number',
        'created_at',
        'last_modified',
        'submitted_at',
        'reviewed_at',
        'approved_at',
        'started_at',
        'completed_at',
        'closed_at',
        'view_full_history'
    )

    fieldsets = (
        ('अनुरोध विवरण (Request Details)', {
            'fields': (
                'request_number',
                'title',
                'description',
                'category',
                'reference_number',
                'attachment',


            )
        }),
        ('विभाग जानकारी (Department Information)', {
            'fields': (

                'to_department',
                'assigned_to',
                'change_type',
                'priority',
            )
        }),
        ('ITIL मूल्यांकन (ITIL Assessment)', {
            'fields': (
                'business_justification',
                'impact_assessment',
                'risk_level',
                'affected_systems',
                'rollback_plan',
            ),
            'classes': ('collapse',)
        }),

        ('अनुपालन (Compliance)', {
            'fields': (
                'data_privacy_confirmed',
                'regulatory_compliance_check',
            )
        }),
        ('कार्य प्रगति (Workflow Progress)', {
            'fields': (
                'status',
                'reviewed_by',
                'approved_by',
                'completed_by',
                'expected_completion_date',
            )
        }),
        ('प्रतिक्रिया र समाधान (Response & Resolution)', {
            'fields': (
                'response_notes',
                'resolution_details',
                'closure_notes',
            ),
            'classes': ('collapse',)
        }),


        ('इतिहास (History)', {
            'fields': ('view_full_history',),
            'classes': ('collapse',)
        }),
    )

    inlines = [RequestCommentInline, RequestAttachmentInline, RequestHistoryInline]

    actions = [
        'action_submit',
        'action_approve',
        'action_reject',
        'action_start_work',
        'action_complete',
        'action_close',
        'action_put_on_hold',
        'action_reopen'
    ]

    def get_queryset(self, request):
        """Filter based on user's department"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # Show requests from user's department or assigned to user's department
        user_dept = getattr(request.user, 'department', None)
        if user_dept:
            return qs.filter(
                Q(from_department=user_dept) |
                Q(to_department=user_dept) |
                Q(assigned_to=request.user)
            )

        return qs.filter(requested_by=request.user)

    def save_model(self, request, obj, form, change):
        """Auto-populate fields and create history"""

        if not change:
            obj.from_department = request.user.department


        if not change:  # New object
            obj.requested_by = request.user
            action = 'CREATED'
            notes = f"अनुरोध सिर्जना गरियो (Request created)"
        else:
            action = 'UPDATED'
            notes = "अनुरोध अद्यावधिक गरियो (Request updated)"

            # Track specific status changes
            if 'status' in form.changed_data:
                old_status = form.initial.get('status')
                new_status = obj.status

                # Update timestamps based on status
                if new_status == 'SUBMITTED' and not obj.submitted_at:
                    obj.submitted_at = timezone.now()
                    action = 'SUBMITTED'
                elif new_status == 'UNDER_REVIEW' and not obj.reviewed_at:
                    obj.reviewed_at = timezone.now()
                    obj.reviewed_by = request.user
                elif new_status == 'APPROVED' and not obj.approved_at:
                    obj.approved_at = timezone.now()
                    obj.approved_by = request.user
                    action = 'APPROVED'
                elif new_status == 'REJECTED':
                    action = 'REJECTED'
                elif new_status == 'IN_PROGRESS' and not obj.started_at:
                    obj.started_at = timezone.now()
                elif new_status == 'COMPLETED' and not obj.completed_at:
                    obj.completed_at = timezone.now()
                    obj.completed_by = request.user
                    action = 'COMPLETED'
                elif new_status == 'CLOSED' and not obj.closed_at:
                    obj.closed_at = timezone.now()
                    action = 'CLOSED'

                notes = f"अवस्था परिवर्तन: {old_status} → {new_status}"

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['category'].required = True
        form.base_fields['reference_number'].required = True
        return form

        # Create history record
        RequestHistory.objects.create(
            request=obj,
            action=action,
            performed_by=request.user,
            notes=notes
        )

        # Track field changes
        if change and form.changed_data:
            for field in form.changed_data:
                if field != 'last_modified':
                    RequestHistory.objects.create(
                        request=obj,
                        action='UPDATED',
                        performed_by=request.user,
                        field_changed=field,
                        old_value=str(form.initial.get(field, '')),
                        new_value=str(form.cleaned_data.get(field, '')),
                        notes=f"क्षेत्र परिवर्तन: {field}"
                    )

    # Custom display methods
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title

    title_short.short_description = 'शीर्षक (Title)'

    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'UNDER_REVIEW': 'purple',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'IN_PROGRESS': 'orange',
            'PENDING_INFO': 'yellow',
            'ON_HOLD': 'brown',
            'COMPLETED': 'darkgreen',
            'CLOSED': 'black',
            'CANCELLED': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'अवस्था (Status)'

    def priority_badge(self, obj):
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )

    priority_badge.short_description = 'प्राथमिकता (Priority)'

    def days_open(self, obj):
        if obj.closed_at:
            delta = obj.closed_at - obj.created_at
        else:
            delta = timezone.now() - obj.created_at

        days = delta.days
        color = 'green' if days < 7 else 'orange' if days < 14 else 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} दिन</span>',
            color,
            days
        )

    days_open.short_description = 'खुला दिन (Days Open)'

    def view_full_history(self, obj):
        if obj.pk:
            history_items = obj.history.all()
            html = '<table style="width: 100%; border-collapse: collapse;">'
            html += '<tr style="background: #f0f0f0;"><th>समय</th><th>कार्य</th><th>गर्ने व्यक्ति</th><th>टिप्पणी</th></tr>'

            for item in history_items:
                html += f'<tr style="border-bottom: 1px solid #ddd;">'
                html += f'<td>{item.timestamp.strftime("%Y-%m-%d %H:%M")}</td>'
                html += f'<td>{item.get_action_display()}</td>'
                html += f'<td>{item.performed_by}</td>'
                html += f'<td>{item.notes}</td>'
                html += '</tr>'

            html += '</table>'
            return mark_safe(html)
        return "सेभ गर्नुहोस् (Save first)"

    view_full_history.short_description = 'पूर्ण इतिहास (Full History)'

    # Custom actions
    def action_submit(self, request, queryset):
        for obj in queryset.filter(status='DRAFT'):
            obj.status = 'SUBMITTED'
            obj.submitted_at = timezone.now()
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='SUBMITTED',
                performed_by=request.user,
                notes='अनुरोध पेश गरियो (Request submitted)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू पेश गरियो")

    action_submit.short_description = "चयनित अनुरोधहरू पेश गर्नुहोस् (Submit selected)"

    def action_approve(self, request, queryset):
        for obj in queryset.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']):
            obj.status = 'APPROVED'
            obj.approved_at = timezone.now()
            obj.approved_by = request.user
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='APPROVED',
                performed_by=request.user,
                notes='अनुरोध स्वीकृत गरियो (Request approved)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू स्वीकृत गरियो")

    action_approve.short_description = "चयनित अनुरोधहरू स्वीकृत गर्नुहोस् (Approve selected)"

    def action_reject(self, request, queryset):
        for obj in queryset.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']):
            obj.status = 'REJECTED'
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='REJECTED',
                performed_by=request.user,
                notes='अनुरोध अस्वीकृत गरियो (Request rejected)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू अस्वीकृत गरियो")

    action_reject.short_description = "चयनित अनुरोधहरू अस्वीकृत गर्नुहोस् (Reject selected)"

    def action_start_work(self, request, queryset):
        for obj in queryset.filter(status='APPROVED'):
            obj.status = 'IN_PROGRESS'
            obj.started_at = timezone.now()
            obj.assigned_to = request.user
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='STATUS_CHANGED',
                performed_by=request.user,
                notes='कार्य सुरु गरियो (Work started)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरूमा कार्य सुरु गरियो")

    action_start_work.short_description = "कार्य सुरु गर्नुहोस् (Start work)"

    def action_complete(self, request, queryset):
        for obj in queryset.filter(status='IN_PROGRESS'):
            obj.status = 'COMPLETED'
            obj.completed_at = timezone.now()
            obj.completed_by = request.user
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='COMPLETED',
                performed_by=request.user,
                notes='अनुरोध सम्पन्न गरियो (Request completed)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू सम्पन्न गरियो")

    action_complete.short_description = "सम्पन्न भयो (Mark as completed)"

    def action_close(self, request, queryset):
        for obj in queryset.filter(status='COMPLETED'):
            obj.status = 'CLOSED'
            obj.closed_at = timezone.now()
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='CLOSED',
                performed_by=request.user,
                notes='अनुरोध बन्द गरियो (Request closed)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू बन्द गरियो")

    action_close.short_description = "बन्द गर्नुहोस् (Close)"

    def action_put_on_hold(self, request, queryset):
        for obj in queryset.exclude(status__in=['CLOSED', 'CANCELLED']):
            obj.status = 'ON_HOLD'
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='STATUS_CHANGED',
                performed_by=request.user,
                notes='अनुरोध रोकियो (Request put on hold)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू रोकियो")

    action_put_on_hold.short_description = "रोक्नुहोस् (Put on hold)"

    def action_reopen(self, request, queryset):
        for obj in queryset.filter(status__in=['CLOSED', 'REJECTED']):
            obj.status = 'SUBMITTED'
            obj.save()

            RequestHistory.objects.create(
                request=obj,
                action='REOPENED',
                performed_by=request.user,
                notes='अनुरोध पुन: खोलियो (Request reopened)'
            )

        self.message_user(request, f"{queryset.count()} अनुरोधहरू पुन: खोलियो")

    action_reopen.short_description = "पुन: खोल्नुहोस् (Reopen)"



    def generate_request_report(self,request_obj):
        """
        Generate a comprehensive PDF report for a request object
        """
        buffer = BytesIO()

        # Create the PDF document (A4 size)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        # Container for the 'Flowable' objects
        elements = []

        # Define styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            borderPadding=5,
            backColor=colors.HexColor('#e8f0f8')
        )

        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            fontName='Helvetica-Bold'
        )

        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica'
        )

        # Helper function to create a field row
        def create_field_table(label, value, col_widths=None):
            if col_widths is None:
                col_widths = [2.5 * inch, 4.5 * inch]

            # Handle None values
            if value is None:
                value = "N/A"

            data = [
                [Paragraph(f"<b>{label}</b>", label_style),
                 Paragraph(str(value), value_style)]
            ]

            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            return table

        # Title
        elements.append(Paragraph("अनुरोध रिपोर्ट / Request Report", title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Generate timestamp
        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"<i>Generated: {generated_time}</i>",
                                  ParagraphStyle('timestamp', parent=styles['Normal'],
                                                 fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)))
        elements.append(Spacer(1, 0.2 * inch))

        # ========== Request Details Section ==========
        elements.append(Paragraph("अनुरोध विवरण (Request Details)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("Request Number:", request_obj.request_number))
        elements.append(create_field_table("Title:", request_obj.title))
        elements.append(create_field_table("Description:", request_obj.description or "N/A"))
        elements.append(create_field_table("Category:", request_obj.get_category_display() if hasattr(request_obj,
                                                                                                      'get_category_display') else request_obj.category))
        elements.append(create_field_table("Reference Number:", request_obj.reference_number or "N/A"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== Department Information Section ==========
        elements.append(Paragraph("विभाग जानकारी (Department Information)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("From Department:",
                                           str(request_obj.from_department) if hasattr(request_obj,
                                                                                       'from_department') else "N/A"))
        elements.append(create_field_table("To Department:",
                                           str(request_obj.to_department) if hasattr(request_obj,
                                                                                     'to_department') else "N/A"))
        elements.append(create_field_table("Assigned To:",
                                           str(request_obj.assigned_to) if request_obj.assigned_to else "Not Assigned"))
        elements.append(create_field_table("Change Type:",
                                           request_obj.get_change_type_display() if hasattr(request_obj,
                                                                                            'get_change_type_display') else str(
                                               request_obj.change_type)))
        elements.append(create_field_table("Priority:",
                                           request_obj.get_priority_display() if hasattr(request_obj,
                                                                                         'get_priority_display') else str(
                                               request_obj.priority)))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== Status and Workflow Section ==========
        elements.append(Paragraph("कार्य प्रगति (Workflow Progress)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("Status:",
                                           request_obj.get_status_display() if hasattr(request_obj,
                                                                                       'get_status_display') else str(
                                               request_obj.status)))
        elements.append(create_field_table("Requested By:", str(request_obj.requested_by)))
        elements.append(create_field_table("Reviewed By:",
                                           str(request_obj.reviewed_by) if request_obj.reviewed_by else "N/A"))
        elements.append(create_field_table("Approved By:",
                                           str(request_obj.approved_by) if request_obj.approved_by else "N/A"))
        elements.append(create_field_table("Completed By:",
                                           str(request_obj.completed_by) if request_obj.completed_by else "N/A"))
        elements.append(create_field_table("Expected Completion Date:",
                                           str(request_obj.expected_completion_date) if request_obj.expected_completion_date else "N/A"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== ITIL Assessment Section ==========
        elements.append(Paragraph("ITIL मूल्यांकन (ITIL Assessment)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("Business Justification:",
                                           request_obj.business_justification or "N/A"))
        elements.append(create_field_table("Impact Assessment:",
                                           request_obj.get_impact_assessment_display() if hasattr(request_obj,
                                                                                                  'get_impact_assessment_display') else str(
                                               request_obj.impact_assessment)))
        elements.append(create_field_table("Risk Level:",
                                           request_obj.get_risk_level_display() if hasattr(request_obj,
                                                                                           'get_risk_level_display') else str(
                                               request_obj.risk_level)))
        elements.append(create_field_table("Affected Systems:",
                                           request_obj.affected_systems or "N/A"))
        elements.append(create_field_table("Rollback Plan:",
                                           request_obj.rollback_plan or "N/A"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== Compliance Section ==========
        elements.append(Paragraph("अनुपालन (Compliance)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("Data Privacy Confirmed:",
                                           "Yes" if request_obj.data_privacy_confirmed else "No"))
        elements.append(create_field_table("Regulatory Compliance Check:",
                                           "Yes" if request_obj.regulatory_compliance_check else "No"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== Response & Resolution Section ==========
        elements.append(Paragraph("प्रतिक्रिया र समाधान (Response & Resolution)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(create_field_table("Response Notes:",
                                           request_obj.response_notes or "N/A"))
        elements.append(create_field_table("Resolution Details:",
                                           request_obj.resolution_details or "N/A"))
        elements.append(create_field_table("Closure Notes:",
                                           request_obj.closure_notes or "N/A"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== Timeline Section ==========
        elements.append(Paragraph("समय विवरण (Timeline)", section_style))
        elements.append(Spacer(1, 0.1 * inch))

        def format_datetime(dt):
            return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"

        elements.append(create_field_table("Created At:", format_datetime(request_obj.created_at)))
        elements.append(create_field_table("Submitted At:", format_datetime(request_obj.submitted_at)))
        elements.append(create_field_table("Reviewed At:", format_datetime(request_obj.reviewed_at)))
        elements.append(create_field_table("Approved At:", format_datetime(request_obj.approved_at)))
        elements.append(create_field_table("Started At:", format_datetime(request_obj.started_at)))
        elements.append(create_field_table("Completed At:", format_datetime(request_obj.completed_at)))
        elements.append(create_field_table("Closed At:", format_datetime(request_obj.closed_at)))
        elements.append(create_field_table("Last Modified:", format_datetime(request_obj.last_modified)))

        # Calculate days open
        if request_obj.closed_at:
            delta = request_obj.closed_at - request_obj.created_at
        else:
            delta = datetime.now().replace(tzinfo=request_obj.created_at.tzinfo) - request_obj.created_at
        days_open = delta.days

        elements.append(create_field_table("Days Open:", f"{days_open} days"))
        elements.append(Spacer(1, 0.15 * inch))

        # ========== History Section (if available) ==========
        if hasattr(request_obj, 'history') and request_obj.history.exists():
            elements.append(PageBreak())
            elements.append(Paragraph("इतिहास (History)", section_style))
            elements.append(Spacer(1, 0.1 * inch))

            history_data = [['समय (Time)', 'कार्य (Action)', 'गर्ने व्यक्ति (Performed By)', 'टिप्पणी (Notes)']]

            for item in request_obj.history.all()[:20]:  # Limit to 20 most recent
                history_data.append([
                    item.timestamp.strftime("%Y-%m-%d %H:%M"),
                    item.get_action_display() if hasattr(item, 'get_action_display') else str(item.action),
                    str(item.performed_by),
                    item.notes[:50] + '...' if len(item.notes) > 50 else item.notes
                ])

            history_table = Table(history_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 2.5 * inch])
            history_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            elements.append(history_table)

        # ========== Footer ==========
        elements.append(Spacer(1, 0.3 * inch))
        footer_style = ParagraphStyle(
            'footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            borderPadding=10,
            borderWidth=1,
            borderColor=colors.grey
        )
        elements.append(Paragraph(
            "This is a system-generated report. For questions, contact your system administrator.",
            footer_style
        ))

        # Build PDF
        doc.build(elements)

        # Get the value of the BytesIO buffer and return it
        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    def download_pdf_button(self, obj):
        if obj.pk:
            url = reverse('admin:download_request_pdf', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" '
               
                'text-decoration: none; border-radius: 4px;">'
                '📄 Download PDF</a>',
                url
            )
        return "-"

    download_pdf_button.short_description = 'रिपोर्ट (Report)'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:request_id>/download-pdf/',
                 self.admin_site.admin_view(self.download_pdf_view),
                 name='download_request_pdf'),
        ]
        return custom_urls + urls

    def download_pdf_view(self, request, request_id):
        request_obj = self.model.objects.get(id=request_id)
        pdf = self.generate_request_report(request_obj)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Request_{request_obj.request_number}_Report.pdf"'

        return response

#@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'performed_by', 'timestamp', 'field_changed')
    list_filter = ('action', 'timestamp', 'performed_by')
    search_fields = ('request__request_number', 'request__title', 'notes')
    readonly_fields = ('request', 'action', 'performed_by', 'timestamp', 'old_value', 'new_value', 'field_changed',
                       'notes')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


#@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ('request', 'user', 'comment_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('request__request_number', 'comment')
    readonly_fields = ('created_at',)

    def comment_preview(self, obj):
        return obj.comment[:100] + '...' if len(obj.comment) > 100 else obj.comment

    comment_preview.short_description = 'टिप्पणी (Comment)'


#@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ('request', 'file', 'description', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('request__request_number', 'description')
    readonly_fields = ('uploaded_at',)