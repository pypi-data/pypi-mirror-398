from .parser import ToonParser

def encode(data, **kwargs):
    return ToonParser.encode(data, **kwargs)

def decode(toon, **kwargs):
    return ToonParser.decode(toon, **kwargs)
