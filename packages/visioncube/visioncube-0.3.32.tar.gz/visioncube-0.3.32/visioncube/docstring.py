#!/usr/bin/env python3

import io
import re

__all__ = [
    'parse_docstring'
]


def parse_docstring(docstring):
    reader = io.StringIO(docstring)
    doc = {}
    state = _short_desc
    while state is not None:
        line = reader.readline()
        state = state(line, doc)
    return doc


def _short_desc(line, doc):
    if not line:
        doc['short_desc'] = ''
        return None

    doc['short_desc'] = line.strip()
    return _long_desc


def _long_desc(line, doc):
    if not line:
        return None

    if re.match(r'^\s*Args:$', line):
        return _args

    line = line.strip()
    if line:
        long_desc = doc.get('long_desc', None)
        doc['long_desc'] = long_desc + '\n' + line if long_desc else line
    return _long_desc


def _args(line, doc):
    if not line:
        return None

    line = line.strip()

    if line == 'Returns:':
        return _returns
    elif m := re.match(r'^(\w[\w_]*)[^:]*:\s*(.*)$', line):
        name, value = m.groups()
        args = doc.get('args', [])
        args.append((name, value))
        doc['args'] = args
        return _arg_item
    else:
        return _args


def _arg_item(line, doc):
    if not line:
        return None

    line = line.strip()
    if line == 'Returns:':
        return _returns
    elif m := re.match(r'^(\w[\w_]*)[^:]*:\s*(.*)$', line):
        name, value = m.groups()
        args = doc.get('args', [])
        args.append((name, value))
        doc['args'] = args
        return _arg_item
    else:
        args = doc.get('args', None)
        if args and line:
            name, value = args[-1]
            args[-1] = (name, value + ' ' + line)
        return _arg_item


def _returns(line, doc):
    if not line:
        return None

    line = line.strip()
    if line:
        returns = doc.get('returns', None)
        doc['returns'] = returns + '\n' + line if returns else line
    return _returns
