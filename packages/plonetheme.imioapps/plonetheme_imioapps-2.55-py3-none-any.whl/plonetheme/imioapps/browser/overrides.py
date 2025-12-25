# -*- coding: utf-8 -*-

from plone.app.layout.globals.context import ContextState
from plone.app.search.browser import Search


class ImioContextState(ContextState):
    """ """

    def canonical_object_url(self):
        """Do not include portal_factory in URL."""
        url = super(ImioContextState, self).canonical_object_url()
        if 'portal_factory' in url:
            portal_factory_index = url.index('portal_factory')
            url = url[:portal_factory_index]
        return url


class ImioSearch(Search):
    """Manage the "*" automatically to hide this from users and
       to be coherent with dashboards."""

    def filter_query(self, query):
        # query may sometimes be None
        query = super(ImioSearch, self).filter_query(query) or {}
        text = query.get('SearchableText', '')
        if not text.endswith('*'):
            text = text + '*'
        query['SearchableText'] = text
        return query
