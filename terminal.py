def clearscreen():
    return "\033[2J\033[H"

def clearline():
    return "\033[K\033[A"

def setCursorLine(num):
    return f"\033[{num}C"

def mvCursorVerticle(num):
    """ +ve value moves up -ve down """
    return f"\033[{num}A" if num > 0 else f"\033[{-num}B"

def clearEverythingAfter():
    return "\033[J"
