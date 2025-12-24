"""Control Panel"""

from plone.app.registry.browser import controlpanel
from eea.api.redirector.interfaces import IRedirectsSettings


class RedirectsControlPanelForm(controlpanel.RegistryEditForm):
    """EEA Redirects Control Panel Form."""

    id = "eea-redirects"
    label = "EEA Redirects Settings"
    description = "Manage redirects stored in Redis. Note: This control panel has no configuration fields. Use the Volto interface to manage redirects."
    schema = IRedirectsSettings


class RedirectsControlPanelView(controlpanel.ControlPanelFormWrapper):
    """EEA Redirects Control Panel"""

    form = RedirectsControlPanelForm
