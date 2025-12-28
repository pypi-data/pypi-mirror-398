__all__ = ['Dumper']

from collections import OrderedDict
import yaml
from inceptum import config

class Dumper(yaml.SafeDumper):
    def represent_scalar(self, tag, value, style=None):
        if style is None and isinstance(value, str) and '\n' in value:
            style = '|'
            value = '\n'.join(line.rstrip() for line in value.split('\n'))
            #value = value.replace('\t', '    ') # Pyyaml does not allow tab in a block string
        return super().represent_scalar(tag, value, style)

    def represent_mapping(self, tag, value):
        return super().represent_mapping(
            tag,
            (
                (key, value[key])
                for key in
                sorted(value.keys(), key=self.order)
            )
        )

    order_begin = config('corylus.yaml.order.begin', default=[])
    order_end = config('corylus.yaml.order.end', default=[])

    def order(self, key):
        if key in self.order_begin:
            return f" {self.order_begin.index(key):02d}"
        elif key in self.order_end:
            return f"~{self.order_end.index(key):02d}"
        else:
            return key
