from django.test import SimpleTestCase

from apps.cms.models import HomePage


class PageSectionEditorTests(SimpleTestCase):
    def setUp(self):
        self.stream_block = HomePage._meta.get_field("body").stream_block

    def test_sections_are_collapsed_by_default(self):
        self.assertTrue(self.stream_block.meta.collapsed)

    def test_section_picker_uses_clear_categories(self):
        groups = {block.meta.group for block in self.stream_block.child_blocks.values()}

        self.assertEqual(
            groups,
            {
                "Actions & forms",
                "Content & media",
                "Destinations & experiences",
                "Layout",
                "Packages",
                "Page headers",
                "Page templates",
                "Trust & information",
            },
        )
        self.assertNotIn("Sections", groups)
