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
Tools for displaying simple data diffs
"""

from mako.template import Template
from webhelpers2.html import HTML


class Diff:  # pylint: disable=too-many-instance-attributes
    """
    Represent / display a basic "diff" between two data records.

    You must provide both the "old" and "new" data records, when
    constructing an instance of this class.  Then call
    :meth:`render_html()` to display the diff table.

    :param config: The app :term:`config object`.

    :param old_data: Dict of "old" data record.

    :param new_data: Dict of "new" data record.

    :param fields: Optional list of field names.  If not specified,
       will be derived from the data records.

    :param nature: What sort of diff is being represented; must be one
       of: ``("create", "update", "delete")``

    :param old_color: Background color to display for "old/deleted"
       field data, when applicable.

    :param new_color: Background color to display for "new/created"
       field data, when applicable.

    :param cell_padding: Optional override for cell padding style.
    """

    cell_padding = "0.25rem"

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        config,
        old_data: dict,
        new_data: dict,
        fields: list = None,
        nature="update",
        old_color="#ffebe9",
        new_color="#dafbe1",
        cell_padding=None,
    ):
        self.config = config
        self.app = self.config.get_app()
        self.old_data = old_data
        self.new_data = new_data
        self.columns = ["field name", "old value", "new value"]
        self.fields = fields or self.make_fields()
        self.nature = nature
        self.old_color = old_color
        self.new_color = new_color
        if cell_padding:
            self.cell_padding = cell_padding

    def make_fields(self):  # pylint: disable=missing-function-docstring
        return sorted(set(self.old_data) | set(self.new_data), key=lambda x: x.lower())

    def render_html(self, template=None, **kwargs):
        """
        Render the diff as HTML table.

        :param template: Name of template to render, if you need to
           override the default.

        :param \\**kwargs: Remaining kwargs are passed as context to
           the template renderer.

        :returns: HTML literal string
        """
        context = kwargs
        context["diff"] = self

        if not isinstance(template, Template):
            path = self.app.resource_path(
                template or "wuttjamaican:templates/diff.mako"
            )
            template = Template(filename=path)

        return HTML.literal(template.render(**context))

    def render_field_row(self, field):  # pylint: disable=missing-function-docstring
        is_diff = self.values_differ(field)

        kw = {}
        if self.cell_padding:
            kw["style"] = f"padding: {self.cell_padding}"
        td_field = HTML.tag("td", class_="field", c=field, **kw)

        td_old_value = HTML.tag(
            "td",
            c=self.render_old_value(field),
            **self.get_old_value_attrs(is_diff),
        )

        td_new_value = HTML.tag(
            "td",
            c=self.render_new_value(field),
            **self.get_new_value_attrs(is_diff),
        )

        return HTML.tag("tr", c=[td_field, td_old_value, td_new_value])

    def render_cell_value(self, value):  # pylint: disable=missing-function-docstring
        return HTML.tag("span", c=[value], style="font-family: monospace;")

    def render_old_value(self, field):  # pylint: disable=missing-function-docstring
        value = "" if self.nature == "create" else repr(self.old_value(field))
        return self.render_cell_value(value)

    def render_new_value(self, field):  # pylint: disable=missing-function-docstring
        value = "" if self.nature == "delete" else repr(self.new_value(field))
        return self.render_cell_value(value)

    def get_cell_attrs(  # pylint: disable=missing-function-docstring
        self, style=None, **attrs
    ):
        style = dict(style or {})

        if self.cell_padding and "padding" not in style:
            style["padding"] = self.cell_padding

        if style:
            attrs["style"] = "; ".join([f"{k}: {v}" for k, v in style.items()])

        return attrs

    def get_old_value_attrs(  # pylint: disable=missing-function-docstring
        self, is_diff
    ):
        style = {}
        if self.nature == "update" and is_diff:
            style["background-color"] = self.old_color
        elif self.nature == "delete":
            style["background-color"] = self.old_color

        return self.get_cell_attrs(style)

    def get_new_value_attrs(  # pylint: disable=missing-function-docstring
        self, is_diff
    ):
        style = {}
        if self.nature == "create":
            style["background-color"] = self.new_color
        elif self.nature == "update" and is_diff:
            style["background-color"] = self.new_color

        return self.get_cell_attrs(style)

    def old_value(self, field):  # pylint: disable=missing-function-docstring
        return self.old_data.get(field)

    def new_value(self, field):  # pylint: disable=missing-function-docstring
        return self.new_data.get(field)

    def values_differ(self, field):  # pylint: disable=missing-function-docstring
        return self.new_value(field) != self.old_value(field)
