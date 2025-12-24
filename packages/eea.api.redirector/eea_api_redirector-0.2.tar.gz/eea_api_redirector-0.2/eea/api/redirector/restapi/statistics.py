"""RestAPI endpoint @redirects-statistics GET"""

from plone.restapi.services import Service
from zope.component import getUtility
from eea.api.redirector.interfaces import IStorageUtility


class RedisRedirectsStatistics(Service):
    """Get redirect statistics"""

    def reply(self):
        """Reply with redirect statistics from Redis"""
        storage = getUtility(IStorageUtility)

        # Get query parameter
        query = self.request.form.get("q", "")

        # Calculate statistics
        stats = storage.get_statistics(
            pattern="*",
            query=query if query else None,
        )

        return {
            "@id": f"{self.context.absolute_url()}/@redirects-statistics",
            "statistics": stats,
        }
