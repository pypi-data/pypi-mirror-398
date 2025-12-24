"""Redirects Controlpanel API"""

from zope.interface import Interface
from zope.component import adapter
from plone.restapi.controlpanels import RegistryConfigletPanel
from eea.api.redirector.interfaces import IRedirectsSettings
from eea.api.redirector.interfaces import IEeaApiRedirectorLayer


@adapter(Interface, IEeaApiRedirectorLayer)
class RedirectsControlpanel(RegistryConfigletPanel):
    """EEA Redirects Control Panel"""

    schema = IRedirectsSettings
    configlet_id = "eea-redirects"
    configlet_category_id = "Products"
    schema_prefix = None
