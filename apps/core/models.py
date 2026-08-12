"""Media models: a custom image (with alt text) and a first-class Video."""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class CustomImage(AbstractImage):
    """Wagtail image extended with the metadata the frontend needs."""

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Describes the image for screen readers and SEO. Falls back to the title.",
    )
    caption = models.CharField(max_length=255, blank=True)
    credit = models.CharField(max_length=255, blank=True, help_text="Photographer / source credit.")

    admin_form_fields = Image.admin_form_fields + ("alt_text", "caption", "credit")

    search_fields = AbstractImage.search_fields + [
        index.SearchField("caption"),
        index.SearchField("credit"),
    ]

    @property
    def default_alt_text(self):
        return self.alt_text or self.title


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class Video(index.Indexed, models.Model):
    """
    A video asset. Either an uploaded file (self-hosted) or an external URL
    (YouTube / Vimeo / a CDN mp4). Editors pick one; the API tells the frontend
    which kind it got via `source`.
    """

    SOURCE_FILE = "file"
    SOURCE_EMBED = "embed"

    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to="videos/",
        blank=True,
        help_text="MP4 / WebM upload. Leave empty when using an external URL.",
    )
    external_url = models.URLField(
        blank=True,
        help_text="YouTube, Vimeo or a direct CDN video URL. Used when no file is uploaded.",
    )
    poster = models.ForeignKey(
        "core.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Still frame shown before playback.",
    )
    caption = models.CharField(max_length=255, blank=True)
    autoplay = models.BooleanField(default=False)
    loop = models.BooleanField(default=False)
    muted = models.BooleanField(default=True, help_text="Required by browsers for autoplay.")
    show_controls = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(
            [FieldPanel("file"), FieldPanel("external_url")],
            heading="Source (upload a file or paste a URL)",
        ),
        FieldPanel("poster"),
        FieldPanel("caption"),
        MultiFieldPanel(
            [
                FieldPanel("autoplay"),
                FieldPanel("loop"),
                FieldPanel("muted"),
                FieldPanel("show_controls"),
            ],
            heading="Playback defaults",
        ),
    ]

    search_fields = [index.SearchField("title"), index.SearchField("caption")]

    class Meta:
        verbose_name = "video"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def source(self):
        return self.SOURCE_FILE if self.file else self.SOURCE_EMBED

    @property
    def url(self):
        return self.file.url if self.file else self.external_url


register_snippet(Video)
