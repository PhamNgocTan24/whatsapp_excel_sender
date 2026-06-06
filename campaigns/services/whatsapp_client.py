import requests
from django.conf import settings


class WhatsAppAPIError(Exception):
    """Raised when the WhatsApp Cloud API returns an error."""

    def __init__(self, message: str, response_payload: dict | None = None):
        self.response_payload = response_payload
        super().__init__(message)


class WhatsAppClient:
    """
    Thin wrapper around the WhatsApp Cloud API messages endpoint.
    Responsible for building the payload, sending the request,
    and raising WhatsAppAPIError on failure.
    """

    def __init__(self):
        self.access_token: str = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id: str = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version: str = settings.WHATSAPP_API_VERSION

    @property
    def _api_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}" f"/{self.phone_number_id}/messages"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str,
        body_params: list[str],
    ) -> dict:
        """
        Send a WhatsApp template message.

        Args:
            to_phone: Recipient phone in international format (no +).
            template_name: Approved WhatsApp template name.
            language_code: e.g. "en_US".
            body_params: List of string values for body component parameters.

        Returns:
            Parsed JSON response from the API.

        Raises:
            WhatsAppAPIError: On API error or network failure.
        """
        payload = self._build_payload(to_phone, template_name, language_code, body_params)

        try:
            response = requests.post(
                self._api_url,
                json=payload,
                headers=self._headers,
                timeout=20,
            )
        except requests.exceptions.Timeout:
            raise WhatsAppAPIError("WhatsApp API request timed out.")
        except requests.exceptions.RequestException as exc:
            raise WhatsAppAPIError(f"WhatsApp API request failed: {exc}")

        try:
            response_data = response.json()
        except Exception:
            response_data = {"raw": response.text}

        if not response.ok:
            error_msg = (
                response_data.get("error", {}).get("message", "Unknown API error")
                if isinstance(response_data, dict)
                else "Unknown API error"
            )
            raise WhatsAppAPIError(
                f"WhatsApp API error {response.status_code}: {error_msg}",
                response_payload=response_data,
            )

        return response_data

    def _build_payload(
        self,
        to_phone: str,
        template_name: str,
        language_code: str,
        body_params: list[str],
    ) -> dict:
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if body_params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in body_params],
                }
            ]

        return payload
