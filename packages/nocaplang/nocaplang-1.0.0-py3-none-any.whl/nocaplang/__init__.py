"""NoCapLang - A Gen Z slang-based programming language."""

# Version is managed in setup.py
try:
    from importlib.metadata import version
    __version__ = version("nocaplang")
except Exception:
    __version__ = "0.1.8"
