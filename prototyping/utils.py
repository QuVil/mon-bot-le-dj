
def string_or_none(string: str) -> object:
    return string if string else None

def as_real_or_none(string: str) -> object:
    try: return float(string.replace(',', '.'))
    except: return None