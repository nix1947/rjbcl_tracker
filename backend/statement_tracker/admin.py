from django.utils import timezone

from .models import User, BankStatementChangeHistory

from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
import copy



from django.http import HttpResponse

from django import forms
from django.contrib import  messages
from django.shortcuts import render, redirect
from django.urls import path
from .models import BankStatement
import csv
import io
from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
import json



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'username', 'full_name', 'mobile', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'full_name', 'mobile')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'full_name', 'mobile')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'mobile', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )

admin.site.register(User, UserAdmin)
class RJCBLAdminSite(AdminSite):
    site_header = _('RJCBL Administration')
    site_title = _('RJCBL Admin Portal')
    index_title = _('Welcome to RJCBL Administration')

    def get_app_list(self, request):
        """
        Customize the app list ordering and labeling
        """
        app_list = super().get_app_list(request)
        # Reorder or rename apps as needed
        return app_list

# Replace the default admin site
admin_site = RJCBLAdminSite(name='rjcbl_admin')



class CSVUploadForm(forms.Form):
    """Class for BankStatement bulk upload form"""
    csv_file = forms.FileField()


class BankTransactionForm(forms.ModelForm):
    balance = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    debit = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    credit = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    system_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = BankStatement
        fields = '__all__'



@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):

    # Template for bulk upload csv
    change_list_template = "admin/bankstatement_changelist.html"
    form = BankTransactionForm


    list_display = (
        'bank_code', 'bank_name', 'bank_account_no',
        'bank_deposit_date', 'bank_transaction_detail',
        'debit', 'credit', 'balance',
        'system_voucher_no', 'system_amount',
        'policy_no', 'branch', 'source',
        'modified_by',
        'created_by', 'bank_voucher', 'last_updated', 'created_date', 'export_action_link'
    )

    list_filter = ('branch', 'source', 'bank_name', 'last_updated', 'created_date')
    search_fields = ( 'policy_no', 'bank_transaction_detail','credit', 'bank_deposit_date', 'source','bank_account_no', 'system_voucher_no', 'balance', 'remarks', 'bank_name', 'bank_code')
    ordering = ('-created_date',)
    date_hierarchy = 'created_date'
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        # List of fields to make read-only
        read_only_fields = [
            'bank_code', 'bank_name', 'bank_account_no',
            'bank_deposit_date', 'bank_transaction_detail',
            'debit', 'credit', 'balance', 'bank_voucher', 'created_by', 'created_date', 'last_updated'
        ]

        # If user is superuser, return no readonly fields
        if request.user.is_superuser:
            return ['created_by', 'created_date', 'last_updated']

        # Otherwise, make all fields in the fieldset read-only
        return read_only_fields

    fieldsets = (
        ('Bank Details', {
            'fields': (
                'bank_code', 'bank_name', 'bank_account_no',
                'bank_deposit_date', 'bank_transaction_detail',
                'debit', 'credit', 'balance', 'bank_voucher'
            )
        }),
        ('System Information', {
            'fields': (
                'system_voucher_no', 'system_amount',
                'policy_no', 'remarks',
                'branch', 'source',
                'created_by', 'created_date','last_updated'
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Allow delete only if it's a single object and user is superuser
        if obj is not None and request.user.is_superuser:
            return True
        return False

    def get_actions(self, request):
        # Remove bulk delete action for all users, including superuser
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def export_action_link(self, obj):
        url = reverse('admin:bankstatement_export_single', args=[obj.pk])
        return format_html('<a href="{}">Export CSV</a>', url)

    export_action_link.short_description = "Export"

    actions = ['export_selected_as_csv']

    def get_export_data(self, queryset):
        """Method to export the data"""
        data = []
        for obj in queryset:
            data.append({
                'Bank Code': obj.bank_code,
                'Bank Name': obj.bank_name,
                'Account No': obj.bank_account_no,
                'Deposit Date': obj.bank_deposit_date,
                'Transaction Detail': obj.bank_transaction_detail,
                'Debit': obj.debit,
                'Credit': obj.credit,
                'Balance': obj.balance,
                'Voucher No': obj.system_voucher_no,
                'System Amount': obj.system_amount,
                'Policy No': str(obj.policy_no),
                'Remarks': obj.remarks,
                'Branch': obj.branch,
                'Source': obj.source,
                'Created By': str(obj.created_by),
                'Created Date': obj.created_date,
                'Last Updated': obj.last_updated,
            })
        return data

    def export_selected_as_csv(self, request, queryset):
        return self.export_as_csv_response(queryset, filename="BankReconcillation.csv")

    def export_as_csv_response(self, queryset, filename):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        response.write('\ufeff')  # UTF-8 BOM

        data = self.get_export_data(queryset)
        if not data:
            return response

        writer = csv.DictWriter(response, fieldnames=data[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return response

    export_selected_as_csv.short_description = "Export selected as CSV"

    def export_single_record(self, request, object_id):
        queryset = self.get_queryset(request).filter(pk=object_id)
        return self.export_as_csv_response(queryset, filename="bank_statement.csv")

    def save_model(self, request, obj, form, change):
        if change:
            obj.modified_by = request.user  # ✅ set current user
            old_instance = copy.deepcopy(BankStatement.objects.get(pk=obj.pk))

        super().save_model(request, obj, form, change)

        if change:
            BankStatementChangeHistory.objects.create(
                bank_statement=obj,
                bank_code=old_instance.bank_code,
                bank_name=old_instance.bank_name,
                bank_account_no=old_instance.bank_account_no,
                bank_deposit_date=old_instance.bank_deposit_date,
                balance=old_instance.balance,
                bank_transaction_detail=old_instance.bank_transaction_detail,
                debit=old_instance.debit,
                credit=old_instance.credit,
                system_voucher_no=old_instance.system_voucher_no,
                system_amount=old_instance.system_amount,
                policy_no=old_instance.policy_no,
                remarks=old_instance.remarks,
                branch=old_instance.branch,
                source=old_instance.source,
                changed_by=request.user,  # ✅ current admin user
                changed_at=timezone.now(),
                action='UPDATE'
            )

    def delete_model(self, request, obj):
        old_instance = copy.deepcopy(obj)

        BankStatementChangeHistory.objects.create(
            bank_statement=obj,
            bank_code=old_instance.bank_code,
            bank_name=old_instance.bank_name,
            bank_account_no=old_instance.bank_account_no,
            bank_deposit_date=old_instance.bank_deposit_date,
            balance=old_instance.balance,
            bank_transaction_detail=old_instance.bank_transaction_detail,
            debit=old_instance.debit,
            credit=old_instance.credit,
            system_voucher_no=old_instance.system_voucher_no,
            system_amount=old_instance.system_amount,
            policy_no=old_instance.policy_no,
            remarks=old_instance.remarks,
            branch=old_instance.branch,
            source=old_instance.source,
            changed_by=request.user,  # ✅ current admin user
            changed_at=timezone.now(),
            action='DELETE'
        )

        super().delete_model(request, obj)




    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload-csv/", self.upload_csv, name="bankstatement_upload_csv"),
            path("<path:object_id>/export/", self.export_single_record, name="bankstatement_export_single"),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        """Function for handling CSV upload and insert data in BankStatement model"""
        if request.method == "POST":
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data['csv_file']
                try:
                    decoded_file = file.read().decode('utf-8-sig')
                    reader = csv.DictReader(io.StringIO(decoded_file))

                    count_created = 0
                    count_skipped = 0

                    for row in reader:
                        bank_code = row['bank_code'].strip()
                        bank_name = row['bank_name'].strip()
                        bank_account_no = row['bank_account_no'].strip()
                        bank_deposit_date = datetime.strptime(row['bank_deposit_date'].strip(), '%Y-%m-%d').date()
                        bank_transaction_detail = row['bank_transaction_detail'].strip()
                        debit = float(row.get('debit', 0) or 0)
                        credit = float(row.get('credit', 0) or 0)
                        balance = float(row.get('balance', 0) or 0)

                        exists = BankStatement.objects.filter(
                            bank_code=bank_code,
                            bank_deposit_date=bank_deposit_date,
                            credit=credit,
                            balance=balance
                        ).exists()

                        if exists:

                            count_skipped += 1
                            continue

                        BankStatement.objects.create(
                            bank_code=bank_code,
                            bank_name=bank_name,
                            bank_account_no=bank_account_no,
                            bank_deposit_date=bank_deposit_date,
                            bank_transaction_detail = bank_transaction_detail,
                            debit=debit,
                            credit=credit,
                            balance=balance,
                            created_by=request.user
                        )
                        count_created += 1



                    self.message_user(
                        request,
                        f"CSV upload complete: {count_created} created, {count_skipped} skipped (duplicates).",
                        messages.SUCCESS
                    )
                    return redirect("..")
                except Exception as e:
                    print(e)
                    self.message_user(request, f"Error: {str(e)}", messages.ERROR)

        else:
            form = CSVUploadForm()

        return render(request, "admin/csv_upload_form.html", {"form": form})



@admin.register(BankStatementChangeHistory)
class BankStatementChangeHistoryAdmin(admin.ModelAdmin):
    """Django admin for Log audit for BankStatementChangeHistory. model"""

    list_display = (
        'bank_code', 'bank_name','changed_at', 'changed_by', 'policy_no',
        'bank_code', 'bank_name', 'bank_account_no', 'bank_deposit_date',
        'balance', 'debit', 'credit', 'branch', 'source', 'action'
    )
    list_filter = ('changed_at', 'changed_by', 'bank_code', 'bank_name')
    search_fields = ('bank_statement__bank_code', 'bank_statement__bank_name', 'changed_by__username')
    readonly_fields = (
        'bank_statement', 'changed_at', 'changed_by',
        'bank_code', 'bank_name', 'bank_account_no', 'bank_deposit_date',
        'balance', 'bank_transaction_detail', 'debit', 'credit',
        'system_voucher_no', 'system_amount', 'policy_no', 'remarks',
        'branch', 'source',
    )


    actions = ['export_selected_as_csv']

    def has_add_permission(self, request):
        # Prevent adding manually in admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion from admin
        return False

    def export_selected_as_csv(self, request, queryset):
        return self.export_as_csv_response(queryset, filename="ReconcillationEditedHistory.csv")

    def export_as_csv_response(self, queryset, filename):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        response.write('\ufeff')  # UTF-8 BOM

        data = self.get_export_data(queryset)
        if not data:
            return response

        writer = csv.DictWriter(response, fieldnames=data[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return response


    def get_export_data(self, queryset):
        """Method to export the data"""
        data = []
        for obj in queryset:
            data.append({
                'Bank Code': obj.bank_code,
                'Bank Name': obj.bank_name,
                'Account No': obj.bank_account_no,
                'Deposit Date': obj.bank_deposit_date,
                'Transaction Detail': obj.bank_transaction_detail,
                'Debit': obj.debit,
                'Credit': obj.credit,
                'Balance': obj.balance,
                'Voucher No': obj.system_voucher_no,
                'System Amount': obj.system_amount,
                'Policy No': obj.policy_no,
                'Remarks': obj.remarks,
                'Branch': obj.branch,
                'Source': obj.source,
                'Changed By': str(obj.changed_by),
                'Created Date': obj.changed_at,
                'action': obj.action
            })
        return data





@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = [
        'action_time', 'user', 'content_type', 'object_link', 'action_type', 'display_changes'
    ]
    list_filter = ['action_flag', 'user', 'content_type']
    search_fields = ['object_repr', 'change_message']
    readonly_fields = [f.name for f in LogEntry._meta.fields]

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            return format_html(f"<i>{obj.object_repr}</i>")
        try:
            url = reverse(f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change", args=[obj.object_id])
            return format_html('<a href="{}">{}</a>', url, obj.object_repr)
        except:
            return obj.object_repr
    object_link.short_description = 'Object'

    def has_delete_permission(self, request, obj=None):
        # 🔒 Prevent delete for all users including superusers
        return False

    def action_type(self, obj):
        if obj.action_flag == ADDITION:
            return format_html('<span style="color:green;">Created</span>')
        elif obj.action_flag == CHANGE:
            return format_html('<span style="color:orange;">Modified</span>')
        elif obj.action_flag == DELETION:
            return format_html('<span style="color:red;">Deleted</span>')
        return obj.action_flag
    action_type.short_description = 'Action'

    def display_changes(self, obj):
        if obj.change_message and obj.action_flag == CHANGE:
            try:
                # parse if it's a structured change
                changes = json.loads(obj.change_message)
                if isinstance(changes, list):
                    formatted = '<ul>'
                    for change in changes:
                        if isinstance(change, dict):
                            for field, values in change.items():
                                formatted += f'<li><b>{field}</b>: {values}</li>'
                        else:
                            formatted += f"<li>{change}</li>"
                    formatted += '</ul>'
                    return mark_safe(formatted)
            except json.JSONDecodeError:
                return obj.change_message
        return obj.change_message or '-'
    display_changes.short_description = 'Changes'



