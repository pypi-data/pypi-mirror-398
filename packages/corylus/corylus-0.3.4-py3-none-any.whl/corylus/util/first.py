__all__ = ['first']

def first(a):
    match a:
        case [head, *tail]:
            return head
        case []:
            return None
        case _:
            return a
