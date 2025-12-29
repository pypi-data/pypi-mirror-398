import base64
import urllib.parse
from io import BytesIO
from tempfile import TemporaryFile

import requests
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class BackblazeStorage(Storage):

    def __init__(self, app_key=None, account_id=None, bucket_name=None, bucket_id=None):
        from django.conf import settings

        self.app_key = app_key or getattr(settings, "STORAGE_BACKBLAZE_APP_KEY", None)
        self.account_id = account_id or getattr(
            settings, "STORAGE_BACKBLAZE_ACCOUNT_ID", None
        )
        self.bucket_name = bucket_name or getattr(
            settings, "STORAGE_BACKBLAZE_BUCKET_NAME", None
        )
        self.bucket_id = bucket_id or getattr(
            settings, "STORAGE_BACKBLAZE_BUCKET_ID", None
        )
        self.download_url = ""
        self.base_url = ""
        
        self.backblaze_authorize()

    def backblaze_authorize(self):
        try:
            auth_string = f"{self.account_id}:{self.app_key}".encode("utf-8")
            encoded_auth_string = base64.b64encode(auth_string).decode("utf-8")

            response = requests.get(
                "https://api.backblaze.com/b2api/v2/b2_authorize_account",
                headers={"Authorization": f"Basic {encoded_auth_string}"},
            )

            response.raise_for_status()

            if response.status_code == 200:
                resp = response.json()
                self.base_url = resp["apiUrl"]
                self.download_url = resp["downloadUrl"]
                self.authorization_token = resp["authorizationToken"]
                return True
            else:
                return False
        except requests.RequestException as e:
            return False

    def _build_url(self, endpoint=None, authorization=True):
        return "%s%s" % (self.base_url, endpoint)

    def _normalize_filename(self, name):
        normalized_name = name.replace("\\", "/")
        parts = normalized_name.split("/")
        encoded_parts = [urllib.parse.quote(part, safe="") for part in parts]
        return "/".join(encoded_parts)

    def _get_upload_url(self):
        params = {"bucketId": self.bucket_id}
        url = self._build_url("/b2api/v1/b2_get_upload_url")
        headers = {"Authorization": self.authorization_token}
        return requests.get(url, headers=headers, params=params).json()

    def _temporary_storage(self, contents):
        return TemporaryFile(contents, "r+")

    def save(self, name, content, max_length=None):
        response = self._get_upload_url() or {}
        
        if "uploadUrl" not in response:
            self.backblaze_authorize()
            response = self._get_upload_url()

        if "uploadUrl" not in response:
            return False

        upload_url = response["uploadUrl"]

        try:
            content.seek(0)
        except Exception:
            pass

        normalized_name = self._normalize_filename(name)

        headers = {
            "Content-Type": "b2/x-auto",
            "X-Bz-File-Name": normalized_name,
            "X-Bz-Content-Sha1": "do_not_verify",
            "X-Bz-Info-src_last_modified_millis": "",
            "Authorization": response["authorizationToken"],
        }

        download_response = requests.post(upload_url, headers=headers, data=content.read())

        if download_response.status_code == 503:
            attempts = 0
            while attempts <= 3 and download_response.status_code == 503:
                download_response = requests.post(
                    upload_url,
                    headers=headers,
                    data=content.read(),
                )
                attempts += 1

        if download_response.status_code != 200:
            download_response.raise_for_status()

        resp = download_response.json()

        if "fileName" in resp:
            return resp["fileName"]
        else:
            pass

    def exists(self, name):
        return False

    def open(self, name, mode="rb"):
        headers = {"Authorization": self.authorization_token}
        normalized_name = self._normalize_filename(name)
        resp = requests.get(
            "%s/file/%s/%s" % (self.download_url, self.bucket_name, normalized_name),
            headers=headers,
        ).content

        output = BytesIO()
        output.write(resp)
        output.seek(0)
        return File(output, name)

    def url(self, name):
        normalized_name = self._normalize_filename(name)
        return "%s/file/%s/%s" % (self.download_url, self.bucket_name, normalized_name)
