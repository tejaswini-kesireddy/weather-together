import binascii


def hex_encode(securestring: str) -> str:
    """Convert to hexadecimal representation of binary data."""
    return "\\u00" + "\\u00".join(binascii.hexlify(
        data=securestring.encode(encoding="utf-8"), sep="-"
    ).decode(encoding="utf-8").split(sep="-"))


def hex_decode(securestring: str) -> str:
    """Convert to bytes with utf-8 encoding and then decode with unicode escape."""
    return bytes(securestring, "utf-8").decode(encoding="unicode_escape")
