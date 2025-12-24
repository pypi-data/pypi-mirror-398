# -*- coding: utf-8; -*-

from wuttjamaican import diffs as mod
from wuttjamaican.testing import ConfigTestCase


class TestDiff(ConfigTestCase):

    def make_diff(self, *args, **kwargs):
        return mod.Diff(self.config, *args, **kwargs)

    def test_constructor(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data, fields=["foo"])
        self.assertEqual(diff.fields, ["foo"])
        self.assertEqual(diff.cell_padding, "0.25rem")
        diff = self.make_diff(old_data, new_data, cell_padding="0.5rem")
        self.assertEqual(diff.cell_padding, "0.5rem")

    def test_make_fields(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "bar", "baz": "zer"}
        # nb. this calls make_fields()
        diff = self.make_diff(old_data, new_data)
        # TODO: should the fields be cumulative? or just use new_data?
        self.assertEqual(diff.fields, ["baz", "foo"])

    def test_values(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        self.assertEqual(diff.old_value("foo"), "bar")
        self.assertEqual(diff.new_value("foo"), "baz")

    def test_values_differ(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        self.assertTrue(diff.values_differ("foo"))

        old_data = {"foo": "bar"}
        new_data = {"foo": "bar"}
        diff = self.make_diff(old_data, new_data)
        self.assertFalse(diff.values_differ("foo"))

    def test_render_values(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        self.assertEqual(
            diff.render_old_value("foo"),
            '<span style="font-family: monospace;">&#39;bar&#39;</span>',
        )
        self.assertEqual(
            diff.render_new_value("foo"),
            '<span style="font-family: monospace;">&#39;baz&#39;</span>',
        )

    def test_get_old_value_attrs(self):

        # no change
        old_data = {"foo": "bar"}
        new_data = {"foo": "bar"}
        diff = self.make_diff(old_data, new_data, nature="update")
        self.assertEqual(diff.get_old_value_attrs(False), {"style": "padding: 0.25rem"})

        # update
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data, nature="update")
        self.assertEqual(
            diff.get_old_value_attrs(True),
            {"style": f"background-color: {diff.old_color}; padding: 0.25rem"},
        )

        # delete
        old_data = {"foo": "bar"}
        new_data = {}
        diff = self.make_diff(old_data, new_data, nature="delete")
        self.assertEqual(
            diff.get_old_value_attrs(True),
            {"style": f"background-color: {diff.old_color}; padding: 0.25rem"},
        )

    def test_get_new_value_attrs(self):

        # no change
        old_data = {"foo": "bar"}
        new_data = {"foo": "bar"}
        diff = self.make_diff(old_data, new_data, nature="update")
        self.assertEqual(diff.get_new_value_attrs(False), {"style": "padding: 0.25rem"})

        # update
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data, nature="update")
        self.assertEqual(
            diff.get_new_value_attrs(True),
            {"style": f"background-color: {diff.new_color}; padding: 0.25rem"},
        )

        # create
        old_data = {}
        new_data = {"foo": "bar"}
        diff = self.make_diff(old_data, new_data, nature="create")
        self.assertEqual(
            diff.get_new_value_attrs(True),
            {"style": f"background-color: {diff.new_color}; padding: 0.25rem"},
        )

    def test_render_field_row(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        row = diff.render_field_row("foo")
        self.assertIn("<tr>", row)
        self.assertIn("&#39;bar&#39;", row)
        self.assertIn(
            f'style="background-color: {diff.old_color}; padding: 0.25rem"', row
        )
        self.assertIn("&#39;baz&#39;", row)
        self.assertIn(
            f'style="background-color: {diff.new_color}; padding: 0.25rem"', row
        )
        self.assertIn("</tr>", row)

    def test_render_html(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        html = diff.render_html()
        self.assertIn("<table", html)
        self.assertIn("<tr>", html)
        self.assertIn("&#39;bar&#39;", html)
        self.assertIn(
            f'style="background-color: {diff.old_color}; padding: 0.25rem"', html
        )
        self.assertIn("&#39;baz&#39;", html)
        self.assertIn(
            f'style="background-color: {diff.new_color}; padding: 0.25rem"', html
        )
        self.assertIn("</tr>", html)
        self.assertIn("</table>", html)
