import pandas as pd
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.urls import path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import textwrap

from .forms import UploadExcelForm
from .models import MenuItem, UserRequest


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_menu']
    list_filter = ['parent_menu']
    search_fields = ['name', 'parent_menu']

    def has_delete_permission(self, request, obj=None):
        return False


class UserRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_name', 'requested_by', 'department',
        'pdf_download_button', 'approval_form',
        'designation', 'request_type', 'status', 'request_date',

    ]

    list_filter = [
        'status', 'request_type', 'department', 'request_date', 'requested_by'
    ]

    search_fields = [
        'request_id', 'first_name', 'last_name', 'email',
        'requested_by__username'
    ]

    readonly_fields = [
        'request_id', 'request_date', 'requested_by'
    ]

    fieldsets = (
        ('Request Information', {
            'fields': (
                'request_id', 'request_date', 'requested_by',
                'department', 'request_type', 'status'
            )
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'gender',
                'email', 'phone_no', 'mobile_no', 'ssn', 'nationality'
            )
        }),

        ('System Access Permissions', {
            'fields': (
                'allow_approve_transaction', 'allow_back_date',
                'is_regional_head', 'is_branch_manager',
                'allow_advance_payment', 'is_me_user'
            )
        }),
        ('Request Details', {
            'fields': (
                'description', 'permissions_requested'
            )
        }),
        ('Memo Information', {
            'fields': (
                'memo_reference_no', 'memo_date', 'memo_subject',
                'approval_form'
            )
        }),
        ('Approval Information', {
            'fields': (
                'approved_by', 'approval_date', 'remarks'
            )
        }),

        ('Document Information', {
            'fields': (
                'document_type', 'citizen_no', 'province'
            )
        }),
        ('Office Information', {
            'fields': ('designation', 'contact_email')
        }),

    )

    filter_horizontal = ['permissions_requested']

    def request_name(self, obj):
        return f"{obj.first_name} {obj.last_name} - {obj.designation}"

    request_name.short_description = 'Request Name'

    def pdf_download_button(self, obj):
        return format_html(
            '<a href="{}" class="button" style="background-color: #4CAF50; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block; text-align: center;">Download PDF</a>',
            f'/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{obj.pk}/download-pdf/'
        )

    pdf_download_button.short_description = 'PDF Report'

    def upload_approval_button(self, obj):
        return format_html(
            '<a href="{}" class="button" style="background-color: #2196F3; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block; text-align: center;">Upload Form</a>',
            f'/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{obj.pk}/change/#approval_form'
        )

    upload_approval_button.short_description = 'Approval Form'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/download-pdf/',
                self.admin_site.admin_view(self.download_pdf),
                name='userrequest_download_pdf',
            ),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if not change:  # Only set requested_by when creating new object
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)

    def download_pdf(self, request, object_id):
        """Generate PDF report for the user request"""
        try:
            user_request = UserRequest.objects.get(pk=object_id)
        except UserRequest.DoesNotExist:
            return HttpResponse("User Request not found", status=404)

        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=0.3 * inch,
                                bottomMargin=0.3 * inch,
                                leftMargin=0.3 * inch,
                                rightMargin=0.3 * inch)
        styles = getSampleStyleSheet()

        # Custom compact styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=12,
            spaceAfter=15,
            alignment=1,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=10,
            spaceAfter=6,
            spaceBefore=8,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=4,
            leading=10,  # Line height
        )

        # Build story (content)
        story = []

        # Title
        title = Paragraph("ISOLUTION SYSTEM USER CREATION REQUEST FORM REPORT", title_style)
        story.append(title)
        story.append(Spacer(1, 0.25 * inch))

        # Grid table style with borders
        grid_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to top
        ])

        # Request Information - Grid
        story.append(Paragraph("Basic Request Information", heading_style))

        # Add italic paragraph
        italic_style = ParagraphStyle(
            'ItalicStyle',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Oblique',
            spaceAfter=12,
            alignment=0,
        )

        italic_text = "Signed this and make approval from CEO or DCEO or other concerned authority and scan it and upload in approval form"
        italic_paragraph = Paragraph(italic_text, italic_style)
        story.append(italic_paragraph)
        story.append(Spacer(1, 0.1 * inch))

        # Get user display name safely
        requested_by_display = getattr(request.user, 'get_full_name', None)
        if callable(requested_by_display):
            requested_by_name = requested_by_display() or request.user.username
        else:
            requested_by_name = getattr(request.user, 'username', 'Unknown User')

        request_data = [
            ['Field', 'Value', 'Field', 'Value'],
            ['Request ID', str(user_request.request_id), 'Request Date',
             user_request.request_date.strftime('%Y-%m-%d')],
            ['Requested By', requested_by_name, 'Department', user_request.department()],
            ['Request Type', user_request.request_type(), 'Status', user_request.status],
        ]

        request_table = Table(request_data,
                              colWidths=[1.5 * inch, 2.5 * inch, 1.5 * inch, 2.5 * inch])  # Increased widths
        request_table.setStyle(grid_style)
        story.append(request_table)
        story.append(Spacer(1, 0.1 * inch))

        # Personal Information - Grid
        story.append(Paragraph("Personal Information", heading_style))

        personal_data = [
            ['Field', 'Value', 'Field', 'Value'],
            ['First Name', user_request.first_name, 'Middle Name', user_request.middle_name or 'N/A'],
            ['Last Name', user_request.last_name, 'Gender', user_request.gender()],
            ['Email', user_request.email, 'Nationality', user_request.nationality()],
            ['Phone No', user_request.phone_no, 'Mobile No', user_request.mobile_no],
            ['SSN', user_request.ssn or 'N/A', '', ''],
        ]

        personal_table = Table(personal_data,
                               colWidths=[1.5 * inch, 2.5 * inch, 1.5 * inch, 2.5 * inch])  # Increased widths
        personal_table.setStyle(grid_style)
        story.append(personal_table)
        story.append(Spacer(1, 0.1 * inch))

        # Document & Office Information - Grid
        story.append(Paragraph("Document & Office Information", heading_style))

        doc_office_data = [
            ['Field', 'Value', 'Field', 'Value'],
            ['Document Type', user_request.document_type, 'Designation',
             user_request.designation()],
            ['Citizen No', user_request.citizen_no, 'Branch', user_request.department],
            ['Province', user_request.province() or 'N/A', 'Contact Email', user_request.contact_email],
        ]

        doc_office_table = Table(doc_office_data,
                                 colWidths=[1.5 * inch, 2.5 * inch, 1.5 * inch, 2.5 * inch])  # Increased widths
        doc_office_table.setStyle(grid_style)
        story.append(doc_office_table)
        story.append(Spacer(1, 0.1 * inch))

        # System Access Permissions - Grid
        story.append(Paragraph("System Access Permissions", heading_style))

        access_data = [
            ['Permission', 'Status', 'Permission', 'Status'],
            ['Approve Transaction', 'YES' if user_request.allow_approve_transaction else 'NO', 'Back Date',
             'YES' if user_request.allow_back_date else 'NO'],
            ['Regional Head', 'YES' if user_request.is_regional_head else 'NO', 'Branch Manager',
             'YES' if user_request.is_branch_manager else 'NO'],
            ['Advance Payment', 'YES' if user_request.allow_advance_payment else 'NO', 'ME User',
             'YES' if user_request.is_me_user else 'NO'],
        ]

        access_table = Table(access_data,
                             colWidths=[1.8 * inch, 1.2 * inch, 1.8 * inch, 1.2 * inch])  # Increased widths
        access_table.setStyle(grid_style)
        story.append(access_table)
        story.append(Spacer(1, 0.1 * inch))

        # Requested Permissions - Improved 3 Column Grid with Sequence Numbers
        if user_request.permissions_requested.exists():
            story.append(Paragraph("Requested Menu Permissions", heading_style))

            # Create permissions list with sequence numbers and proper wrapping
            permissions = []
            for idx, perm in enumerate(user_request.permissions_requested.all(), 1):
                if perm.parent_menu:
                    display_name = f"{idx}. {perm.name} - {perm.parent_menu}"
                else:
                    display_name = f"{idx}. {perm.name}"
                permissions.append(display_name)

            # Create 3-column grid with better layout
            permission_data = []

            # Calculate how many rows we need for 3 columns
            num_permissions = len(permissions)
            num_rows = (num_permissions + 2) // 3  # Ceiling division

            for row in range(num_rows):
                row_data = []
                for col in range(3):
                    index = row * 3 + col
                    if index < num_permissions:
                        # Use Paragraph for automatic text wrapping
                        permission_text = permissions[index]
                        row_data.append(Paragraph(permission_text, normal_style))
                    else:
                        row_data.append('')  # Empty cell for alignment
                permission_data.append(row_data)

            # Add header row
            permission_data.insert(0, [
                Paragraph('<b>Menu Permission</b>', normal_style),
                Paragraph('<b>Menu Permission</b>', normal_style),
                Paragraph('<b>Menu Permission</b>', normal_style)
            ])

            permission_table = Table(permission_data,
                                     colWidths=[2.2 * inch, 2.2 * inch, 2.2 * inch])  # Increased widths
            permission_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(permission_table)
            story.append(Spacer(1, 0.1 * inch))

        # Description - Improved single row grid with better text handling
        if user_request.description:
            story.append(Paragraph("Description", heading_style))
            desc_text = user_request.description

            # Use Paragraph for automatic text wrapping instead of truncating
            desc_paragraph = Paragraph(desc_text, normal_style)

            desc_data = [[Paragraph('<b>Description</b>', normal_style)]]
            desc_data.append([desc_paragraph])

            desc_table = Table(desc_data, colWidths=[6.5 * inch])  # Increased width
            desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(desc_table)
            story.append(Spacer(1, 0.1 * inch))

        # Memo Information - Grid with improved text handling
        story.append(Paragraph("Memo Information", heading_style))

        memo_ref = user_request.memo_reference_no or 'N/A'
        memo_date = user_request.memo_date.strftime('%Y-%m-%d') if user_request.memo_date else 'N/A'
        memo_subject = user_request.memo_subject or 'N/A'

        # Use Paragraphs for memo subject to handle long text
        memo_subject_para = Paragraph(memo_subject, normal_style) if len(memo_subject) > 50 else memo_subject

        memo_data = [
            ['Field', 'Value'],
            ['Reference No', memo_ref],
            ['Date', memo_date],
            ['Subject', memo_subject_para],
        ]

        memo_table = Table(memo_data, colWidths=[1.8 * inch, 5.2 * inch])  # Increased widths
        memo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(memo_table)
        story.append(Spacer(1, 0.1 * inch))

        # Remarks - Improved single row grid
        if user_request.remarks:
            story.append(Paragraph("Remarks", heading_style))
            remarks_text = user_request.remarks

            # Use Paragraph for automatic text wrapping
            remarks_paragraph = Paragraph(remarks_text, normal_style)

            remarks_data = [[Paragraph('<b>Remarks</b>', normal_style)]]
            remarks_data.append([remarks_paragraph])

            remarks_table = Table(remarks_data, colWidths=[6.5 * inch])  # Increased width
            remarks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(remarks_table)
            story.append(Spacer(1, 0.1 * inch))

        # Approval Information - Grid
        story.append(Paragraph("Approval Information", heading_style))

        # Safely get approved_by display name
        if user_request.approved_by:
            approved_by_display = getattr(user_request.approved_by, 'get_full_name', None)
            if callable(approved_by_display):
                approved_by_name = approved_by_display() or user_request.approved_by.username
            else:
                approved_by_name = getattr(user_request.approved_by, 'username', 'Unknown')
        else:
            approved_by_name = 'N/A'

        approval_info_data = [
            ['Field', 'Value'],
            ['Approved By', approved_by_name],
            ['Approval Date', user_request.approval_date.strftime('%Y-%m-%d') if user_request.approval_date else 'N/A'],
        ]
        approval_info_table = Table(approval_info_data, colWidths=[1.8 * inch, 5.2 * inch])  # Increased widths
        approval_info_table.setStyle(grid_style)
        story.append(approval_info_table)
        story.append(Spacer(1, 0.1 * inch))

        # Approved By Section - Single line format
        story.append(Spacer(1, 0.3 * inch))

        # Create the approval section with single lines for signatures
        approval_data = [
            ['Approved By:', '_________________________'],
        ]

        approval_table = Table(approval_data, colWidths=[1.5 * inch, 3 * inch])  # Adjusted widths
        approval_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(approval_table)

        # Build PDF
        doc.build(story)

        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"user_request_{user_request.request_id}_{user_request.first_name}_{user_request.last_name}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


    def has_delete_permission(self, request, obj=None):
        # Remove delete permission for all users
        return False

    def has_change_permission(self, request, obj=None):
        # Only allow editing if the user created the record or is superuser
        if obj is not None:
            return obj.requested_by == request.user or request.user.is_superuser
        return super().has_change_permission(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Regular users can only see their own requests
        if not request.user.is_superuser:
            qs = qs.filter(requested_by=request.user)
        return qs


# admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(UserRequest, UserRequestAdmin)



@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_menu')
    search_fields = ('name', 'parent_menu')
    actions = None  # disables default bulk delete

    # ✅ Disable delete for normal users
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # only superuser can delete

    # ✅ Add custom URL for Excel upload
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.upload_excel, name='menuitem_upload_excel'),
        ]
        return custom_urls + urls

    # ✅ Add the upload button to admin interface
    change_list_template = "admin/menuitem_changelist.html"

    # ✅ Define upload view
    def upload_excel(self, request):
        if request.method == "POST":
            form = UploadExcelForm(request.POST, request.FILES)
            if form.is_valid():
                df = pd.read_excel(request.FILES['excel_file'])
                created, skipped = 0, 0
                for _, row in df.iterrows():
                    name = str(row['name']).strip()
                    parent_menu = str(row.get('parent_menu', '')).strip()
                    if not MenuItem.objects.filter(name=name).exists():
                        MenuItem.objects.create(name=name, parent_menu=parent_menu)
                        created += 1
                    else:
                        skipped += 1
                messages.success(request, f"Upload complete: {created} added, {skipped} skipped.")
                return redirect("..")
        else:
            form = UploadExcelForm()
        return render(request, "admin/upload_excel.html", {"form": form, "title": "Upload Menu Items via Excel"})