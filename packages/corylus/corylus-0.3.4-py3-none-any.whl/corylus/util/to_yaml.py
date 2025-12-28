__all__ = ['to_yaml']

from .with_attrs import with_attrs

@with_attrs(raw_output=True)
def to_yaml(a):
    import json
    import yaml
    from .yaml_dumper import Dumper
    if hasattr(a, 'read'):
        a = json.load(a)
    elif isinstance(a, str):
        a = json.loads(a)
    return yaml.dump(a, Dumper=Dumper, allow_unicode=True, width=1000)
