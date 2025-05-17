from django.http import HttpResponse
from django.utils import timezone

from .models import User, Bank, Transaction

from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook



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


# Bank Admin
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)

# Transaction Admin
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'system_voucher_no',
        'branch',
        'created_by',
        'created_date',
        'bank',
        'bank_account_no',
        'bank_trans_id',
        'bank_deposit_date',
        'cheque_no',
        'policy_no',
        'transaction_detail',
        'system_value_date',
        'debit',
        'credit',
        'used_in_system',
        'reconciled_by',
        'reconciled_date',
        'system_posted_by',
        'system_verified_by',
        'voucher_amount',
        'refund_amount',
        'reverse_voucher_no',
        'reversal_correction_voucher_no',
        'refund_voucher_no',
        'remarks',
        'source',
        'status',
        'is_verified',
        'voucher_image',
    )

    list_filter = (
        'branch',
        'status',
        'is_verified',
        'used_in_system',
        'source',
        'bank',
        'created_date',
        'bank_deposit_date',
        'system_value_date',
    )

    search_fields = (
        'system_voucher_no',
        'bank_trans_id',
        'bank_account_no',
        'policy_no',
        'cheque_no',
        'transaction_detail',
        'remarks',
        'reverse_voucher_no',
        'reversal_correction_voucher_no',
        'refund_voucher_no',
    )

    readonly_fields = (
        'created_date',
    )

    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'system_voucher_no',
                'branch',
                'status',
                'is_verified',
                'used_in_system',
                'source',
            )
        }),
        ('Bank Details', {
            'fields': (
                'bank',
                'bank_account_no',
                'bank_trans_id',
                'bank_deposit_date',
                'cheque_no',
            )
        }),
        ('Financial Details', {
            'fields': (
                'debit',
                'credit',
                'voucher_amount',
                'refund_amount',
            )
        }),
        ('Reference Numbers', {
            'fields': (
                'policy_no',
                'reverse_voucher_no',
                'reversal_correction_voucher_no',
                'refund_voucher_no',
            )
        }),
        ('Dates', {
            'fields': (
                'created_date',
                'system_value_date',
            )
        }),
        ('Descriptions', {
            'fields': (
                'transaction_detail',
                'remarks',
            )
        }),
        ('Documentation', {
            'fields': (
                'voucher_image',
            )
        }),
        ('User References', {
            'fields': (
                'created_by',
                'reconciled_by',
                'reconciled_date',
                'system_posted_by',
                'system_verified_by',
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by during the first save
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # Make created_by read-only after creation
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields

    # Add export action
    actions = ['export_to_excel']

    def export_to_excel(self, request, queryset):
        """
        Export selected transactions to Excel
        """
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"transactions_export_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={filename}'

        wb = Workbook()
        ws = wb.active
        ws.title = "Transactions"

        # Write headers
        headers = [
            'System Voucher No',
            'Branch',
            'Created By',
            'Created Date',
            'Bank',
            'Bank Account No',
            'Bank Transaction ID',
            'Bank Deposit Date',
            'Cheque No',
            'Policy No',
            'Transaction Detail',
            'System Value Date',
            'Debit',
            'Credit',
            'Used in System',
            'Reconciled By',
            'Reconciled Date',
            'System Posted By',
            'System Verified By',
            'Voucher Amount',
            'Refund Amount',
            'Reverse Voucher No',
            'Reversal Correction Voucher No',
            'Refund Voucher No',
            'Remarks',
            'Source',
            'Status',
            'Is Verified',
        ]

        ws.append(headers)

        # Write data
        for transaction in queryset:
            ws.append([
                transaction.system_voucher_no,
                str(transaction.branch) if transaction.branch else '',
                str(transaction.created_by) if transaction.created_by else '',
                transaction.created_date.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_date else '',
                str(transaction.bank) if transaction.bank else '',
                transaction.bank_account_no or '',
                transaction.bank_trans_id or '',
                transaction.bank_deposit_date.strftime('%Y-%m-%d') if transaction.bank_deposit_date else '',
                transaction.cheque_no or '',
                transaction.policy_no or '',
                transaction.transaction_detail or '',
                transaction.system_value_date.strftime('%Y-%m-%d') if transaction.system_value_date else '',
                transaction.debit or 0,
                transaction.credit or 0,
                'Yes' if transaction.used_in_system else 'No',
                str(transaction.reconciled_by) if transaction.reconciled_by else '',
                transaction.reconciled_date.strftime('%Y-%m-%d %H:%M:%S') if transaction.reconciled_date else '',
                str(transaction.system_posted_by) if transaction.system_posted_by else '',
                str(transaction.system_verified_by) if transaction.system_verified_by else '',
                transaction.voucher_amount or 0,
                transaction.refund_amount or 0,
                transaction.reverse_voucher_no or '',
                transaction.reversal_correction_voucher_no or '',
                transaction.refund_voucher_no or '',
                transaction.remarks or '',
                transaction.source or '',
                transaction.status or '',
                'Yes' if transaction.is_verified else 'No',
            ])

        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected transactions to Excel"