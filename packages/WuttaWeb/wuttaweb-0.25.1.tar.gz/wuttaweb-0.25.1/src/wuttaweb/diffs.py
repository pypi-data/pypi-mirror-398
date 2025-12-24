# -*- coding: utf-8; -*-
################################################################################
#
#  wuttaweb -- Web App for Wutta Framework
#  Copyright © 2024-2025 Lance Edgar
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

import sqlalchemy as sa

from pyramid.renderers import render
from webhelpers2.html import HTML

from wuttjamaican.diffs import Diff


class WebDiff(Diff):
    """
    Simple diff class for the web app.

    This is based on the
    :class:`~wuttjamaican:wuttjamaican.diffs.Diff` class; it just
    tweaks :meth:`render_html()` to use the web template lookup
    engine.
    """

    cell_padding = None

    def render_html(self, template="/diff.mako", **kwargs):
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
        html = render(template, context)
        return HTML.literal(html)


class VersionDiff(WebDiff):
    """
    Special diff class for use with version history views.  While
    based on :class:`WebDiff`, this class uses a different signature
    for the constructor.

    :param config: The app :term:`config object`.

    :param version: Reference to a Continuum version record object.

    :param \\**kwargs: Remaining kwargs are passed as-is to the
       :class:`WebDiff` constructor.
    """

    def __init__(self, config, version, **kwargs):
        import sqlalchemy_continuum as continuum  # pylint: disable=import-outside-toplevel
        from wutta_continuum.util import (  # pylint: disable=import-outside-toplevel
            render_operation_type,
        )

        self.version = version
        self.model_class = continuum.parent_class(type(self.version))
        self.mapper = sa.inspect(self.model_class)
        self.version_mapper = sa.inspect(type(self.version))
        self.title = kwargs.pop("title", self.model_class.__name__)

        self.operation_title = render_operation_type(self.version.operation_type)

        if "nature" not in kwargs:
            if (
                version.previous
                and version.operation_type == continuum.Operation.DELETE
            ):
                kwargs["nature"] = "delete"
            elif version.previous:
                kwargs["nature"] = "update"
            else:
                kwargs["nature"] = "create"

        if "fields" not in kwargs:
            kwargs["fields"] = self.get_default_fields()

        old_data = {}
        new_data = {}
        for field in kwargs["fields"]:
            if version.previous:
                old_data[field] = getattr(version.previous, field)
            new_data[field] = getattr(version, field)

        super().__init__(config, old_data, new_data, **kwargs)

    def get_default_fields(self):  # pylint: disable=missing-function-docstring
        fields = sorted(self.version_mapper.columns.keys())

        unwanted = [
            "transaction_id",
            "end_transaction_id",
            "operation_type",
        ]

        return [field for field in fields if field not in unwanted]

    def render_version_value(self, version, field, value):
        """
        Render the cell value HTML for a given version + field.

        This method is used to render both sides of the diff (old +
        new values).  It will just render the field value using a
        monospace font by default.  However:

        If the field is involved in a mapper relationship (i.e. it is
        the "foreign key" to a related table), the logic here will
        also (try to) traverse that show display text for the related
        object (if found).

        :param version: Reference to the Continuum version object.

        :param field: Name of the field, as string.

        :param value: Raw value for the field, as obtained from the
           version object.

        :returns: Rendered cell value as HTML literal
        """
        # first render normal span; this is our fallback but also may
        # be embedded within a more complex result.
        text = HTML.tag("span", c=[repr(value)], style="font-family: monospace;")

        # loop thru all mapped relationship props
        for prop in self.mapper.relationships:

            # we only want singletons
            if prop.uselist:
                continue

            # loop thru columns for prop
            # nb. there should always be just one colum for a
            # singleton prop, but technically a list is used, so no
            # harm in looping i assume..
            for col in prop.local_columns:

                # we only want the matching column
                if col.name != field:
                    continue

                # grab "related version" reference via prop key.  this
                # would be like a UserVersion for instance.
                if ref := getattr(version, prop.key):

                    # grab "related object" reference.  this would be
                    # like a User for instance.
                    if ref := getattr(ref, "version_parent", None):

                        # render text w/ related object as bold string
                        style = (
                            "margin-left: 2rem; font-style: italic; font-weight: bold;"
                        )
                        return HTML.tag(
                            "span",
                            c=[text, HTML.tag("span", c=[str(ref)], style=style)],
                        )

        return text

    def render_old_value(self, field):
        if self.nature == "create":
            return ""
        value = self.old_value(field)
        return self.render_version_value(self.version.previous, field, value)

    def render_new_value(self, field):
        if self.nature == "delete":
            return ""
        value = self.new_value(field)
        return self.render_version_value(self.version, field, value)
