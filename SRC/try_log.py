from functools import wraps
import logging

logger = logging.getLogger(__name__)


def log_exceptions(_fn=None, *, name: str | None = None, reraise: bool = False):
    # поддержка формы @log_exceptions("текст")
    if _fn is not None and not callable(_fn):
        name = str(_fn)
        _fn = None

    def _decorate(fn):
        @wraps(fn)
        def w(*a, **k):
            try:
                need = fn.__code__.co_argcount
                return fn(*a[:need], **k)
            except Exception:
                logger.exception(name or fn.__qualname__)
                if reraise:
                    raise

        return w

    # @log_exceptions          -> _fn is function
    if callable(_fn):
        return _decorate(_fn)
    # @log_exceptions(...)     -> вернуть декоратор
    return _decorate
