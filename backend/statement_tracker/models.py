# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from django.conf import settings


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

class Bank(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Bank Name')
    account_no = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)

    def clean(self):
        super().clean()
        if self.name:
            self.name = ' '.join(self.name.strip().split())
            if len(self.name) < 3:
                raise ValidationError({'name': _('Bank name must be at least 3 characters.')})
            if not re.match(r'^[a-zA-Z0-9\s\-\.&]+$', self.name):
                raise ValidationError({'name': _('Bank name contains invalid characters.')})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Bank'
        verbose_name_plural = 'Banks'
        ordering = ['name']



class Transaction(models.Model):
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

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Reconciled', 'Reconciled'),
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

    branch = models.CharField(max_length=255, choices=BRANCH_CHOICES)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='transactions_created', on_delete=models.PROTECT)
    created_date = models.DateTimeField(default=timezone.now, editable=False)

    bank = models.ForeignKey('Bank', on_delete=models.PROTECT)
    bank_account_no = models.CharField(max_length=50)
    bank_trans_id = models.CharField(max_length=100, null=True, blank=False)
    bank_deposit_date = models.DateField()

    branch = models.CharField(max_length=255, choices=())
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    policy_no = models.CharField(max_length=100, blank=True, null=True)
    transaction_detail = models.TextField()

    system_voucher_no = models.CharField(max_length=100, unique=True)
    system_value_date = models.DateField()

    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)

    used_in_system = models.BooleanField(default=False)

    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='transactions_reconciled', on_delete=models.SET_NULL, blank=True, null=True)
    reconciled_date = models.DateField(blank=True, null=True)
    system_posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='transactions_posted', on_delete=models.SET_NULL, blank=True, null=True)
    system_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='transactions_verified', on_delete=models.SET_NULL, blank=True, null=True)

    voucher_amount = models.DecimalField(max_digits=18, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00, blank=True, null=True)

    reverse_voucher_no = models.CharField(max_length=100, blank=True, null=True)
    reversal_correction_voucher_no = models.CharField(max_length=100, blank=True, null=True)
    refund_voucher_no = models.CharField(max_length=100, blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)

    source = models.CharField(max_length=50, choices=SOURCE_TYPES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_verified = models.BooleanField(default=False)

    voucher_image = models.ImageField(upload_to='voucher_images/', blank=True, null=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_date']
        constraints = [
            models.UniqueConstraint(fields=['bank', 'bank_trans_id'], name='unique_bank_transaction')
        ]

    def clean(self):
        super().clean()
        errors = {}

        today = timezone.now().date()
        if self.bank_deposit_date > today:
            errors['bank_deposit_date'] = _('Deposit date cannot be in the future.')
        if self.system_value_date > today:
            errors['system_value_date'] = _('Value date cannot be in the future.')
        if self.bank_deposit_date > self.system_value_date:
            errors['system_value_date'] = _('Value date cannot be before deposit date.')

        if self.debit < 0:
            errors['debit'] = _('Debit amount cannot be negative.')
        if self.credit < 0:
            errors['credit'] = _('Credit amount cannot be negative.')
        if self.debit > 0 and self.credit > 0:
            errors['debit'] = errors['credit'] = _('Cannot have both debit and credit amounts.')
        if self.voucher_amount <= 0:
            errors['voucher_amount'] = _('Voucher amount must be positive.')

        if self.refund_amount is not None:
            if self.refund_amount < 0:
                errors['refund_amount'] = _('Refund amount cannot be negative.')
            if self.refund_amount > self.voucher_amount:
                errors['refund_amount'] = _('Refund cannot exceed voucher amount.')

        if not self.bank_account_no or not self.bank_account_no.strip():
            errors['bank_account_no'] = _('Account number is required.')
        elif not re.match(r'^[a-zA-Z0-9\-]+$', self.bank_account_no):
            errors['bank_account_no'] = _('Account number contains invalid characters.')

        if self.cheque_no and not re.match(r'^[a-zA-Z0-9\-]+$', self.cheque_no):
            errors['cheque_no'] = _('Cheque number contains invalid characters.')

        if not self.transaction_detail or len(self.transaction_detail.strip()) < 10:
            errors['transaction_detail'] = _('Detail must be at least 10 characters.')

        if not self.system_voucher_no or not self.system_voucher_no.strip():
            errors['system_voucher_no'] = _('Voucher number is required.')
        elif not re.match(r'^[a-zA-Z0-9\-_/]+$', self.system_voucher_no):
            errors['system_voucher_no'] = _('Voucher number contains invalid characters.')

        for field_name in ['reverse_voucher_no', 'reversal_correction_voucher_no', 'refund_voucher_no']:
            val = getattr(self, field_name)
            if val and not re.match(r'^[a-zA-Z0-9\-_/]+$', val):
                errors[field_name] = _(f'{field_name.replace("_", " ").title()} contains invalid characters.')

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Strip all text fields
        text_fields = [
            'bank_account_no', 'bank_trans_id', 'cheque_no', 'policy_no',
            'transaction_detail', 'system_voucher_no', 'reverse_voucher_no',
            'reversal_correction_voucher_no', 'refund_voucher_no', 'remarks'
        ]

        for field in text_fields:
            value = getattr(self, field)
            if value and isinstance(value, str):
                setattr(self, field, value.strip())

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.system_voucher_no} - {self.transaction_detail[:50]}"
