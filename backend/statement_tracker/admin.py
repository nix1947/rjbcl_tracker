from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Bank, Transaction

# Custom User Admin
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
            'fields': ('email', 'username', 'full_name', 'mobile', 'password', 'password2',
                       'is_staff', 'is_superuser', 'is_active'),
        }),
    )
    # Note: For add_fieldsets, you'd typically have a custom form (UserCreationForm)
    # to handle password confirmation ('password2'), but this is a basic setup.

admin.site.register(User, UserAdmin)

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
        'system_voucher_no', 'bank', 'bank_account_no', 'voucher_amount', 'status',
        'created_by', 'created_date', 'system_value_date', 'is_verified'
    )
    list_filter = ('status', 'is_verified', 'bank', 'source', 'bank_deposit_date', 'system_value_date', 'created_date')
    search_fields = (
        'system_voucher_no', 'bank_account_no', 'bank_trans_id', 'cheque_no',
        'policy_no', 'transaction_detail', 'created_by__username', 'bank__name'
    )
    readonly_fields = ('created_date', 'created_by') # Often 'created_by' is set automatically

    fieldsets = (
        ('Core Information', {
            'fields': ('system_voucher_no', 'bank', 'bank_account_no', 'bank_trans_id', 'bank_deposit_date', 'transaction_detail')
        }),
        ('Financials', {
            'fields': ('voucher_amount', 'debit', 'credit', 'refund_amount')
        }),
        ('Categorization & Status', {
            'fields': ('source', 'status', 'is_verified', 'used_in_system')
        }),
        ('System Dates & Users', {
            'fields': ('created_by', 'created_date', 'system_value_date', 'reconciled_by', 'reconciled_date',
                       'system_posted_by', 'system_verified_by')
        }),
        ('Additional Identifiers', {
            'fields': ('cheque_no', 'policy_no', 'reverse_voucher_no', 'reversal_correction_voucher_no', 'refund_voucher_no')
        }),
        ('Attachments & Remarks', {
            'fields': ('voucher_image', 'remarks')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk: # if creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # If you want to display the image in admin (optional)
    # def voucher_image_tag(self, obj):
    #     from django.utils.html import format_html
    #     if obj.voucher_image:
    #         return format_html('<img src="{}" width="150" height="auto" />', obj.voucher_image.url)
    #     return "-"
    # voucher_image_tag.short_description = 'Voucher Image Preview'
    #
    # # Add to list_display or readonly_fields if needed
    # readonly_fields = ('created_date', 'created_by', 'voucher_image_tag')