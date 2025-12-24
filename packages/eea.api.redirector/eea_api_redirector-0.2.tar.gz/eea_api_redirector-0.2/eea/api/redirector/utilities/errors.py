"""Custom error handling for API requests."""

from zope.component import getUtility
from plone.rest.errors import ErrorHandling as BaseErrorHandling
from plone.rest.interfaces import IAPIRequest
from zope.component import adapter
from zope.component.hooks import getSite
from zExceptions import NotFound
from eea.api.redirector.interfaces import IStorageUtility


@adapter(NotFound, IAPIRequest)
class ErrorHandling(BaseErrorHandling):
    """Custom error handling for API requests."""

    def find_redirect_if_view_or_service(self, old_path_elements, storage):
        """Check if the requested URL corresponds to a view or service"""
        if len(old_path_elements) <= 1:
            return None

        site_id = getSite().getId()
        extra_storage = getUtility(IStorageUtility)
        splitpoint = len(old_path_elements)
        while splitpoint > 1:
            possible_obj_path = "/".join(old_path_elements[:splitpoint])
            other_possible_obj_path = possible_obj_path
            if other_possible_obj_path.startswith("/" + site_id):
                other_possible_obj_path = other_possible_obj_path[len(site_id) + 1 :]

            remainder = old_path_elements[splitpoint:]
            new_path = (
                storage.get(possible_obj_path)
                or extra_storage.get(possible_obj_path)
                or extra_storage.get(other_possible_obj_path)
            )

            if new_path == b"":
                self.request.response.setStatus(410, lock=1)
                return None

            if new_path:
                if new_path.startswith(possible_obj_path):
                    # New URL would match originally requested URL.
                    # Lets not cause a redirect loop.
                    return None

                return new_path + "/" + "/".join(remainder)

            splitpoint -= 1

        return None
