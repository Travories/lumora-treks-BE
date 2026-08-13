from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.leads.models import LeadSubmission


class AnonymousLeadApiTests(TestCase):
    @patch("apps.core.api.views.LeadCreateView._notify")
    def test_anonymous_traveler_can_submit_an_enquiry(self, notify):
        response = APIClient().post(
            "/api/v2/leads/",
            {
                "form_key": "enquiry",
                "name": "Maya Gurung",
                "email": "maya@example.com",
                "message": "Is this departure available?",
                "consent": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["ok"])
        lead = LeadSubmission.objects.get(pk=response.data["id"])
        self.assertEqual(lead.email, "maya@example.com")
        notify.assert_called_once()

