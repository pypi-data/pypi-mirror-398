__all__ = ['deserialize']

import re
from xml.etree import ElementTree

def deserialize(input):
    stack = []
    for event, element in ElementTree.iterparse(input, events=('start', 'end',)):
        match event:
            case 'start':
                stack.append((
                    element.tag.rpartition('}')[-1],
                    {
                        k.rpartition('}')[-1]: v
                        for k, v in element.attrib.items()
                    }
                ))
            case 'end':
                tag, value = stack.pop()
                if element.text and (text := element.text.strip()):
                    value['^text'] = re.sub(r'\s+', ' ', text)
                element.clear()
                node = {tag:value}
                if len(stack) > 0:
                    parent = stack[-1][1]
                    if '^block' not in parent:
                        parent['^block'] = []
                    parent['^block'].append(node)
                else:
                    return node
