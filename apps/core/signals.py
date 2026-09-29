"""Pre-generate the display rendition when an image is saved.

The API serves every image through `DISPLAY_RENDITION`; creating it here
(after the upload commits) means the first page to show a new image doesn't
pay for downloading, resizing and re-uploading it.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import CustomImage
from apps.core.serializers import DISPLAY_RENDITION

logger = logging.getLogger(__name__)


def generate_display_rendition(image):
    try:
        image.get_rendition(DISPLAY_RENDITION)
    except Exception:  # a broken upload must never fail the save that triggered this
        logger.warning("Could not pre-generate the display rendition for image %s", image.pk, exc_info=True)


@receiver(post_save, sender=CustomImage, dispatch_uid="core_image_display_rendition")
def pregenerate_display_rendition(sender, instance, **kwargs):
    transaction.on_commit(lambda: generate_display_rendition(instance))
