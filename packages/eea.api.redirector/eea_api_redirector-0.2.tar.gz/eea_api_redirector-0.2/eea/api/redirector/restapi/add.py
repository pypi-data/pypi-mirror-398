"""RestAPI endpoint @redirects POST"""

from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from eea.api.redirector.interfaces import IStorageUtility
import plone.protect.interfaces
import logging


logger = logging.getLogger(__name__)


def add_redirects(storage, redirects):
    """Validate and add redirects to storage."""
    failed_redirects = []
    success_count = 0

    for redirect in redirects:
        if not isinstance(redirect, dict):
            failed_redirects.append(
                {
                    "redirect": str(redirect),
                    "error": "Item must be a dictionary with 'path' and 'redirect-to' keys",
                }
            )
            continue

        path = redirect.get("path")
        target = redirect.get("redirect-to")

        if not path:
            failed_redirects.append(
                {"redirect": str(redirect), "error": "Missing 'path' field"}
            )
            continue

        if target is None:
            failed_redirects.append(
                {"redirect": str(redirect), "error": "Missing 'redirect-to' field"}
            )
            continue

        # Validate paths
        if not path.startswith("/"):
            failed_redirects.append(
                {
                    "redirect": str(redirect),
                    "error": f"Path must start with '/': {path}",
                }
            )
            continue

        # Prevent self-redirects (but allow empty target for Gone)
        if target and path == target:
            failed_redirects.append(
                {
                    "redirect": str(redirect),
                    "error": "Path and target cannot be the same",
                }
            )
            continue

        # Add to Redis
        try:
            result = storage.set(path, target)
            if result:
                success_count += 1
                logger.info("Added redirect: %s -> %s", path, target)
            else:
                failed_redirects.append(
                    {
                        "path": path,
                        "redirect-to": target,
                        "error": "Failed to set value in Redis",
                    }
                )
        except Exception as err:
            logger.exception("Error adding redirect %s -> %s: %s", path, target, err)
            failed_redirects.append(
                {"path": path, "redirect-to": target, "error": str(err)}
            )

    return success_count, failed_redirects


@implementer(IPublishTraverse)
class RedisRedirectsPost(Service):
    """Add redirects to Redis"""

    def reply(self):
        """Add one or more redirects to Redis storage"""
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        data = json_body(self.request)
        storage = getUtility(IStorageUtility)
        redirects = data.get("items", [])

        if not redirects:
            raise BadRequest(
                "No items provided. Expected format: {'items': [{'path': '/old', 'redirect-to': '/new'}]}"
            )

        success_count, failed_redirects = add_redirects(storage, redirects)

        # Return appropriate response
        if failed_redirects:
            self.request.response.setStatus(207)  # Multi-Status
            return {
                "type": "partial_success" if success_count > 0 else "error",
                "success_count": success_count,
                "failed_count": len(failed_redirects),
                "failed": failed_redirects,
            }

        return self.reply_no_content()
