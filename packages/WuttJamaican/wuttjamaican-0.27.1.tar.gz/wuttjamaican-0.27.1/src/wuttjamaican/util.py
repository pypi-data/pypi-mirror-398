# -*- coding: utf-8; -*-
################################################################################
#
#  WuttJamaican -- Base package for Wutta Framework
#  Copyright © 2023-2025 Lance Edgar
#
#  This file is part of Wutta Framework.
#
#  Wutta Framework is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Wutta Framework is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  Wutta Framework.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
"""
WuttJamaican - utilities
"""

import datetime
import importlib
import logging
import os
import shlex
import warnings

from uuid_extensions import uuid7


log = logging.getLogger(__name__)


# nb. this is used as default kwarg value in some places, to
# distinguish passing a ``None`` value, vs. *no* value at all
UNSPECIFIED = object()


def get_class_hierarchy(klass, topfirst=True):
    """
    Returns a list of all classes in the inheritance chain for the
    given class.

    For instance::

       class A:
          pass

       class B(A):
          pass

       class C(B):
          pass

       get_class_hierarchy(C)
       # -> [A, B, C]

    :param klass: The reference class.  The list of classes returned
       will include this class and all its parents.

    :param topfirst: Whether the returned list should be sorted in a
       "top first" way, e.g. A) grandparent, B) parent, C) child.
       This is the default but pass ``False`` to get the reverse.
    """
    hierarchy = []

    def traverse(cls):
        if cls is not object:
            hierarchy.append(cls)
            for parent in cls.__bases__:
                traverse(parent)

    traverse(klass)
    if topfirst:
        hierarchy.reverse()
    return hierarchy


def load_entry_points(group, ignore_errors=False):
    """
    Load a set of ``setuptools``-style entry points.

    This is used to locate "plugins" and similar things, e.g. the set
    of subcommands which belong to a main command.

    :param group: The group (string name) of entry points to be
       loaded, e.g. ``'wutta.commands'``.

    :param ignore_errors: If false (the default), any errors will be
       raised normally.  If true, errors will be logged but not
       raised.

    :returns: A dictionary whose keys are the entry point names, and
       values are the loaded entry points.
    """
    entry_points = {}

    try:
        # nb. this package was added in python 3.8
        import importlib.metadata as importlib_metadata  # pylint: disable=import-outside-toplevel
    except ImportError:
        import importlib_metadata  # pylint: disable=import-outside-toplevel

    eps = importlib_metadata.entry_points()
    if not hasattr(eps, "select"):
        # python < 3.10
        eps = eps.get(group, [])
    else:
        # python >= 3.10
        eps = eps.select(group=group)
    for entry_point in eps:
        try:
            ep = entry_point.load()
        except Exception:  # pylint: disable=broad-exception-caught
            if not ignore_errors:
                raise
            log.warning("failed to load entry point: %s", entry_point, exc_info=True)
        else:
            entry_points[entry_point.name] = ep

    return entry_points


def load_object(spec):
    """
    Load an arbitrary object from a module, according to the spec.

    The spec string should contain a dotted path to an importable module,
    followed by a colon (``':'``), followed by the name of the object to be
    loaded.  For example:

    .. code-block:: none

       wuttjamaican.util:parse_bool

    You'll notice from this example that "object" in this context refers to any
    valid Python object, i.e. not necessarily a class instance.  The name may
    refer to a class, function, variable etc.  Once the module is imported, the
    ``getattr()`` function is used to obtain a reference to the named object;
    therefore anything supported by that approach should work.

    :param spec: Spec string.

    :returns: The specified object.
    """
    if not spec:
        raise ValueError("no object spec provided")

    module_path, name = spec.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, name)


def make_title(text):
    """
    Return a human-friendly "title" for the given text.

    This is mostly useful for converting a Python variable name (or
    similar) to a human-friendly string, e.g.::

        make_title('foo_bar')     # => 'Foo Bar'
    """
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    words = text.split()
    return " ".join([x.capitalize() for x in words])


def make_full_name(*parts):
    """
    Make a "full name" from the given parts.

    :param \\*parts: Distinct name values which should be joined
       together to make the full name.

    :returns: The full name.

    For instance::

       make_full_name('First', '', 'Last', 'Suffix')
       # => "First Last Suffix"
    """
    parts = [(part or "").strip() for part in parts]
    parts = [part for part in parts if part]
    return " ".join(parts)


def get_timezone_by_name(tzname):
    """
    Retrieve a timezone object by name.

    This is mostly a compatibility wrapper, since older Python is
    missing the :mod:`python:zoneinfo` module.

    For Python 3.9 and newer, this instantiates
    :class:`python:zoneinfo.ZoneInfo`.

    For Python 3.8, this calls :func:`dateutil:dateutil.tz.gettz()`.

    See also :meth:`~wuttjamaican.app.AppHandler.get_timezone()` on
    the app handler.

    :param tzname: String name for timezone.

    :returns: :class:`python:datetime.tzinfo` instance
    """
    try:
        from zoneinfo import ZoneInfo  # pylint: disable=import-outside-toplevel

        return ZoneInfo(tzname)

    except ImportError:  # python 3.8
        from dateutil.tz import gettz  # pylint: disable=import-outside-toplevel

        return gettz(tzname)


def localtime(dt=None, from_utc=True, want_tzinfo=True, local_zone=None):
    """
    This produces a datetime in the "local" timezone.  By default it
    will be *zone-aware*.

    See also the shortcut
    :meth:`~wuttjamaican.app.AppHandler.localtime()` method on the app
    handler.  For usage examples see :ref:`convert-to-localtime`.

    See also :func:`make_utc()` which is sort of the inverse.

    :param dt: Optional :class:`python:datetime.datetime` instance.
       If not specified, the current time will be used.

    :param from_utc: Boolean indicating whether a naive ``dt`` is
       already (effectively) in UTC timezone.  Set this to false when
       providing a naive ``dt`` which is already in "local" timezone
       instead of UTC.  This flag is ignored if ``dt`` is zone-aware.

    :param want_tzinfo: Boolean indicating whether the resulting
       datetime should have its
       :attr:`~python:datetime.datetime.tzinfo` attribute set.  Set
       this to false if you want a naive value; it's true by default,
       for zone-aware.

    :param local_zone: Optional :class:`python:datetime.tzinfo`
       instance to use as "local" timezone, instead of relying on
       Python to determine the system local timezone.

    :returns: :class:`python:datetime.datetime` instance in local
       timezone.
    """
    # use current time if none provided
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)

    # set dt's timezone if needed
    if not dt.tzinfo:
        # UTC is default assumption unless caller says otherwise
        if from_utc:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        elif local_zone:
            dt = dt.replace(tzinfo=local_zone)
        else:  # default system local timezone
            tz = dt.astimezone().tzinfo
            dt = dt.replace(tzinfo=tz)

    # convert to local timezone
    if local_zone:
        dt = dt.astimezone(local_zone)
    else:
        dt = dt.astimezone()

    # maybe strip tzinfo
    if want_tzinfo:
        return dt
    return dt.replace(tzinfo=None)


def make_utc(dt=None, tzinfo=False):
    """
    This returns a datetime local to the UTC timezone.  By default it
    will be a *naive* datetime; the common use case is to convert as
    needed for sake of writing to the database.

    See also the shortcut
    :meth:`~wuttjamaican.app.AppHandler.make_utc()` method on the app
    handler.  For usage examples see :ref:`convert-to-utc`.

    See also :func:`localtime()` which is sort of the inverse.

    :param dt: Optional :class:`python:datetime.datetime` instance.
       If not specified, the current time will be used.

    :param tzinfo: Boolean indicating whether the return value should
       have its :attr:`~python:datetime.datetime.tzinfo` attribute
       set.  This is false by default in which case the return value
       will be naive.

    :returns: :class:`python:datetime.datetime` instance local to UTC.
    """
    # use current time if none provided
    if dt is None:
        now = datetime.datetime.now(datetime.timezone.utc)
        if tzinfo:
            return now
        return now.replace(tzinfo=None)

    # otherwise may need to convert timezone
    if dt.tzinfo:
        if dt.tzinfo is not datetime.timezone.utc:
            dt = dt.astimezone(datetime.timezone.utc)
        if tzinfo:
            return dt
        return dt.replace(tzinfo=None)

    # naive value returned as-is..
    if not tzinfo:
        return dt

    # ..unless tzinfo is wanted, in which case this assumes naive
    # value is in the UTC timezone
    return dt.replace(tzinfo=datetime.timezone.utc)


# TODO: deprecate / remove this eventually
def make_true_uuid():
    """
    Generate a new v7 UUID.

    See also :func:`make_uuid()`.

    :returns: :class:`python:uuid.UUID` instance
    """
    return uuid7()


# TODO: deprecate / remove this eventually
def make_str_uuid():
    """
    Generate a new v7 UUID value as string.

    See also :func:`make_uuid()`.

    :returns: UUID as 32-character hex string
    """
    return make_true_uuid().hex


# TODO: eventually refactor, to return true uuid
def make_uuid():
    """
    Generate a new v7 UUID value.

    See also the app handler shortcut,
    :meth:`~wuttjamaican.app.AppHandler.make_uuid()`.

    :returns: UUID as 32-character hex string

    .. warning::

       **TEMPORARY BEHAVIOR**

       For the moment, use of this function is discouraged.  Instead you
       should use :func:`make_true_uuid()` or :func:`make_str_uuid()` to
       be explicit about the return type you expect.

       *Eventually* (once it's clear most/all callers are using the
       explicit functions) this will be refactored to return a UUID
       instance.  But for now this function returns a string.
    """
    warnings.warn(
        "util.make_uuid() is temporarily deprecated, in favor of "
        "explicit functions, util.make_true_uuid() and util.make_str_uuid()",
        DeprecationWarning,
        stacklevel=2,
    )
    return make_str_uuid()


def parse_bool(value):
    """
    Derive a boolean from the given string value.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if str(value).lower() in ("true", "yes", "y", "on", "1"):
        return True
    return False


def parse_list(value):
    """
    Parse a configuration value, splitting by whitespace and/or commas
    and taking quoting into account etc., yielding a list of strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    parser = shlex.shlex(value)
    parser.whitespace += ","
    parser.whitespace_split = True
    values = list(parser)
    for i, val in enumerate(values):
        if val.startswith('"') and val.endswith('"'):
            values[i] = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            values[i] = val[1:-1]
    return values


def progress_loop(func, items, factory, message=None):
    """
    Convenience function to iterate over a set of items, invoking
    logic for each, and updating a progress indicator along the way.

    This function may also be called via the :term:`app handler`; see
    :meth:`~wuttjamaican.app.AppHandler.progress_loop()`.

    The ``factory`` will be called to create the progress indicator,
    which should be an instance of
    :class:`~wuttjamaican.progress.ProgressBase`.

    The ``factory`` may also be ``None`` in which case there is no
    progress, and this is really just a simple "for loop".

    :param func: Callable to be invoked for each item in the sequence.
       See below for more details.

    :param items: Sequence of items over which to iterate.

    :param factory: Callable which creates/returns a progress
       indicator, or can be ``None`` for no progress.

    :param message: Message to display along with the progress
       indicator.  If no message is specified, whether a default is
       shown will be up to the progress indicator.

    The ``func`` param should be a callable which accepts 2 positional
    args ``(obj, i)`` - meaning for which is as follows:

    :param obj: This will be an item within the sequence.

    :param i: This will be the *one-based* sequence number for the
       item.

    See also :class:`~wuttjamaican.progress.ConsoleProgress` for a
    usage example.
    """
    progress = None
    if factory:
        count = len(items)
        progress = factory(message, count)

    for i, item in enumerate(items, 1):
        func(item, i)
        if progress:
            progress.update(i)

    if progress:
        progress.finish()


def resource_path(path):
    """
    Returns the absolute file path for the given resource path.

    A "resource path" is one which designates a python package name,
    plus some path under that.  For instance:

    .. code-block:: none

       wuttjamaican.email:templates

    Assuming such a path should exist, the question is "where?"

    So this function uses :mod:`python:importlib.resources` to locate
    the path, possibly extracting the file(s) from a zipped package,
    and returning the final path on disk.

    It only does this if it detects it is needed, based on the given
    ``path`` argument.  If that is already an absolute path then it
    will be returned as-is.

    :param path: Either a package resource specifier as shown above,
       or regular file path.

    :returns: Absolute file path to the resource.
    """
    if not os.path.isabs(path) and ":" in path:
        try:
            # nb. these were added in python 3.9
            from importlib.resources import (  # pylint: disable=import-outside-toplevel
                files,
                as_file,
            )
        except ImportError:  # python < 3.9
            from importlib_resources import (  # pylint: disable=import-outside-toplevel
                files,
                as_file,
            )

        package, filename = path.split(":")
        ref = files(package) / filename
        with as_file(ref) as p:
            return str(p)

    return path


def simple_error(error):
    """
    Return a "simple" string for the given error.  Result will look
    like::

       "ErrorClass: Description for the error"

    However the logic checks to ensure the error has a descriptive
    message first; if it doesn't the result will just be::

       "ErrorClass"
    """
    cls = type(error).__name__
    msg = str(error)
    if msg:
        return f"{cls}: {msg}"
    return cls
