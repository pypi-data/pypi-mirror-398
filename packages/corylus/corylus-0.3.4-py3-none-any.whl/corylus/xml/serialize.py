__all__ = ['serialize']

from html import escape
import json

from ..util.array import array

html_close = {
    'link': False,
    'meta': False,
}

def serialize(a, close=None, indent=False, indentation=None, html=False, preamble=True):
    match preamble:
        case True:
            yield '<!DOCTYPE html>' if html else '<?xml version="1.0" encoding="UTF-8"?>'
        case str(s):
            yield s
    if preamble and indent: yield '\n'
    if html and close is None: close = html_close
    if indent:
        if not indentation: indentation = '  '
        indent = ''
    else:
        indent = indentation = ''
    for node in array(a):
        yield from serialize_node(node, close, indent, indentation)

def serialize_node(node, close, indent, indentation):
    if indentation: yield indent
    yield '<'
    match node:
        case {'tag':tag}:
            yield tag.replace('~', ':')
            yield from serialize_attributes(node.get('attributes'))
            yield '>\n' if indentation else '>'
            for n in node.get('nodes', []):
                yield from serialize_node(n, close, indent + indentation, indentation)
            yield from serialize_close(node['tag'], True, indent, indentation, close)
        case _:
            tag = next(iter(node))
            value = node[tag]
            yield tag.replace('~', ':')
            match value:
                case {'attributes': dict(attributes), 'nodes': list(nodes)}:
                    yield from serialize_attributes(attributes)
                    yield '>'
                    if indentation: yield '\n'
                    for n in nodes:
                        yield from serialize_node(n, close, indent + indentation, indentation)
                    yield from serialize_close(tag, True, indent, indentation, close)
                case dict(attributes):
                    yield from serialize_attributes(attributes)
                    if block := attributes.get('^block'):
                        yield '>'
                        if indentation: yield '\n'
                        for n in array(block):
                            yield from serialize_node(n, close, indent + indentation, indentation)
                        yield from serialize_close(tag, True, indent, indentation, close)
                    elif text := attributes.get('^text'):
                        yield '>'
                        yield text
                        yield from serialize_close(tag, False, indent, indentation, close)
                    else:
                        yield from serialize_close(tag, None, indent, indentation, close)
                case list(nodes):
                    yield '>'
                    if indentation: yield '\n'
                    for n in nodes:
                        yield from serialize_node(n, close, indent + indentation, indentation)
                    yield from serialize_close(tag, True, indent, indentation, close)
                case _:
                    yield '>'
                    yield value
                    yield from serialize_close(tag, False, indent, indentation, close)

def serialize_attributes(a):
    for key, value in (a or {}).items():
        if not key.startswith('^'):
            yield ' '
            yield key.replace('~', ':')
            if value != True:
                yield '="'
                yield escape(str(value), quote=True)
                yield '"'

def serialize_close(key, content, indent, indentation, close):
    if content is not None:
        if indentation:
            if content: yield indent
            yield '</'
            yield key.replace('~', ':')
            yield '>\n'
        else:
            yield '</'
            yield key.replace('~', ':')
            yield '>'
    else:
        if close:
            if isinstance(close, dict) and close.get(key) == False:
                yield '>'
            else:
                yield '></'
                yield key.replace('~', ':')
                yield '>'
        else:
            yield '/>'
        if indentation: yield '\n'
