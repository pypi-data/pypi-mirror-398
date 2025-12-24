"""RestAPI endpoint @redirects-import POST (CSV upload)."""

import csv
import io
import plone.protect.interfaces
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

from eea.api.redirector.interfaces import IStorageUtility
from eea.api.redirector.restapi.add import add_redirects


@implementer(IPublishTraverse)
class RedisRedirectsCSVImport(Service):
    """Import redirects from a CSV file upload."""

    def _get_uploaded_file(self):
        file_upload = self.request.form.get("file")
        if not file_upload:
            raise BadRequest(
                "No file uploaded. Expected multipart/form-data with 'file' field."
            )
        return file_upload

    def _parse_csv(self, file_upload):
        data = file_upload.read()
        if not data:
            raise BadRequest("CSV file is empty")

        try:
            text = data.decode("utf-8-sig")
        except Exception as err:
            raise BadRequest(f"Failed to decode CSV file: {err}") from err

        reader = csv.reader(io.StringIO(text))
        redirects = []
        failed_rows = []

        for index, row in enumerate(reader):
            if index == 0:
                continue
            if not row or all(not cell.strip() for cell in row):
                continue

            old_url = row[0].strip() if len(row) > 0 else ""
            new_url = row[1].strip() if len(row) > 1 else ""

            if not old_url:
                failed_rows.append({"row": index + 1, "error": "Missing old URL"})
                continue

            redirects.append({"path": old_url, "redirect-to": new_url})

        return redirects, failed_rows

    def reply(self):
        """Import redirects to Redis storage from CSV."""
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        file_upload = self._get_uploaded_file()
        redirects, failed_rows = self._parse_csv(file_upload)

        if not redirects and not failed_rows:
            raise BadRequest("No valid redirects found in CSV file")

        storage = getUtility(IStorageUtility)
        success_count, failed_redirects = add_redirects(storage, redirects)
        failed = failed_rows + failed_redirects

        if failed:
            self.request.response.setStatus(207)  # Multi-Status
            return {
                "type": "partial_success" if success_count > 0 else "error",
                "success_count": success_count,
                "failed_count": len(failed),
                "failed": failed,
            }

        return {
            "type": "success",
            "success_count": success_count,
            "failed_count": 0,
            "failed": [],
        }
