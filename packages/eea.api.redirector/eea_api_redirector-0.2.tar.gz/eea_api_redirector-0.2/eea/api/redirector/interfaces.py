"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IEeaApiRedirectorLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IStorageUtility(Interface):
    """Storage Utility"""


class IRedirectsSettings(Interface):
    """Settings for EEA Redirects Control Panel.

    This interface has no fields as the control panel UI
    will be fully customized in the Volto frontend.
    """
