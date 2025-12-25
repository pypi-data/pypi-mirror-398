from django import forms


class OpaqueWidget(forms.MultiWidget):
    template_name = "forms/widgets/opaquewidget.html"

    def __init__(self, data_widget, display_value):
        self.display_value = display_value
        super().__init__([forms.HiddenInput, data_widget])

    def decompress(self, value):
        return [self.display_value(value), None]


UNSPECIFIED = object()


class OpaqueField(forms.MultiValueField, forms.FileField):
    """
    Suggested usage, assuming the model field does some encrypting in get_db_prep_value::

        class OpaqueCreditCardNumberField(OpaqueField):
            validator_field = CreditCardNumberField(required=False)
            value_widget = validator_field.widget
            value_field = forms.CharField

            def clean_value(self, value):
                return self.validator_field.clean(value)

            def display_value(self, value):
                return f'encrypted to {len(value)} character payload'
    """

    value_widget: type
    value_field: type

    def __init__(self, required=UNSPECIFIED, widget=UNSPECIFIED, disabled=UNSPECIFIED, **kwargs):
        if not (required is UNSPECIFIED or required):
            raise TypeError("Cannot make this field not mandatory.")
        if widget is not UNSPECIFIED:
            raise TypeError("Cannot override widget.")
        if not (disabled is UNSPECIFIED or not disabled):
            raise TypeError("Cannot disable this field.")
        super().__init__(
            fields=[forms.CharField(required=False), self.value_field(required=False)],
            widget=OpaqueWidget(self.value_widget, self.display_value),
            required=False,
            require_all_fields=False,
            **kwargs,
        )

    def compress(self, data_list):
        if data_list:
            _, data = data_list
            return self.clean_value(data)

    def clean(self, value, initial=None):
        return super().clean(value) or initial

    def clean_value(self, value):
        raise NotImplementedError

    def display_value(self, value):
        raise NotImplementedError
