"""RestAPI endpoint @redirects GET"""

from plone.restapi.services import Service
from zope.component import getUtility
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from eea.api.redirector.interfaces import IStorageUtility


@implementer(IPublishTraverse)
class RedisRedirectsGet(Service):
    """Get Redis redirects"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        """Traverse to capture path parameters"""
        self.params.append(name)
        return self

    def reply(self):
        """Reply with redirect information from Redis"""
        storage = getUtility(IStorageUtility)

        # If a specific path is provided, get that redirect
        if self.params:
            path = "/" + "/".join(self.params)
            target = storage.get(path)

            if target:
                return {
                    "@id": f"{self.context.absolute_url()}/@redirects{path}",
                    "path": path,
                    "redirect-to": target.decode("utf-8")
                    if isinstance(target, bytes)
                    else target,
                }
            else:
                self.request.response.setStatus(404)
                return {
                    "type": "NotFound",
                    "message": f"No redirect found for path: {path}",
                }

        # List redirects with efficient pagination
        query = self.request.form.get("q", "")
        b_size = int(self.request.form.get("b_size", 25))
        b_start = int(self.request.form.get("b_start", 0))
        search_scope = self.request.form.get("search_scope", "old_url")

        # Validate search_scope
        if search_scope not in ("old_url", "new_url", "both"):
            search_scope = "old_url"

        # Get paginated redirects (efficient for large datasets)
        # Statistics are now fetched separately via @redirects-statistics endpoint
        items, items_total, _ = storage.list_paginated(
            pattern="*",
            query=query if query else None,
            batch_size=b_size,
            batch_start=b_start,
            search_scope=search_scope,
        )

        result = {
            "@id": f"{self.context.absolute_url()}/@redirects",
            "items": items,
            "items_total": items_total,
        }

        return result
