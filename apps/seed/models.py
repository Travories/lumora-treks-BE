from django.db import models


class SeedRun(models.Model):
    """
    Records that the database holds a clean seed of a specific version of the
    seed content, so a restart with `SEED_DATABASE=true` doesn't wipe and
    re-seed the same data again.
    """

    fingerprint = models.CharField(max_length=64, help_text="SHA-256 of the seed content and media.")
    summary = models.JSONField(default=dict, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        get_latest_by = "applied_at"

    def __str__(self):
        return f"Seed {self.fingerprint[:12]} ({self.applied_at:%Y-%m-%d %H:%M})"
