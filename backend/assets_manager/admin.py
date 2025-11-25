from django.contrib import admin
from django.utils.html import format_html
from .models import ITAsset


@admin.register(ITAsset)
class ITAssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_tag',
        'name_display',
        'category',
        'department',
        'fiscal_year',
        'criticality_badge',
        'license_status',
        'ip_address',
    )

    list_filter = (
        'category',
        'status',
        'fiscal_year',
        'criticality',
        'department',
        'procurement_method'
    )

    search_fields = ('name', 'asset_tag', 'custodian', 'invoice_no', 'ip_address')

    readonly_fields = ('risk_score', 'criticality')

    fieldsets = (
        ('आधारभूत विवरण (Basic Info)', {
            'fields': ('asset_tag', 'name', 'ip_address', 'category', 'status', 'specs')
        }),
        ('खरिद विवरण (Procurement - PPA 2063)', {
            'fields': (
                ('fiscal_year', 'procurement_method'),
                ('purchase_date', 'cost'),
                ('vendor_name', 'invoice_no')
            ),
            'classes': ('collapse',),  # Collapsed to save space
        }),
        ('जोखिम विश्लेषण (Risk & IS Audit)', {
            'description': 'Based on CIA Triad (Confidentiality, Integrity, Availability)',
            'fields': (('confidentiality', 'integrity', 'availability'), ('risk_score', 'criticality'))
        }),
        ('लाइसेन्स र म्याद (License & Expiry)', {
            'fields': ('amc_expiry_date',)
        }),
        ('जिम्मेवारी (Ownership)', {
            'fields': ('department', 'custodian', 'location')
        }),
    )

    def name_display(self, obj):
        return format_html('<b>{}</b>', obj.name)

    name_display.short_description = "Asset Name"

    def criticality_badge(self, obj):
        """Auto-colors High Risk items for Auditors"""
        colors = {
            'HIGH': '#d9534f',  # Red
            'MEDIUM': '#f0ad4e',  # Orange
            'LOW': '#5cb85c',  # Green
        }
        color = colors.get(obj.criticality, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            color, obj.criticality
        )

    criticality_badge.short_description = "Risk Level"

    def license_status(self, obj):
        """Logic for AMC/License Expiry Alerts"""
        if not obj.amc_expiry_date:
            return "-"

        days = obj.days_remaining

        if days < 0:
            return format_html('<span style="color: red; font-weight: bold;">EXPIRED ({} days)</span>', abs(days))
        elif days <= 45:  # 45 days is standard Gov notification period
            return format_html('<span style="color: orange; font-weight: bold;">Expiring in {} days</span>', days)
        else:
            return format_html('<span style="color: green;">Valid ({} days)</span>', days)

    license_status.short_description = "License/AMC"