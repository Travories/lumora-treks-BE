from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.leads.models import LeadSubmission


class Command(BaseCommand):
    help = "Delete lead submissions older than the configured retention period."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=730)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        days = max(options["days"], 1)
        cutoff = timezone.now() - timedelta(days=days)
        queryset = LeadSubmission.objects.filter(submitted_at__lt=cutoff)
        count = queryset.count()
        if count and not options["dry_run"]:
            queryset.delete()
        action = "Would remove" if options["dry_run"] else "Removed"
        self.stdout.write(self.style.SUCCESS(f"{action} {count} lead submission(s) older than {days} days."))
