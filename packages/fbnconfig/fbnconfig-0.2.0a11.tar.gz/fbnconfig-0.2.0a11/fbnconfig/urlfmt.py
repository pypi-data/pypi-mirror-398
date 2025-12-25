from string import Formatter
from urllib.parse import quote


class Urlfmt(Formatter):

    def __init__(self, base_path):
        self.base = base_path

    def get_value(self, field_name, *args, **kwargs):
        if field_name == "base":
            return self.base
        return super().get_value(field_name, *args, **kwargs)

    def format_field(self, value, format_spec):
        if value is self.base:
            return super().format_field(value, "")
        else:
            return quote(super().format_field(value, format_spec), safe=[])
