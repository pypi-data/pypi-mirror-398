# -*- coding: utf-8; -*-

from wuttaweb.menus import MenuHandler


class NullMenuHandler(MenuHandler):
    """
    Dummy :term:`menu handler` for testing.
    """

    def make_menus(self, request, **kwargs):
        """
        This always returns an empty menu set.
        """
        return []
