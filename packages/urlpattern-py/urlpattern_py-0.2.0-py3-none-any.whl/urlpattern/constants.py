# Internal constants for URLPattern implementation.

SPECIAL_SCHEMES = {
    "ftp": 21,
    "file": None,
    "http": 80,
    "https": 443,
    "ws": 80,
    "wss": 443,
}

_CONTROL_WHITESPACE_STRIP = str.maketrans("", "", "\t\n\r")

_COMPONENTS = [
    "protocol",
    "username",
    "password",
    "hostname",
    "port",
    "pathname",
    "search",
    "hash",
]
