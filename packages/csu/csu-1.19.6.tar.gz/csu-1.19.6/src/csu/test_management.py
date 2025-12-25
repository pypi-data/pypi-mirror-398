from unittest.mock import call

import pytest

from csu.management import SimpleCommand

junk = dict.fromkeys(["verbosity", "settings", "pythonpath", "traceback", "no_color", "force_color", "skip_checks"])


def test_command_abstract():
    class Bad(SimpleCommand):
        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class Bad without an implementation for abstract method 'handle'"):
        Bad()


def test_command_subclass():
    class Ok(SimpleCommand):
        def handle(self, foo):
            return foo

    class MaybeOk(Ok):
        def handle(self, foo):
            return super().handle(foo)

    assert Ok().handle(1, pdb_on_failure=False, **junk) == 1
    assert MaybeOk().handle(1, pdb_on_failure=False, **junk) == 1


def test_command_full():
    class Full(SimpleCommand):
        include_base_options = True

        def handle(self, foo, **kwargs):
            return foo, kwargs

    assert Full().handle(1, pdb_on_failure=False, **junk) == (1, junk)


def test_command_pdb(mocker):
    mock = mocker.patch("pdb.post_mortem")

    class Full(SimpleCommand):
        include_base_options = True

        def handle(self, foobar, **kwargs):
            pass

    assert Full().handle(foo=1, pdb_on_failure=True, **junk) is None
    assert mock.call_args_list == [call()]
