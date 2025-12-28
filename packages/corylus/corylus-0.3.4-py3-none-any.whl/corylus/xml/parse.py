__all__ = ['parse']

import re
from xml.etree import ElementTree

from ..util.array import array

def parse(input, level=2, root=None, le=[], reduce_whitespace=False):
    if isinstance(le, str): le = le.split(',')
    depth = 0
    stack = []
    if not isinstance(level, int):
        start = array(level)
        level = None
    top = None
    parsing = ElementTree.iterparse(input, events=('start', 'end',))
    for event, element in parsing:
        if event == 'start':
            depth += 1
            if not top:
                if level:
                    top = (depth >= level) and depth
                else:
                    tag = element.tag.rpartition('}')[-1]
                    top = (tag in start) and depth
            if top:
                if len(element.attrib) > 0:
                    value = {}
                    for k, v in element.attrib.items():
                        k = k.rpartition('}')[-1]
                        value[k] = v
                else:
                    value = None
                stack.append(value)
        elif event == 'end':
            if top:
                tag = element.tag.rpartition('}')[-1]
                if depth > top:
                    value = stack.pop()
                    if not isinstance(stack[-1], dict):
                        stack[-1] = {}
                    if value and element.text:
                        text = element.text.strip()
                        if text:
                            value['_'] = re.sub(r'\s+', ' ', text) if reduce_whitespace else text
                    if value is None:
                        value = element.text
                        if value and reduce_whitespace:
                            value = re.sub(r'\s+', ' ', value)
                    if tag not in stack[-1]:
                        stack[-1][tag] = [value] if tag in le else value
                    else:
                        if isinstance(stack[-1][tag], list):
                            stack[-1][tag].append(value)
                        else:
                            stack[-1][tag] = [
                                stack[-1][tag],
                                value
                            ]
                else:
                    top = None
                    value = stack.pop()
                    if root:
                        value[root] = tag
                    yield value
            element.clear()
            depth -= 1
