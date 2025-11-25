from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model
from ticket.models import Department

User = get_user_model()







class ChangeRequest(models.Model):
    """
    Generic Inter-Department Change Request System
    Following ITIL Change Management Guidelines
    """

    # --- ITIL Change Types ---
    CHANGE_TYPE_CHOICES = [
        ('STANDARD', 'मानक परिवर्तन (Standard Change)'),
        ('NORMAL', 'सामान्य परिवर्तन (Normal Change)'),
        ('EMERGENCY', 'आपतकालीन परिवर्तन (Emergency Change)'),
    ]

    # --- Request Categories (Generic for all departments) ---
    CATEGORY_CHOICES = [
        # Life-Insurance Specific (Top 5)
        ('UNDERWRITING_ISSUE', 'बीमालेखन समस्या (Underwriting Issue)'),
        ('CLAIM_PROCESSING_ISSUE', 'दाबी प्रसोधन समस्या (Claim Processing Issue)'),
        ('PREMIUM_ACCOUNTING_ISSUE', 'प्रिमियम / लेखा समस्या (Premium & Accounting Issue)'),
        ('POLICY_SERVICE_ISSUE', 'पोलिसी सेवा समस्या (Policy Servicing Issue)'),
        ('AGENT_PORTAL_ISSUE', 'अभिकर्ता पोर्टल / आयोग समस्या (Agent Portal / Commission Issue)'),

        # General Office IT Issues (Added 3)
        ('NETWORK_ISSUE', 'नेटवर्क / इन्टरनेट समस्या (Network/Internet Issue)'),
        ('PRINTER_ISSUE', 'प्रिन्टर / स्क्यानर समस्या (Printer/Scanner Issue)'),
        ('GENERAL_OFFICE_ISSUE', 'सामान्य अफिस समस्या (General Office Issue)'),
    ]

    # --- Priority Levels ---
    PRIORITY_CHOICES = [
        ('LOW', 'न्यून (Low)'),
        ('MEDIUM', 'मध्यम (Medium)'),
        ('HIGH', 'उच्च (High)'),
        ('CRITICAL', 'अत्यन्त जरुरी (Critical)'),
    ]

    # --- ITIL Status Workflow ---
    STATUS_CHOICES = [
        ('DRAFT', 'मस्यौदा (Draft)'),
        ('SUBMITTED', 'पेश गरिएको (Submitted)'),
        ('UNDER_REVIEW', 'समीक्षाधीन (Under Review)'),
        ('APPROVED', 'स्वीकृत (Approved)'),
        ('REJECTED', 'अस्वीकृत (Rejected)'),
        ('IN_PROGRESS', 'कार्यान्वयनमा (In Progress)'),
        ('PENDING_INFO', 'जानकारी बाँकी (Pending Information)'),
        ('ON_HOLD', 'रोकिएको (On Hold)'),
        ('COMPLETED', 'सम्पन्न (Completed)'),
        ('CLOSED', 'बन्द गरिएको (Closed)'),
        ('CANCELLED', 'रद्द गरिएको (Cancelled)'),
    ]

    # --- Impact Assessment (ITIL) ---
    IMPACT_CHOICES = [
        ('LOW', 'न्यून प्रभाव (Low Impact)'),
        ('MEDIUM', 'मध्यम प्रभाव (Medium Impact)'),
        ('HIGH', 'उच्च प्रभाव (High Impact)'),
        ('CRITICAL', 'गम्भीर प्रभाव (Critical Impact)'),
    ]

    # --- Risk Level (ITIL) ---
    RISK_CHOICES = [
        ('LOW', 'न्यून जोखिम (Low Risk)'),
        ('MEDIUM', 'मध्यम जोखिम (Medium Risk)'),
        ('HIGH', 'उच्च जोखिम (High Risk)'),
        ('VERY_HIGH', 'अति उच्च जोखिम (Very High Risk)'),
    ]

    # ============= CORE FIELDS =============

    # Request Identification
    request_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="अनुरोध नं (Request Number)"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="शीर्षक"
    )

    description = HTMLField(
        verbose_name="विस्तृत विवरण",
        help_text="समस्या वा आवश्यकताको पूर्ण विवरण"
    )

    # Department Routing (Generic)
    from_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='outgoing_requests',
        verbose_name="अनुरोध गर्ने विभाग "
    )

    to_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='incoming_requests',
        verbose_name="अनुरोध प्राप्त गर्ने विभाग"
    )

    # Request Classification
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        default='NORMAL',
        verbose_name="परिवर्तनको प्रकार"
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        verbose_name="श्रेणी ",
        blank=True,
        null=True
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        verbose_name="प्राथमिकता (Priority)"
    )

    # ============= ITIL SPECIFIC FIELDS =============

    business_justification = models.TextField(
        verbose_name="व्यावसायिक औचित्य (Business Justification)",
        help_text="यो परिवर्तन किन आवश्यक छ?",
        blank=True,
        null=True
    )

    impact_assessment = models.CharField(
        max_length=10,
        choices=IMPACT_CHOICES,
        default='MEDIUM',
        verbose_name="प्रभाव मूल्यांकन (Impact Assessment)",
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default='MEDIUM',
        verbose_name="जोखिम स्तर (Risk Level)"
    )

    affected_systems = models.TextField(
        blank=True,
        verbose_name="प्रभावित प्रणालीहरू (Affected Systems)",
        help_text="कुन प्रणाली वा मोड्युलहरू प्रभावित हुन्छन्?"
    )

    rollback_plan = HTMLField(
        blank=True,
        verbose_name="फिर्ता योजना (Rollback Plan)",
        help_text="समस्या भएमा पहिलेको अवस्थामा फर्कने योजना"
    )

    # Reference Data
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="सन्दर्भ नं",
        help_text="Policy/Claim/Contract Number/RoomNo/Your location आदि"
    )

    # Data Modification Specifics
    current_value = models.TextField(
        blank=True,
        verbose_name="हालको विवरण (Current Value)"
    )

    proposed_value = models.TextField(
        blank=True,
        verbose_name="प्रस्तावित विवरण (Proposed Value)"
    )

    # Compliance & Security
    data_privacy_confirmed = models.BooleanField(
        default=False,
        verbose_name="गोपनीयता पुष्टि (Data Privacy Confirmed)",
        help_text="म तथ्याङ्कको गोपनीयता कायम राख्ने घोषणा गर्दछु"
    )

    regulatory_compliance_check = models.BooleanField(
        default=False,
        verbose_name="नियामक अनुपालन (Regulatory Compliance)",
        help_text="NRB/Regulatory requirements पूरा भएको छ?"
    )

    # ============= WORKFLOW & STATUS =============

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="अवस्था (Status)"
    )

    # User Tracking
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_requests',
        verbose_name="अनुरोधकर्ता (Requested By)"
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        verbose_name="जिम्मेवार व्यक्ति (Assigned To)"
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name="समीक्षक (Reviewed By)"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests',
        verbose_name="स्वीकृतकर्ता (Approved By)"
    )

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_requests',
        verbose_name="पूर्णकर्ता (Completed By)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="सिर्जना मिति (Created At)"
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="पेश गरेको मिति (Submitted At)"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="समीक्षा मिति (Reviewed At)"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="स्वीकृति मिति (Approved At)"
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="सुरु मिति (Started At)"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="सम्पन्न मिति (Completed At)"
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="बन्द गरेको मिति (Closed At)"
    )

    # Expected Timeline
    expected_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="अपेक्षित पूर्णता मिति (Expected Completion)"
    )

    # Response & Resolution
    response_notes = models.TextField(
        blank=True,
        verbose_name="प्रतिक्रिया टिप्पणी (Response Notes)",
        help_text="विभागको प्रतिक्रिया वा टिप्पणी"
    )

    resolution_details = models.TextField(
        blank=True,
        verbose_name="समाधान विवरण (Resolution Details)",
        help_text="अनुरोध कसरी पूरा गरियो"
    )

    closure_notes = models.TextField(
        blank=True,
        verbose_name="बन्द गर्ने टिप्पणी (Closure Notes)"
    )

    # Attachments (file upload - optional)
    attachment = models.FileField(
        upload_to='change_requests/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="संलग्नक (Attachment)"
    )

    # Metadata
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name="अन्तिम परिमार्जन (Last Modified)"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Register Change Request)"
        verbose_name_plural = "1. Register Issue (अनुरोध गर्नुहोस)"
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['from_department', 'to_department']),
            models.Index(fields=['request_number']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate request number
        if not self.request_number:
            last_request = ChangeRequest.objects.order_by('-id').first()
            if last_request:
                last_num = int(last_request.request_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.request_number = f"CR-{timezone.now().year}-{new_num:05d}"

        super().save(*args, **kwargs)

    # def clean(self):
    #     """Validation rules"""
    #     if self.from_department == self.to_department:
    #         raise ValidationError("अनुरोध गर्ने र प्राप्त गर्ने विभाग फरक हुनुपर्छ।")
    #
    #     if self.category == 'DATA_MODIFICATION':
    #         if not self.current_value or not self.proposed_value:
    #             raise ValidationError(
    #                 "तथ्याङ्क परिमार्जनको लागि हालको र प्रस्तावित विवरण अनिवार्य छ।"
    #             )


class RequestHistory(models.Model):
    """
    Complete audit trail for all changes to a request
    Tracks every status change, field modification, and action
    """

    ACTION_CHOICES = [
        ('CREATED', 'सिर्जना गरियो (Created)'),
        ('SUBMITTED', 'पेश गरियो (Submitted)'),
        ('ASSIGNED', 'जिम्मेवारी दियो (Assigned)'),
        ('STATUS_CHANGED', 'अवस्था परिवर्तन (Status Changed)'),
        ('UPDATED', 'अद्यावधिक गरियो (Updated)'),
        ('COMMENTED', 'टिप्पणी थपियो (Commented)'),
        ('APPROVED', 'स्वीकृत गरियो (Approved)'),
        ('REJECTED', 'अस्वीकृत गरियो (Rejected)'),
        ('COMPLETED', 'सम्पन्न गरियो (Completed)'),
        ('CLOSED', 'बन्द गरियो (Closed)'),
        ('REOPENED', 'पुन: खोलियो (Reopened)'),
    ]

    request = models.ForeignKey(
        ChangeRequest,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="अनुरोध (Request)"
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="कार्य (Action)"
    )

    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="गर्ने व्यक्ति (Performed By)"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="समय (Timestamp)"
    )

    old_value = models.TextField(
        blank=True,
        verbose_name="पुरानो मूल्य (Old Value)"
    )

    new_value = models.TextField(
        blank=True,
        verbose_name="नयाँ मूल्य (New Value)"
    )

    field_changed = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="परिवर्तन क्षेत्र (Field Changed)"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="टिप्पणी (Notes)"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "अनुरोध इतिहास (Request History)"
        verbose_name_plural = "अनुरोध इतिहासहरू (Request Histories)"

    def __str__(self):
        return f"{self.request.request_number} - {self.get_action_display()} by {self.performed_by}"


class RequestComment(models.Model):
    """
    Comments and discussions on change requests
    """

    request = models.ForeignKey(
        ChangeRequest,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="अनुरोध (Request)"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="प्रयोगकर्ता (User)"
    )

    comment = models.TextField(
        verbose_name="टिप्पणी (Comment)"
    )

    is_internal = models.BooleanField(
        default=False,
        verbose_name="आन्तरिक टिप्पणी (Internal Comment)",
        help_text="केवल विभागीय कर्मचारीलाई देखिने"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="सिर्जना मिति (Created At)"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = "टिप्पणी (Comment)"
        verbose_name_plural = "टिप्पणीहरू (Comments)"

    def __str__(self):
        return f"Comment by {self.user} on {self.request.request_number}"


class RequestAttachment(models.Model):
    """
    Multiple file attachments for a request
    """

    request = models.ForeignKey(
        ChangeRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="अनुरोध (Request)"
    )

    file = models.FileField(
        upload_to='request_attachments/%Y/%m/',
        verbose_name="फाइल (File)"
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="विवरण (Description)"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="अपलोड गर्ने (Uploaded By)"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="अपलोड मिति (Uploaded At)"
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "संलग्नक (Attachment)"
        verbose_name_plural = "संलग्नकहरू (Attachments)"

    def __str__(self):
        return f"{self.file.name} - {self.request.request_number}"