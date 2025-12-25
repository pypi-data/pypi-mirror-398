import pdb
from abc import ABCMeta
from abc import abstractmethod

from django.core.management import BaseCommand


class SimpleCommand(BaseCommand, metaclass=ABCMeta):
    """
    A slightly better base class.
    """

    include_base_options = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handle_original = self.handle
        self.handle = self.handle_wrapper

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument(
            "--pdb",
            action="store_true",
            dest="pdb_on_failure",
            help="Enable Pdb on failure.",
        )
        return parser

    def handle_wrapper(self, *args, pdb_on_failure, verbosity, settings, pythonpath, traceback, no_color, force_color, skip_checks=False, **kwargs):
        if self.include_base_options:
            kwargs.update(
                verbosity=verbosity,
                settings=settings,
                pythonpath=pythonpath,
                traceback=traceback,
                no_color=no_color,
                force_color=force_color,
                skip_checks=skip_checks,
            )
        if pdb_on_failure:
            try:
                return self.handle_original(*args, **kwargs)
            except Exception:
                pdb.post_mortem()
        else:
            return self.handle_original(*args, **kwargs)

    @abstractmethod
    def handle(self, *args, **options): ...
