# -*- coding: utf-8 -*-

from collective.messagesviewlet.interfaces import ICollectiveMessagesviewletLayer
from plonetheme.imioapps import PloneMessageFactory as _
from zope import schema
from zope.interface import Interface


class IThemeSpecific(ICollectiveMessagesviewletLayer):
    """Marker interface that defines a Zope browser layer.
       Make it inherits from the collective.messagesviewlet layer so we are able
       to easily redefine the collective.messagesviewlet viewlet.
    """


class IPlonethemeImioappsSettings(Interface):
    """ """
    help_url = schema.ASCIILine(
        title=_(u"Help icon url"),
        description=_(u"Set the url of the help icon here"),
        default='',
        required=False,
    )
