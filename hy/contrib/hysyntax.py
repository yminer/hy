"""
   Inspired by PyXL, register.py.
"""
# stdlib
from __future__ import with_statement
from __future__ import print_function
import ast
import cStringIO
import codecs
import encodings
import sys
from encodings import utf_8

# third party
import astor.codegen

# local
from hy.importer import import_buffer_to_hst, incr_import_buffer_to_ast
from hy.lex import tokenize, LexException, PrematureEndOfInput

def hy_transform(stream):
    """
    - read a python code stream
    - extract lisp code
    - generate python ast
    """
    try:
        py_buffer = ""
        lisp_expr = ""
        prv_char = None
        in_lisp = False
        counter = 0
        ctx = {}
        for char in stream.read():
            if not in_lisp and prv_char == "@" and char == "(":
                in_lisp = True
                lisp_expr = "("
                counter += 1
                py_buffer = py_buffer[:-1]
            elif in_lisp:
                lisp_expr += char
                if char == ")":
                    counter -= 1
                elif char == "(":
                    counter += 1
                if counter == 0:
                    in_lisp = False
                    genc, ctx = incr_import_buffer_to_ast(lisp_expr, "none", ctx=ctx)
                    py_buffer += astor.codegen.to_source(genc)
            else:
                py_buffer += char
            prv_char = char
        output = py_buffer
    except Exception as exc:
        print(exc)
        raise

    return output.rstrip()

def hy_transform_string(text):
    stream = cStringIO.StringIO(text)
    return hy_transform(stream)

def hy_decode(input, errors='strict'):
    return utf_8.decode(hy_transform_string(input), errors)

class HyIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            return super(HyIncrementalDecoder, self).decode(
                hy_transform_string(buff), final=True)

class HyStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = cStringIO.StringIO(hy_transform(self.stream))

def search_function(encoding):
    if encoding != 'hy': 
        return None
    # Assume utf8 encoding
    utf8 = encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'hy',
        encode = utf8.encode,
        decode = hy_decode,
        incrementalencoder = utf8.incrementalencoder,
        incrementaldecoder = HyIncrementalDecoder,
        streamreader = HyStreamReader,
        streamwriter = utf8.streamwriter)

codecs.register(search_function)

