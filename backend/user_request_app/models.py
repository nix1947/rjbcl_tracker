from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from rjbcl.common_data import (
    GENDER_CHOICES, NATIONALITY_CHOICES, DOCUMENT_TYPE_CHOICES,
    PROVINCE_CHOICES, DESIGNATION_CHOICES

)
from ticket.models import  Department

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MenuItem(models.Model):
    """Represents all available system modules or permissions."""
    name = models.CharField(max_length=150, unique=True)
    parent_menu = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']
        verbose_name = "ISolution Menu / Module"
        verbose_name_plural = "Isolution Menus / Modules"

    def __str__(self):
        return self.name + " - " + self.parent_menu


class UserRequest(models.Model):
    """Main user request form for software/system access."""
    REQUEST_TYPE_CHOICES = [
        ('New Access', 'New Access'),
        ('Modification', 'Access Modification'),
        ('Deactivation', 'Deactivation'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    request_id = models.AutoField(primary_key=True)
    request_date = models.DateField(auto_now_add=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests_made')
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tickets",
        help_text="New user Department or branch"
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField( verbose_name="RJBCL office email", unique=True)
    phone_no = models.CharField(max_length=20)
    mobile_no = models.CharField(max_length=20)
    ssn = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=30, choices=NATIONALITY_CHOICES)

    # --- Document Information ---
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, default='Citizen')
    citizen_no = models.CharField(max_length=50)
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES, blank=True, null=True)

    # --- Office Information ---
    designation = models.CharField(max_length=100, choices=DESIGNATION_CHOICES)

    # --- System Access Flags ---
    allow_approve_transaction = models.BooleanField(default=False)
    allow_back_date = models.BooleanField(default=False)
    is_regional_head = models.BooleanField(default=False)
    is_branch_manager = models.BooleanField(default=False)
    allow_advance_payment = models.BooleanField(default=False)
    is_me_user = models.BooleanField(default=False)

    contact_email = models.EmailField(verbose_name="Personal Email")
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES, default='New Access')
    description = models.TextField(blank=True, null=True)

    # many-to-many relationship to MenuItem
    permissions_requested = models.ManyToManyField(MenuItem, related_name='user_requests')

    # memo fields
    memo_reference_no = models.CharField(max_length=50, blank=True, null=True)
    memo_date = models.DateField(blank=True, null=True)
    memo_subject = models.CharField(max_length=200, blank=True, null=True)
    approval_form = models.FileField(
        upload_to="isolution/user_request",
        verbose_name="फारम सबमिट गरेपछि  डाउनलोड गरी हस्ताक्षर गरेर फेरि स्क्यान गरी पुनः यहाँ अपलोड गर्नुहोस्",
        blank=True,
        null=True
    )

    # approval and status
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='requests_approved', null=True, blank=True)
    approval_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Request #{self.request_id} - {self.requested_by.username}"

    class Meta:
        verbose_name = "User Request"
        verbose_name_plural = "Request -> New Isolution User"
        ordering = ['-request_date']




class UserAccessRequest(models.Model):
    SYSTEM_CHOICES = [
        ('ACTIVE_DIRECTORY', 'Active Directory'),
        ('EMAIL', 'Email Account'),
        ('HR_SYSTEM', 'HR System'),
        ('OTHER', 'Other'),
    ]

    # User Details
    full_name = models.CharField(max_length=100, verbose_name="Full Name")
    mobile = models.CharField(max_length=15, verbose_name="Mobile Number")
    email = models.EmailField(verbose_name="Email Address")
    designation = models.CharField(max_length=255, choices=DESIGNATION_CHOICES)

    # System Access
    system_type = models.CharField(
        max_length=20,
        choices=SYSTEM_CHOICES,
        default='ACTIVE_DIRECTORY',
        verbose_name="System Type"
    )

    # Approval Document
    approval_form = models.FileField(
        upload_to='approval_forms/',
        verbose_name="Approval Form",
        help_text="Upload scanned approval document",
        blank=True,
        null=True
    )

    # Request Information (Auto-populated)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Requested By",
        related_name='access_requests_created'
    )

    requested_dept = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Requesting Department"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Computer, AD, Email -> User Access Request"
        verbose_name_plural = "Computer, AD, Email -> User Access Request"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.get_system_type_display()}"