from crispy_forms.layout import HTML
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import SafeString


class SimpleFieldset(Fieldset):
    @staticmethod
    def get_css_id(fields):
        parts = []
        for field in fields:
            if isinstance(field, Field):
                parts.extend(field.fields)
            elif isinstance(field, str):
                parts.append(field)
        return "_".join(parts)

    def __init__(self, title, *fields, extra=""):
        super().__init__(
            title,
            *fields,
            HTML(extra),
            css_id=f"{self.get_css_id(fields)}_fieldset",
        )

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        fields = self.get_rendered_fields(form, context, template_pack, **kwargs)

        if self.legend:
            legend = format_html("<h4>{}</h4>", self.legend)
        else:
            legend = SafeString("")

        template = self.get_template_name(template_pack)
        context.update({"fieldset": self, "legend": legend, "fields": fields})
        return render_to_string(template, context.flatten())


class CollapsibleFieldset(SimpleFieldset):
    def __init__(self, title, *fields):
        super().__init__(
            title,
            *fields,
            extra='<a class="form-control form-group collapsible"><span class="flex"><span class="value"></span><span class="pen">🖊️</span></span></a>',
        )
