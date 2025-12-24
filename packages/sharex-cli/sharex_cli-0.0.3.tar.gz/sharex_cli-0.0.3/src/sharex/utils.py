import secrets
import string


def s(to_len: list) -> str:
    return "s" if len(to_len) > 1 else ""


def gen_rand(length: int = 4) -> str:
    r = "".join(secrets.choice(string.ascii_letters) for _ in range(length))
    return "".join(r)


def fmt_bytes(num: float, suffix: str = "B") -> str:
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"
