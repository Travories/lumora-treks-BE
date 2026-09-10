"""
Article body blocks for BlogPostPage.

Unlike the section library (`sections.py`), these are *prose* blocks — the
building units of a single article, rendered by the frontend's `ArticleBody`
component in a narrow reading measure. Each block's API `type` maps 1:1 to the
frontend `BlogBodyBlock` union:

    heading    -> { type: "heading",   text }
    paragraph  -> { type: "paragraph", text }   # rich-text HTML
    quote      -> { type: "quote",     text, cite }
    image      -> { type: "image",     src, alt, caption }
"""

from wagtail import blocks

from apps.core.blocks import APIImageChooserBlock, APIRichTextBlock


class ArticleQuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    cite = blocks.CharBlock(required=False, max_length=160, help_text="Attribution, e.g. a person or source.")

    class Meta:
        icon = "openquote"
        label = "Pull quote"


class ArticleImageBlock(blocks.StructBlock):
    image = APIImageChooserBlock()
    alt = blocks.CharBlock(required=False, max_length=200)
    caption = blocks.CharBlock(required=False, max_length=250)

    class Meta:
        icon = "image"
        label = "Image"

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        image = data.get("image") or {}
        # Flatten to what ArticleBody consumes; keep the full image object too.
        data["src"] = image.get("src") or image.get("url")
        data["alt"] = data.get("alt") or image.get("alt") or ""
        return data


#: StreamField definition shared by the model field and its migration.
ARTICLE_BLOCKS = [
    ("heading", blocks.CharBlock(icon="title", label="Heading", max_length=200)),
    ("paragraph", APIRichTextBlock(label="Paragraph")),
    ("quote", ArticleQuoteBlock()),
    ("image", ArticleImageBlock()),
]
