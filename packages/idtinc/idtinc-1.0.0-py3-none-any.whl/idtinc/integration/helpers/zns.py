import json
import random

import requests


class ZNS:

    def __init__(
        self,
        api_url: str = "",
        zns_code: str = "",
        oa_id: str = "",
        secret_key: str = "",
        application_id: str = "",
        admin_phones: list = [],
    ):
        self.zns_code = zns_code
        self.admin_phones = admin_phones
        self.application_id = application_id
        self.secret_key = secret_key
        self.api_url = api_url
        self.oa_id = oa_id
        self.headers = {
            "Content-Type": "application/json",
            "X-Application-Id": self.application_id,
            "X-Secret-Key": self.secret_key,
        }

    @staticmethod
    def generate_code(length: int = 6) -> str:
        return str(random.randint(10 ** (length - 1), 10**length - 1))

    def send(self, phone: str, code: str = "", send_mode="production") -> dict:
        """_summary_

        Args:
            phone: Số điện thoại nhận mã xác thực
            code: Mã xác thực gửi đến người dùng. Mặc định "".
            send_mode: Chế độ gửi tin nhắn, có thể là "production" hoặc "development". Mặc định "production".
        Returns:
            dict: Kết quả gửi mã xác thực
        """
        send_mode = "development" if phone in self.admin_phones else "production"

        try:
            payload = {
                "oa": self.oa_id,
                "phone": phone,
                "payload": {
                    "otp": code,
                },
                "zns": self.zns_code,
                "mode": send_mode,
            }
            response = requests.request(
                "POST",
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
            )
            response_data = (response.json() or {}).get("data") or {}

            if response.status_code == 200:
                if response_data.get("error") not in [0, "0"]:
                    err_msg = response_data.get("message", "Lỗi khi gửi mã xác thực")
                    return {
                        "success": False,
                        "message": err_msg,
                        "data": {
                            "code": code,
                            "phone": phone,
                        },
                    }

                return {
                    "success": True,
                    "message": "Gửi mã xác thực thành công",
                    "data": {
                        "code": code,
                        "phone": phone,
                    },
                }

            return {
                "success": False,
                "message": "Lỗi khi gửi mã xác thực",
                "data": {
                    "code": code,
                    "phone": phone,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": {
                    "code": code,
                    "phone": phone,
                },
            }
