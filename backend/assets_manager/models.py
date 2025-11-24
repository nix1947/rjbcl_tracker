from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from tinymce.models import HTMLField

from rjbcl.common_data import FISCAL_YEAR_CHOICES


class ITAsset(models.Model):
    # =================================================
    # 1. CLASSIFICATION (ITIL + NEPAL GOV)
    # =================================================
    CATEGORY_CHOICES = (
        ('HW', 'Hardware (Physical)'),
        ('SW', 'Software (Installed/SaaS)'),
        ('LIC', 'License / Subscription'),
        ('NET', 'Network Infrastructure'),
        ('AMC', 'AMC / Service Contract'),  # Critical for Nepal Gov Audits
    )

    LIFECYCLE_STATUS = (
        ('PLAN', 'Planning/Procurement'),
        ('ACTIVE', 'Operational (Active)'),
        ('MAINT', 'In Maintenance/Repair'),
        ('RETIRED', 'Retired/Disposed'),
        ('LOST', 'Lost/Stolen'),
    )

    # =================================================
    # 2. PROCUREMENT (PUBLIC PROCUREMENT ACT 2063)
    # =================================================
    PROCUREMENT_METHOD_CHOICES = (
        ('DIRECT', 'Direct Purchase (Sojhai Kharid)'),
        ('SEALED', 'Sealed Quotation (Darbhau Patra)'),
        ('TENDER', 'Open Tender (Bolpatra)'),
        ('DONATION', 'Grant/Donation'),
    )

    # Basic Identity
    asset_tag = models.CharField(
        max_length=50, unique=True,
        help_text="Govt Code/Barcode (e.g., MOF-IT-001)"
    )
    name = models.CharField(max_length=200, verbose_name="Asset Name")
    category = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=LIFECYCLE_STATUS, default='ACTIVE')

    # Procurement Details (PPA Compliance)
    fiscal_year = models.CharField(
        max_length=10,
        help_text="e.g., 2080/81",
        choices=FISCAL_YEAR_CHOICES,
        verbose_name="Fiscal Year (A.B.)"

    )
    procurement_method = models.CharField(
        max_length=10,
        choices=PROCUREMENT_METHOD_CHOICES,
        default='DIRECT'
    )
    purchase_date = models.DateField(verbose_name="Kharid Miti", null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Cost (NPR)", default=0.0)
    vendor_name = models.CharField(max_length=200, blank=True, help_text="Supplier/Vendor")
    invoice_no = models.CharField(max_length=100, blank=True, verbose_name="Bill/Invoice No")

    # =================================================
    # 3. IS AUDIT & RISK (NRB/GEA GUIDELINES)
    # =================================================
    # CIA Triad for Risk Calculation
    RATING = ((1, 'Low'), (2, 'Medium'), (3, 'High'))

    confidentiality = models.IntegerField(choices=RATING, default=1, help_text="Impact if data is disclosed")
    integrity = models.IntegerField(choices=RATING, default=1, help_text="Impact if data is corrupted")
    availability = models.IntegerField(choices=RATING, default=2, help_text="Impact if system goes down")

    # Automatically calculated based on CIA
    risk_score = models.IntegerField(editable=False, default=0)
    criticality = models.CharField(max_length=10, editable=False, default='Low')

    # License & AMC Management
    amc_expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name="License/AMC Expiry",
        help_text="System will alert 30 days before this date"
    )

    # Ownership
    department = models.CharField(max_length=100, verbose_name="Sakha/Department")
    custodian = models.CharField(max_length=100, verbose_name="Responsible Person", help_text="Staff Name")
    location = models.CharField(max_length=100, help_text="Room No / Branch")

    # Technical Specs (JSON for flexibility)
    specs = HTMLField(blank=True, help_text="RAM, Storage, IP Address, etc.")

    def save(self, *args, **kwargs):
        # Auto-calculate Risk per IS Audit Guidelines
        # Risk Score = C + I + A (Max 9)
        self.risk_score = self.confidentiality + self.integrity + self.availability

        if self.risk_score >= 7:
            self.criticality = 'HIGH'
        elif self.risk_score >= 5:
            self.criticality = 'MEDIUM'
        else:
            self.criticality = 'LOW'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    @property
    def days_remaining(self):
        if self.amc_expiry_date:
            return (self.amc_expiry_date - timezone.now().date()).days
        return None