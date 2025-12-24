# -*- coding: utf-8; -*-

import datetime
import sys
from unittest import TestCase
from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest

from wuttjamaican import util as mod
from wuttjamaican.progress import ProgressBase


class A:
    pass


class B(A):
    pass


class C(B):
    pass


class TestGetClassHierarchy(TestCase):

    def test_basic(self):

        classes = mod.get_class_hierarchy(A)
        self.assertEqual(classes, [A])

        classes = mod.get_class_hierarchy(B)
        self.assertEqual(classes, [A, B])

        classes = mod.get_class_hierarchy(C)
        self.assertEqual(classes, [A, B, C])

        classes = mod.get_class_hierarchy(C, topfirst=False)
        self.assertEqual(classes, [C, B, A])


class TestLoadEntryPoints(TestCase):

    def test_empty(self):
        # empty set returned for unknown group
        result = mod.load_entry_points("this_should_never_exist!!!!!!")
        self.assertEqual(result, {})

    def test_basic(self):
        # load some entry points which should "always" be present,
        # even in a testing environment.  basic sanity check
        result = mod.load_entry_points("console_scripts", ignore_errors=True)
        self.assertTrue(len(result) >= 1)
        self.assertIn("pip", result)

    def test_basic_pre_python_3_10(self):

        # the goal here is to get coverage for code which would only
        # run on python 3,9 and older, but we only need that coverage
        # if we are currently testing python 3.10+
        if sys.version_info.major == 3 and sys.version_info.minor < 10:
            pytest.skip("this test is not relevant before python 3.10")

        import importlib.metadata

        real_entry_points = importlib.metadata.entry_points()

        class FakeEntryPoints(dict):
            def get(self, group, default):
                return real_entry_points.select(group=group)

        importlib = MagicMock()
        importlib.metadata.entry_points.return_value = FakeEntryPoints()

        with patch.dict("sys.modules", **{"importlib": importlib}):

            # load some entry points which should "always" be present,
            # even in a testing environment.  basic sanity check
            result = mod.load_entry_points("console_scripts", ignore_errors=True)
            self.assertTrue(len(result) >= 1)
            self.assertIn("pytest", result)

    def test_basic_pre_python_3_8(self):

        # the goal here is to get coverage for code which would only
        # run on python 3.7 and older, but we only need that coverage
        # if we are currently testing python 3.8+
        if sys.version_info.major == 3 and sys.version_info.minor < 8:
            pytest.skip("this test is not relevant before python 3.8")

        from importlib.metadata import entry_points

        real_entry_points = entry_points()

        class FakeEntryPoints(dict):
            def get(self, group, default):
                if hasattr(real_entry_points, "select"):
                    return real_entry_points.select(group=group)
                return real_entry_points.get(group, [])

        importlib_metadata = MagicMock()
        importlib_metadata.entry_points.return_value = FakeEntryPoints()

        orig_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "importlib.metadata":
                raise ImportError
            if name == "importlib_metadata":
                return importlib_metadata
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):

            # load some entry points which should "always" be present,
            # even in a testing environment.  basic sanity check
            result = mod.load_entry_points("console_scripts", ignore_errors=True)
            self.assertTrue(len(result) >= 1)
            self.assertIn("pytest", result)

    def test_error(self):

        # skip if < 3.8
        if sys.version_info.major == 3 and sys.version_info.minor < 8:
            pytest.skip("this requires python 3.8 for entry points via importlib")

        entry_point = MagicMock()
        entry_point.load.side_effect = NotImplementedError

        entry_points = MagicMock()
        entry_points.select.return_value = [entry_point]

        importlib = MagicMock()
        importlib.metadata.entry_points.return_value = entry_points

        with patch.dict("sys.modules", **{"importlib": importlib}):

            # empty set returned if errors suppressed
            result = mod.load_entry_points("wuttatest.thingers", ignore_errors=True)
            self.assertEqual(result, {})
            importlib.metadata.entry_points.assert_called_once_with()
            entry_points.select.assert_called_once_with(group="wuttatest.thingers")
            entry_point.load.assert_called_once_with()

            # error is raised, if not suppressed
            importlib.metadata.entry_points.reset_mock()
            entry_points.select.reset_mock()
            entry_point.load.reset_mock()
            self.assertRaises(
                NotImplementedError, mod.load_entry_points, "wuttatest.thingers"
            )
            importlib.metadata.entry_points.assert_called_once_with()
            entry_points.select.assert_called_once_with(group="wuttatest.thingers")
            entry_point.load.assert_called_once_with()


class TestLoadObject(TestCase):

    def test_missing_spec(self):
        self.assertRaises(ValueError, mod.load_object, None)

    def test_basic(self):
        result = mod.load_object("unittest:TestCase")
        self.assertIs(result, TestCase)


class TestGetTimezoneByName(TestCase):

    def test_modern(self):
        try:
            import zoneinfo
        except ImportError:
            self.assertLess(sys.version_info, (3, 9))
            pytest.skip("this test is not relevant before python 3.9")

        tz = mod.get_timezone_by_name("America/Chicago")
        self.assertIsInstance(tz, zoneinfo.ZoneInfo)
        self.assertIsInstance(tz, datetime.tzinfo)
        self.assertEqual(tz.key, "America/Chicago")

    def test_legacy(self):
        import dateutil.tz

        orig_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "zoneinfo":
                raise ImportError
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            tz = mod.get_timezone_by_name("America/Chicago")
            self.assertIsInstance(tz, dateutil.tz.tzfile)
            self.assertIsInstance(tz, datetime.tzinfo)
            dt = datetime.datetime.now(tz)
            self.assertIn(dt.tzname(), ["CDT", "CST"])


class TestLocaltime(TestCase):

    def test_naive_utc(self):
        # nb. must override local_zone for test consistency
        tz = datetime.timezone(-datetime.timedelta(hours=5))
        dt = datetime.datetime(2025, 12, 16, 0, 16)  # utc
        result = mod.localtime(dt, local_zone=tz)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIs(result.tzinfo, tz)
        self.assertEqual(result, datetime.datetime(2025, 12, 15, 19, 16, tzinfo=tz))

    def test_naive_local(self):
        # nb. must override local_zone for test consistency
        tz = datetime.timezone(-datetime.timedelta(hours=5))
        dt = datetime.datetime(2025, 12, 15, 19, 16)  # local

        # can test precisely when overriding local_zone
        result = mod.localtime(dt, local_zone=tz, from_utc=False)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIs(result.tzinfo, tz)
        self.assertEqual(result, datetime.datetime(2025, 12, 15, 19, 16, tzinfo=tz))

        # must test loosely for fallback to system local timezone
        result = mod.localtime(dt, from_utc=False)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIsInstance(result.tzinfo, datetime.tzinfo)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)

    def test_aware_utc(self):
        # nb. must override local_zone for test consistency
        tz = datetime.timezone(-datetime.timedelta(hours=5))
        dt = datetime.datetime(2025, 12, 16, 0, 16, tzinfo=datetime.timezone.utc)
        result = mod.localtime(dt, local_zone=tz)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIs(result.tzinfo, tz)
        self.assertEqual(result, datetime.datetime(2025, 12, 15, 19, 16, tzinfo=tz))

    def test_aware_local(self):
        # nb. must override local_zone for test consistency
        tz = datetime.timezone(-datetime.timedelta(hours=5))
        other = datetime.timezone(-datetime.timedelta(hours=7))
        dt = datetime.datetime(2025, 12, 15, 17, 16, tzinfo=other)

        # can test precisely when overriding local_zone
        result = mod.localtime(dt, local_zone=tz)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIs(result.tzinfo, tz)
        self.assertEqual(result, datetime.datetime(2025, 12, 15, 19, 16, tzinfo=tz))

        # must test loosely for fallback to system local timezone
        result = mod.localtime(dt)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIsInstance(result.tzinfo, datetime.tzinfo)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)

    def test_current_time(self):
        tz = datetime.timezone(-datetime.timedelta(hours=5))

        # overriding local_zone
        result = mod.localtime(local_zone=tz)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIs(result.tzinfo, tz)

        # fallback to system local timezone
        result = mod.localtime()
        self.assertIsInstance(result, datetime.datetime)
        self.assertIsInstance(result.tzinfo, datetime.tzinfo)
        self.assertIsNot(result.tzinfo, tz)

    def test_want_tzinfo(self):

        # wants tzinfo implicitly
        result = mod.localtime()
        self.assertIsInstance(result.tzinfo, datetime.tzinfo)

        # wants tzinfo explicitly
        result = mod.localtime(want_tzinfo=True)
        self.assertIsInstance(result.tzinfo, datetime.tzinfo)

        # no tzinfo
        result = mod.localtime(want_tzinfo=False)
        self.assertIsNone(result.tzinfo)


class TestMakeUTC(TestCase):

    def test_current_time(self):

        # no tzinfo by default
        dt = mod.make_utc()
        self.assertIsInstance(dt, datetime.datetime)
        self.assertIsNone(dt.tzinfo)
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        self.assertAlmostEqual(int(dt.timestamp()), int(now.timestamp()))

        # with tzinfo
        dt = mod.make_utc(tzinfo=True)
        self.assertIsInstance(dt, datetime.datetime)
        self.assertIs(dt.tzinfo, datetime.timezone.utc)
        now = datetime.datetime.now(datetime.timezone.utc)
        self.assertAlmostEqual(int(dt.timestamp()), int(now.timestamp()))

    def test_convert_with_tzinfo(self):
        sample = datetime.datetime(
            2024, 9, 15, 8, 30, tzinfo=datetime.timezone(-datetime.timedelta(hours=5))
        )

        # no tzinfo by default
        dt = mod.make_utc(sample)
        self.assertEqual(dt, datetime.datetime(2024, 9, 15, 13, 30, tzinfo=None))

        # with tzinfo
        dt = mod.make_utc(sample, tzinfo=True)
        self.assertEqual(
            dt, datetime.datetime(2024, 9, 15, 13, 30, tzinfo=datetime.timezone.utc)
        )

    def test_convert_without_tzinfo(self):
        sample = datetime.datetime(2024, 9, 15, 8, 30)

        # no tzinfo by default
        dt = mod.make_utc(sample)
        self.assertEqual(dt, datetime.datetime(2024, 9, 15, 8, 30, tzinfo=None))

        # with tzinfo
        dt = mod.make_utc(sample, tzinfo=True)
        self.assertEqual(
            dt, datetime.datetime(2024, 9, 15, 8, 30, tzinfo=datetime.timezone.utc)
        )


class TestMakeUUID(TestCase):

    def test_str_uuid(self):
        uuid = mod.make_str_uuid()
        self.assertIsInstance(uuid, str)

    def test_true_uuid(self):
        uuid = mod.make_true_uuid()
        self.assertIsInstance(uuid, UUID)

    def test_temporary_behavior(self):
        uuid = mod.make_uuid()
        self.assertIsInstance(uuid, str)


class TestParseBool(TestCase):

    def test_null(self):
        self.assertIsNone(mod.parse_bool(None))

    def test_bool(self):
        self.assertTrue(mod.parse_bool(True))
        self.assertFalse(mod.parse_bool(False))

    def test_string_true(self):
        self.assertTrue(mod.parse_bool("true"))
        self.assertTrue(mod.parse_bool("yes"))
        self.assertTrue(mod.parse_bool("y"))
        self.assertTrue(mod.parse_bool("on"))
        self.assertTrue(mod.parse_bool("1"))

    def test_string_false(self):
        self.assertFalse(mod.parse_bool("false"))
        self.assertFalse(mod.parse_bool("no"))
        self.assertFalse(mod.parse_bool("n"))
        self.assertFalse(mod.parse_bool("off"))
        self.assertFalse(mod.parse_bool("0"))
        # nb. assume false for unrecognized input
        self.assertFalse(mod.parse_bool("whatever-else"))


class TestParseList(TestCase):

    def test_null(self):
        value = mod.parse_list(None)
        self.assertIsInstance(value, list)
        self.assertEqual(len(value), 0)

    def test_list_instance(self):
        mylist = []
        value = mod.parse_list(mylist)
        self.assertIs(value, mylist)

    def test_single_value(self):
        value = mod.parse_list("foo")
        self.assertEqual(len(value), 1)
        self.assertEqual(value[0], "foo")

    def test_single_value_padded_by_spaces(self):
        value = mod.parse_list("   foo   ")
        self.assertEqual(len(value), 1)
        self.assertEqual(value[0], "foo")

    def test_slash_is_not_a_separator(self):
        value = mod.parse_list("/dev/null")
        self.assertEqual(len(value), 1)
        self.assertEqual(value[0], "/dev/null")

    def test_multiple_values_separated_by_whitespace(self):
        value = mod.parse_list("foo bar baz")
        self.assertEqual(len(value), 3)
        self.assertEqual(value[0], "foo")
        self.assertEqual(value[1], "bar")
        self.assertEqual(value[2], "baz")

    def test_multiple_values_separated_by_commas(self):
        value = mod.parse_list("foo,bar,baz")
        self.assertEqual(len(value), 3)
        self.assertEqual(value[0], "foo")
        self.assertEqual(value[1], "bar")
        self.assertEqual(value[2], "baz")

    def test_multiple_values_separated_by_whitespace_and_commas(self):
        value = mod.parse_list("  foo,   bar   baz")
        self.assertEqual(len(value), 3)
        self.assertEqual(value[0], "foo")
        self.assertEqual(value[1], "bar")
        self.assertEqual(value[2], "baz")

    def test_multiple_values_separated_by_whitespace_and_commas_with_some_quoting(self):
        value = mod.parse_list(
            """
        foo
        "C:\\some path\\with spaces\\and, a comma",
        baz
        """
        )
        self.assertEqual(len(value), 3)
        self.assertEqual(value[0], "foo")
        self.assertEqual(value[1], "C:\\some path\\with spaces\\and, a comma")
        self.assertEqual(value[2], "baz")

    def test_multiple_values_separated_by_whitespace_and_commas_with_single_quotes(
        self,
    ):
        value = mod.parse_list(
            """
        foo
        'C:\\some path\\with spaces\\and, a comma',
        baz
        """
        )
        self.assertEqual(len(value), 3)
        self.assertEqual(value[0], "foo")
        self.assertEqual(value[1], "C:\\some path\\with spaces\\and, a comma")
        self.assertEqual(value[2], "baz")


class TestMakeTitle(TestCase):

    def test_basic(self):
        text = mod.make_title("foo_bar")
        self.assertEqual(text, "Foo Bar")


class TestMakeFullName(TestCase):

    def test_basic(self):
        name = mod.make_full_name("Fred", "", "Flintstone", "")
        self.assertEqual(name, "Fred Flintstone")


class TestProgressLoop(TestCase):

    def test_basic(self):

        def act(obj, i):
            pass

        # with progress
        mod.progress_loop(act, [1, 2, 3], ProgressBase, message="whatever")

        # without progress
        mod.progress_loop(act, [1, 2, 3], None, message="whatever")


class TestResourcePath(TestCase):

    def test_basic(self):

        # package spec is resolved to path
        path = mod.resource_path("wuttjamaican:util.py")
        self.assertTrue(path.endswith("wuttjamaican/util.py"))

        # absolute path returned as-is
        self.assertEqual(
            mod.resource_path("/tmp/doesnotexist.txt"), "/tmp/doesnotexist.txt"
        )

    def test_basic_pre_python_3_9(self):

        # the goal here is to get coverage for code which would only
        # run on python 3.8 and older, but we only need that coverage
        # if we are currently testing python 3.9+
        if sys.version_info.major == 3 and sys.version_info.minor < 9:
            pytest.skip("this test is not relevant before python 3.9")

        from importlib.resources import files, as_file

        orig_import = __import__

        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "importlib.resources":
                raise ImportError
            if name == "importlib_resources":
                return MagicMock(files=files, as_file=as_file)
            return orig_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=mock_import):

            # package spec is resolved to path
            path = mod.resource_path("wuttjamaican:util.py")
            self.assertTrue(path.endswith("wuttjamaican/util.py"))

            # absolute path returned as-is
            self.assertEqual(
                mod.resource_path("/tmp/doesnotexist.txt"), "/tmp/doesnotexist.txt"
            )


class TestSimpleError(TestCase):

    def test_with_description(self):
        try:
            raise RuntimeError("just testin")
        except Exception as error:
            result = mod.simple_error(error)
        self.assertEqual(result, "RuntimeError: just testin")

    def test_without_description(self):
        try:
            raise RuntimeError
        except Exception as error:
            result = mod.simple_error(error)
        self.assertEqual(result, "RuntimeError")
