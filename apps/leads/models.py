"""Enquiry / newsletter submissions captured from the frontend forms."""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class LeadSubmission(models.Model):
    """
    One submission from a `lead_form` block or the footer newsletter.

    Known fields are stored in columns so the admin listing is readable; any
    extra fields the editor added to the form are kept in `data`.
    """

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("converted", "Converted"),
        ("spam", "Spam"),
    ]

    form_key = models.CharField(max_length=60, default="enquiry", db_index=True)
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="All submitted fields.")

    page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    source_url = models.URLField(blank=True)
    package = models.ForeignKey(
        "catalog.Package", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("form_key"), FieldPanel("status"), FieldPanel("notes")], heading="Handling"
        ),
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("email"), FieldPanel("phone"), FieldPanel("message")],
            heading="Contact",
        ),
        FieldPanel("data", read_only=True),
        MultiFieldPanel(
            [FieldPanel("source_url"), FieldPanel("page"), FieldPanel("package")], heading="Origin"
        ),
    ]

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "lead submission"

    def __str__(self):
        who = self.name or self.email or "Anonymous"
        return f"{who} — {self.form_key}"
