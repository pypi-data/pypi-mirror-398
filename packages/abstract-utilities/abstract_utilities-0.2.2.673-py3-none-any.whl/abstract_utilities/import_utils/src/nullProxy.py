from ...imports import *
lazy_import_logger = logging.getLogger("abstract.lazy_import")
class nullProxy:
    """
    Safe, chainable, callable placeholder for missing modules/attributes.
    """

    def __init__(self, name, path=()):
        self._name = name
        self._path = path

    def __getattr__(self, attr):
        return nullProxy(self._name, self._path + (attr,))

    def __call__(self, *args, **kwargs):
        lazy_import_logger.warning(
            "[lazy_import] Call to missing module/attr: %s.%s args=%s kwargs=%s",
            self._name,
            ".".join(self._path),
            args,
            kwargs,
        )
        return None

    def __repr__(self):
        full = ".".join((self._name, *self._path))
        return f"<nullProxy {full}>"

    def __bool__(self):
        return False  # safe in conditionals
