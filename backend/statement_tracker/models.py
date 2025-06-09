# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
from django.conf import settings
from django.core.exceptions import ValidationError



class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, full_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='Email Address')
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, verbose_name='Full Name')
    mobile = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    def clean(self):
        super().clean()
        errors = {}
        
        # Email validation
        if self.email:
            self.email = self.email.strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
                errors['email'] = _('Enter a valid email address.')
        
        # Username validation
        if self.username:
            self.username = self.username.strip()
            if len(self.username) < 4:
                errors['username'] = _('Username must be at least 4 characters.')
            if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
                errors['username'] = _('Username can only contain letters, numbers and underscores.')
        
        # Full name validation
        if self.full_name:
            self.full_name = ' '.join(self.full_name.strip().split())
            if len(self.full_name) < 3:
                errors['full_name'] = _('Full name must be at least 3 characters.')
            if len(self.full_name.split()) < 2:
                errors['full_name'] = _('Please provide both first and last name.')
        
        # Mobile validation
        if self.mobile and self.mobile.strip():
            self.mobile = self.mobile.strip()
            if not self.mobile.isdigit():
                errors['mobile'] = _('Mobile number should contain only digits.')
            if len(self.mobile) < 10:
                errors['mobile'] = _('Mobile number should be at least 10 digits.')
            if len(self.mobile) > 20:
                errors['mobile'] = _('Mobile number should not exceed 20 digits.')
        else:
            self.mobile = None
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'




class BankStatement(models.Model):
    objects = None
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('REFUND', 'Refund'),
    ]

    SOURCE_TYPES = [
        ('Cheque', 'Cheque'),
        ('BankVoucher', 'Physical Bank Voucher'),
        ('PhonePay', 'PhonePay'),
        ('ConnectIPS', 'ConnectIPS'),
        ('Esewa', 'Esewa'),
        ('Khalti', 'Khalti'),
        ('IMEPAY', 'IMEPAY'),
        ('NEPALPAY', 'NEPALPAY'),
        ('Other', 'Other'),
    ]

    BRANCH_CHOICES = [
        ('head_office', 'प्रधान कार्यलय'),
        ('chabahil', 'चाबहिल'),
        ('lagankhel', 'लगनखेल'),
        ('kalanki', 'कलंकी'),
        ('suryabinayak', 'सूर्यविनायक'),
        ('banepa', 'बनेपा'),
        ('biratnagar', 'विराटनगर'),
        ('birgunj', 'वीरगञ्ज'),
        ('pokhara', 'पोखरा'),
        ('butwal', 'बुटवल'),
        ('nepalgunj', 'नेपालगञ्ज'),
        ('dhangadhi', 'धनगढी'),
        ('hetauda', 'हेटौडा'),
        ('bhaktapur', 'भक्तपुर'),
        ('lalitpur', 'ललितपुर'),
        ('baglung', 'बागलुङ'),
        ('dhankuta', 'धनकुटा'),
        ('birtamod', 'बिर्तामोड'),
        ('narayangadh', 'नारायणगढ'),
        ('ghorahi', 'घोराही'),
    ]

    def validate_file_size(file):
        max_size = 5 * 1024 * 1024  # 1MB
        if file.size > max_size:
            raise ValidationError("File too large (max 1MB)")

    bank_code = models.CharField(max_length=255, help_text="NBL")
    bank_name = models.CharField(max_length=255, help_text="Bank name")
    bank_account_no = models.CharField(max_length=255, null=True, help_text="Bank account number")
    bank_deposit_date = models.DateField(null=True, blank=True, help_text="Bank deposit date")
    balance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Bank balance")
    bank_transaction_detail= models.CharField(max_length=255, null=True, help_text="Bank transaction detail")
    debit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Debit amount")
    credit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Credit amount")
    system_voucher_no = models.CharField(max_length=255, blank=True, null=True, help_text="System voucher number (e.g., RP300181820000001)")
    system_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="System amount")
    policy_no = models.CharField(max_length=500, null=True, help_text="Policy number(s), e.g., 2156, 2122")
    remarks = models.TextField(blank=True, null=True, help_text="Remarks")
    branch = models.CharField(max_length=255, choices=BRANCH_CHOICES, null=True, blank=True, help_text="Receipt Issue From Branch")
    source = models.CharField(max_length=50, choices=SOURCE_TYPES, null=True, blank=True, help_text="Transaction Source")
    bank_voucher = models.FileField(
        upload_to='vouchers/',
        blank=True,
        null=True,
        validators=[validate_file_size]
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bankstatement_createdby', on_delete=models.PROTECT)
    created_date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.bank_code} - {self.policy_no or 'N/A'}"



    class Meta:
        verbose_name = "Bank Statement"
        verbose_name_plural = "Bank Statements"
        ordering = ['-created_date']
        constraints = [
            models.UniqueConstraint(fields=['bank_code', 'balance', 'credit', 'bank_deposit_date'],
                                    name='unique_bank_statement')
        ]


class BankStatementChangeHistory(models.Model):
    """
    Django model to save the log of bank statement changes
    """
    ACTION_CHOICES = [
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    bank_statement = models.ForeignKey('BankStatement', on_delete=models.SET_NULL, null=True, blank=True, related_name='change_history')

    bank_code = models.CharField(max_length=255, help_text="NBL")
    bank_name = models.CharField(max_length=255, help_text="Bank name")
    bank_account_no = models.CharField(max_length=255, null=True, help_text="Bank account number")
    bank_deposit_date = models.DateField(null=True, blank=True, help_text="Bank deposit date")
    balance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Bank balance")
    bank_transaction_detail = models.CharField(max_length=255, null=True, help_text="Bank transaction detail")
    debit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Debit amount")
    credit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Credit amount")
    system_voucher_no = models.CharField(max_length=255, blank=True, null=True, help_text="System voucher number")
    system_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text="System amount")
    policy_no = models.CharField(max_length=500, null=True, help_text="Policy number(s)")
    remarks = models.TextField(blank=True, null=True, help_text="Remarks")
    branch = models.CharField(max_length=255, null=True, blank=True, help_text="Receipt Issue From Branch")
    source = models.CharField(max_length=50, null=True, blank=True, help_text="Transaction Source")

    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(default=timezone.now, editable=False)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, help_text="Change action type")

    class Meta:
        ordering = ['-changed_at']
        verbose_name = "Bank Statement Change History"
        verbose_name_plural = "Bank Statement Change History"

    def __str__(self):
        return f"{self.action} - {self.bank_statement} at {self.changed_at} by {self.changed_by}"


# Signals for logging updates and deletes of bank statement change
@receiver(pre_save, sender='statement_tracker.BankStatement')
def create_history_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return  # New object; skip logging

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    tracked_fields = [
        'bank_code', 'bank_name', 'bank_account_no', 'bank_deposit_date', 'balance',
        'bank_transaction_detail', 'debit', 'credit', 'system_voucher_no', 'system_amount',
        'policy_no', 'remarks', 'branch', 'source'
    ]

    has_changes = any(
        getattr(old_instance, field) != getattr(instance, field)
        for field in tracked_fields
    )

    if has_changes:
        BankStatementChangeHistory.objects.create(
            bank_statement=instance,
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
            changed_by=instance.created_by,
            changed_at=timezone.now(),
            action='UPDATE'
        )


@receiver(pre_delete, sender='statement_tracker.BankStatement')
def create_history_on_delete(sender, instance, **kwargs):
    """Signal for tracking the delete of objects"""
    BankStatementChangeHistory.objects.create(
        bank_statement=instance,
        bank_code=instance.bank_code,
        bank_name=instance.bank_name,
        bank_account_no=instance.bank_account_no,
        bank_deposit_date=instance.bank_deposit_date,
        balance=instance.balance,
        bank_transaction_detail=instance.bank_transaction_detail,
        debit=instance.debit,
        credit=instance.credit,
        system_voucher_no=instance.system_voucher_no,
        system_amount=instance.system_amount,
        policy_no=instance.policy_no,
        remarks=instance.remarks,
        branch=instance.branch,
        source=instance.source,
        changed_by=instance.created_by,
        changed_at=timezone.now(),
        action='DELETE'
    )