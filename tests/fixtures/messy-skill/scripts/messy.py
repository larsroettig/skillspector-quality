def f(a, b, c, d):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    return a + b + c + d
                else:
                    return a + b + c
            else:
                if d > 0:
                    return a + b + d
                else:
                    return a + b
        else:
            if c > 0:
                return a + c
            else:
                return a
    else:
        if b > 0:
            if c > 0:
                return b + c
            else:
                return b
        else:
            return 0
