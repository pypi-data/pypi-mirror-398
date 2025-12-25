# Functions dealing with text

def linewrap(tokens, prefix="", prefix1=None, llen=72):
    """Return string of tokens with lines wrapped at whitespace (generator).

    prefix  : line prefix
    prefix1 : prefix of line 1 (same as prefix if None or unspecified)
    llen    : maximum line length before wrap
    """
    if prefix1 is None:
        prefix1 = prefix
    next_line = prefix1
    first = True
    for token in tokens:
        tlen = len(token)
        if first:
            next_line += token
            first = False
        elif len(next_line) + tlen >= llen:
            yield next_line
            next_line = prefix + token
        else:            
            next_line += " " + token
    yield next_line
    
