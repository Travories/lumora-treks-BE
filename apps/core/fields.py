"""
Text fields with an editorial length limit.

`ui_max_length` is the longest text the frontend layout is designed for. It is
enforced by admin forms (which also render the live character counter, see
static/lumora_admin/char-count.js) and by model validation. The database
column keeps its own, larger `max_length`, so tightening a limit never needs a
schema change — and never fails a migration on existing longer content, which
editors simply shorten the next time they save.
"""

from django.core.validators import MaxLengthValidator
from django.db import models


class UIMaxLengthMixin:
    def __init__(self, *args, ui_max_length=None, **kwargs):
        self.ui_max_length = ui_max_length
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        if self.ui_max_length:
            kwargs["max_length"] = self.ui_max_length
        return super().formfield(**kwargs)

    def run_validators(self, value):
        super().run_validators(value)
        if self.ui_max_length and value not in self.empty_values:
            MaxLengthValidator(self.ui_max_length)(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.ui_max_length:
            kwargs["ui_max_length"] = self.ui_max_length
        return name, path, args, kwargs


class LimitedCharField(UIMaxLengthMixin, models.CharField):
    pass


class LimitedTextField(UIMaxLengthMixin, models.TextField):
    pass
