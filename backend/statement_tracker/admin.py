from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Bank, Transaction
from django.contrib.auth.admin import UserAdmin



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

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

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.http import HttpResponse
import openpyxl


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
