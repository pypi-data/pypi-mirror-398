class ArgcompleteWrapper:
    def __init__(self):
        self.directories = None
        self.argcomplete_module = None

        try:
            import argcomplete  # type: ignore # noqa: F401

            self.argcomplete_module = argcomplete
        except ImportError:
            return

        self.directories = argcomplete.completers.DirectoriesCompleter()

    def files(self, allowed_extensions=[]):
        if not self.argcomplete_module:
            return None

        argcomplete = self.argcomplete_module

        return argcomplete.completers.FilesCompleter(allowed_extensions)

    def init(self, parser):
        if not self.argcomplete_module:
            return

        argcomplete = self.argcomplete_module

        argcomplete.autocomplete(parser)


_singleton: ArgcompleteWrapper | None = None


def completion() -> ArgcompleteWrapper:
    global _singleton
    if _singleton is None:
        _singleton = ArgcompleteWrapper()
    return _singleton
