import sys

from enum import Enum
from io import TextIOBase
from re import compile as REGEX


class Color(Enum):
    FG = ("FG", 30)
    BG = ("BG", 40)

    def __new__(cls, name, base):
        colors = {
            "black": 0,
            "red": 1,
            "green": 2,
            "yellow": 3,
            "blue": 4,
            "magenta": 5,
            "cyan": 6,
            "white": 7,
            "default": 9,
        }

        class ANSIColor(Enum):
            def __str__(self):
                base, code = self.value
                return f"\033[{base + code}m"

        obj = object.__new__(cls)
        obj._value_ = ANSIColor(
            name,
            {key: (base, val) for key, val in colors.items()}
        )
        return obj

    def __getattr__(self, name):
        return getattr(self.value, name)

    def __getitem__(self, name):
        return getattr(self.value, name)

# pylint: disable=invalid-name,no-member


class Tag(Enum):
    B = 1
    U = 4
    F = Color.FG
    K = Color.BG
    b = 22
    u = 24
    f = Color.FG.default
    k = Color.BG.default
    r = 0

    def __str__(self):
        if isinstance(self.value, int):
            return f"\033[{self.value}m"
        if isinstance(self.value, Color):
            return str(self.value.value)
        return str(self.value)

    def _proxy_enum(self, name, operation):
        try:
            value = object.__getattribute__(self, "_value_")
        except AttributeError:
            raise AttributeError(name) from None

        if isinstance(value, Enum):
            try:
                return operation(value, name)
            except (AttributeError, KeyError, TypeError) as exc:
                raise AttributeError(name) from exc
        raise AttributeError(name)

    def __getattr__(self, name):
        # pylint: disable=unnecessary-lambda
        return self._proxy_enum(name, lambda obj, attr: getattr(obj, attr))

    def __getitem__(self, name):
        return self._proxy_enum(name, lambda obj, key: obj[key])

    @classmethod
    def __call__(cls, name):
        return cls.tag(name)

    @classmethod
    def format(cls, text: str, tty: bool = True) -> str:
        pattern = REGEX(
            r"%%(?=[RBUbufkrFK](?:\[|[^a-zA-Z])?)"
            r"|%(?:([RBUbufkr])|([FK])\[(\w+)\])"
        )

        def replace(match):
            if match.group(0).startswith("%%"):
                return match.group(0)[1:]

            simple, color_tag, color = match.groups()

            if color_tag:
                try:
                    code = getattr(cls, color_tag)[color]
                except (AttributeError, KeyError, TypeError):
                    return match.group(0)
            else:
                code = cls[simple]

            return str(code) if tty else ""

        return pattern.sub(replace, text)


class ColorStream(TextIOBase):
    def __init__(self, stream=None, enabled=None):
        super().__init__()
        self.stream = stream if stream is not None else sys.stdout
        self.enabled = (
            self.stream.isatty() if enabled is None else enabled
        )

    def write(self, text: str) -> int:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if not isinstance(text, str):
            raise TypeError("write() argument must be str")

        self.stream.write(Tag.format(text, tty=self.enabled))
        return len(text)

    def flush(self):
        if not self.closed:
            self.stream.flush()

    def isatty(self):
        return self.stream.isatty()

    def fileno(self):
        return self.stream.fileno()

    def writable(self):
        return not self.closed and self.stream.writable()

    def readable(self):
        return False

    def seekable(self):
        return False

    @property
    def encoding(self):
        return self.stream.encoding

    @property
    def errors(self):
        return self.stream.errors

    @property
    def name(self):
        return self.stream.name

    def close(self):
        if not self.closed:
            self.flush()
            super().close()

    def __getattr__(self, name):
        return getattr(self.stream, name)


stdout = ColorStream(sys.stdout)
stderr = ColorStream(sys.stderr)
# vim: ts=4:et:
