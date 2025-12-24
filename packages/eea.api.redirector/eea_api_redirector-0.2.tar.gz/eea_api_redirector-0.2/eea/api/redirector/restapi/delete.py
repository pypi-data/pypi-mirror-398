"""RestAPI endpoint @redirects DELETE"""

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


@implementer(IPublishTraverse)
class RedisRedirectsDelete(Service):
    """Delete redirects from Redis"""

    def reply(self):
        """Delete one or more redirects from Redis storage"""
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        data = json_body(self.request)
        storage = getUtility(IStorageUtility)
        redirects = data.get("items", [])

        if not redirects:
            raise BadRequest(
                "No items provided. Expected format: {'items': [{'path': '/old'}]}"
            )

        failed_redirects = []
        success_count = 0

        for redirect in redirects:
            # Handle both dict format and simple string format
            if isinstance(redirect, dict):
                path = redirect.get("path")
            else:
                path = redirect

            if not path:
                failed_redirects.append(
                    {"redirect": str(redirect), "error": "Missing 'path' field"}
                )
                continue

            # Validate path
            if not path.startswith("/"):
                failed_redirects.append(
                    {"path": path, "error": f"Path must start with '/': {path}"}
                )
                continue

            # Delete from Redis
            try:
                result = storage.delete(path)
                if result:
                    success_count += 1
                    logger.info(f"Deleted redirect: {path}")
                else:
                    # result is 0 if key didn't exist, None if error occurred
                    if result == 0:
                        failed_redirects.append(
                            {"path": path, "error": "Path not found in Redis"}
                        )
                    else:
                        failed_redirects.append(
                            {"path": path, "error": "Failed to delete from Redis"}
                        )
            except Exception as err:
                logger.exception(f"Error deleting redirect {path}: {err}")
                failed_redirects.append({"path": path, "error": str(err)})

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
