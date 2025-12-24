import httpx
from hiws.types.exceptions import WhatsappApiException
from hiws.types import Contact
from typing import Optional, Any, Dict, overload
from hiws.internal.helpers import amake_cloud_api_request


BASE_URL = "https://graph.facebook.com/{API_VERSION}"
MESSAGES_ENDPOINT = "/{phone_number_id}/messages"
MEDIA_ENDPOINT = "/{phone_number_id}/media"
DEFAULT_TIMEOUT = 15.0


class WhatsappMessenger:
    """
    A class to interact with the WhatsApp Cloud API.
    
    Attributes:
        access_token (str): The access token for authentication.
        phone_number_id (str): The phone number ID associated with the WhatsApp Business account.
        api_version (str): The version of the WhatsApp API to use.
        request_timeout (float): Timeout for HTTP requests in seconds. Default is 15.0 seconds.
    """

    access_token: str
    phone_number_id: str
    api_version: str
    request_timeout: float = DEFAULT_TIMEOUT

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        api_version: str = "v23.0",
        request_timeout: float = DEFAULT_TIMEOUT,
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = BASE_URL.format(API_VERSION=self.api_version)
        self.messages_endpoint = MESSAGES_ENDPOINT.format(phone_number_id=self.phone_number_id)
        self.media_endpoint = MEDIA_ENDPOINT.format(phone_number_id=self.phone_number_id)
        self.request_timeout = request_timeout
        self.default_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text(
        self, 
        recipient_phone_number: str, 
        text: str, 
        enable_link_preview: bool = True,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a text message.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            text (str): The text message to send.
            enable_link_preview (bool): Whether to enable link preview. Default is True.
            reply_to (Optional[str]): Message ID to reply to. Default is None.
            
        Returns:
            str: The message ID of the sent message.
            
        Raises:
            WhatsappApiException: If there is an error sending the message.
            
        ## Note
            WhatsApp Cloud API has a limit of 4096 characters for text messages.
            Messages longer than this will not be sent.
            
        ## Documentation
            https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone_number,
            "type": "text",
            "text": {"preview_url": enable_link_preview, "body": text},
        }
        
        if reply_to:
            payload["context"] = {"message_id": reply_to}

        return await self._send_message_payload(payload)

    async def send_image(
        self,
        recipient_phone_number: str,
        image_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send an image.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            image_link (Optional[str]): The URL of the image to send. Default is None.
            media_id (Optional[str]): The media ID of a previously uploaded image. Default is None.
            caption (Optional[str]): Caption for the image. Default is None.
            reply_to (Optional[str]): Message ID to reply to. Default is None.
        Returns:
            str: The message ID of the sent message.
        Raises:
            ValueError: If neither image_link nor media_id is provided.
            WhatsappApiException: If there is an error sending the message.
        ## Note
            Supported formats: JPEG, PNG.
            Max file size: 5 MB.
        ## Documentation
            https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages
        """
        return await self._send_media(
            media_type="image",
            media_link=image_link,
            media_id=media_id,
            caption=caption,
            recipient_phone_number=recipient_phone_number,
            reply_to=reply_to
        )

    async def send_document(
        self,
        recipient_phone_number: str,
        document_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a document.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            document_link (Optional[str]): The URL of the document to send. Default is None.
            media_id (Optional[str]): The media ID of a previously uploaded document. Default is None.
            caption (Optional[str]): Caption for the document. Default is None.
            filename (Optional[str]): Filename for the document. Default is None.
            reply_to (Optional[str]): Message ID to reply to. Default is None.
        Returns:
            str: The message ID of the sent message.
        Raises:
            ValueError: If neither document_link nor media_id is provided.
            WhatsappApiException: If there is an error sending the message.
        ## Note
            Supported formats: PDF, XLS, XLSX, DOC, DOCX, PPT, PPTX, TXT.
            Max file size: 100 MB.
        ## Documentation
            https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages
        """
        return await self._send_media(
            media_type="document",
            media_link=document_link,
            media_id=media_id,
            caption=caption,
            filename=filename,
            recipient_phone_number=recipient_phone_number,
            reply_to=reply_to
        )
        
    async def send_audio(
        self,
        recipient_phone_number: str,
        audio_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send an audio message.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            audio_link (Optional[str]): The URL of the audio to send. Default is None.
            media_id (Optional[str]): The media ID of a previously uploaded audio. Default is None.
            caption (Optional[str]): Caption for the audio. Default is None.
            reply_to (Optional[str]): Message ID to reply to. Default is None.
        Returns:
            str: The message ID of the sent message.
        Raises:
            ValueError: If neither audio_link nor media_id is provided.
            WhatsappApiException: If there is an error sending the message.
        ## Note
            Supported formats: AAC, AMR, MP3, M4A, OGG (only OPUS codec).
            Max file size: 16 MB.
        """
        return await self._send_media(
            media_type="audio",
            media_link=audio_link,
            media_id=media_id,
            caption=caption,
            recipient_phone_number=recipient_phone_number,
            reply_to=reply_to
        )
        
    async def send_video(
        self,
        recipient_phone_number: str,
        video_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a video message.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            video_link (Optional[str]): The URL of the video to send. Default is None.
            media_id (Optional[str]): The media ID of a previously uploaded video. Default is None.
            caption (Optional[str]): Caption for the video. Default is None.
            reply_to (Optional[str]): Message ID to reply to. Default is None.
        Returns:
            str: The message ID of the sent message.
        Raises:
            ValueError: If neither video_link nor media_id is provided.
            WhatsappApiException: If there is an error sending the message.
        ## Note
            Supported formats: MP4, 3GPP.
            Max file size: 16 MB.
        ## Documentation
            https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages
        """
        return await self._send_media(
            media_type="video",
            media_link=video_link,
            media_id=media_id,
            caption=caption,
            recipient_phone_number=recipient_phone_number,
            reply_to=reply_to
        )
        
    async def send_contact(
        self,
        recipient_phone_number: str,
        contact: Contact | Dict[str, Any],
    ) -> str:
        """
        Send a contact message.
        Args:
            recipient_phone_number (str): The recipient's phone number in international format (without leading '+').
            contact (Contact | Dict[str, Any]): The contact information to send.
        Returns:
            str: The message ID of the sent message.
        Raises:
            ValueError: If contact is invalid.
            WhatsappApiException: If there is an error sending the message.
        """
        if isinstance(contact, Contact):
            contact = contact.model_dump(mode="json", exclude_none=True)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone_number,
            "type": "contact",
            "contact": contact,
        }

        return await self._send_message_payload(payload)

    async def mark_as_read(
        self,
        message_id: str
    ) -> None:
        """
        Mark a message as read.
        Args:
            message_id (str): The ID of the message to mark as read.
        Returns:
            str: The message ID of the read receipt.
        Raises:
            WhatsappApiException: If there is an error sending the read receipt.
        ## Documentation
            https://developers.facebook.com/docs/whatsapp/cloud-api/guides/mark-message-as-read
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        await self._send_mark_as_read_payload(payload)

    async def send_typing_indicator(
        self,
        message_id: str
    ) -> None:
        """
        Send a typing indicator.
        Args:
            message_id (str): The ID of the message to which the typing indicator relates. This message will be marked as read.
        Returns:
            str: The message ID of the typing indicator.
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
            "typing_indicator": {
                "type": "text",
            }
        }
        
        await self._send_mark_as_read_payload(payload)

    async def get_media_url(
        self,
        media_id: str,
    ) -> str:
        url = f"{self.base_url}/{media_id}"
        
        response = await amake_cloud_api_request(
            "GET",
            url,
            self.default_headers
        )
        
        try: 
            data = response.json()
            return data.get("url")
        except Exception as e:
            raise WhatsappApiException(
                message="Failed to parse JSON response",
                endpoint=self.messages_endpoint,
                method="POST",
                payload=None,
                status_code=response.status_code,
                details=str(e),
            ) from e
            
    @overload     
    async def query_media_url(
        self,
        media_url: str,
    ) -> bytes:
        pass
    
    @overload
    async def query_media_url(
        self,
        media_url: str,
        file_path: str
    ) -> None:
        pass
            
    async def query_media_url(
        self,
        media_url: str,
        file_path: Optional[str] = None
    ) -> Optional[bytes]:
        response = await amake_cloud_api_request(
            "GET",
            media_url,
            self.default_headers
        )
        if file_path:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return None
        else:
            return response.content

    async def _send_media(
        self,
        recipient_phone_number: str,
        media_type: str,
        media_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        if not media_link and not media_id:
            raise ValueError("Either media_link or media_id must be provided.")

        media_payload = {}
        if media_link:
            media_payload["link"] = media_link
        if media_id:
            media_payload["id"] = media_id
        if caption:
            media_payload["caption"] = caption
        if filename and media_type == "document":
            media_payload["filename"] = filename

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone_number,
            "type": media_type,
            media_type: media_payload,
        }
        
        if reply_to:
            payload["context"] = {"message_id": reply_to}

        return await self._send_message_payload(payload)

    async def _send_message_payload(self, payload: dict) -> str:
        """
        Send a custom payload to WhatsApp's API messages endpoint with robust error handling.

        Args:
            payload (dict): The payload to send.
            timeout (Optional[float]): Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            SendResponse: A mapping with at least the "message_id" and, when available, "recipient_id".

        Raises:
            WhatsappApiException: For network errors, non-2xx responses, or malformed responses.
        """
        url = f"{self.base_url}{self.messages_endpoint}"
        response = await self._send_payload(self.messages_endpoint, payload)
        
        try:
            data = response.json()
        except ValueError as e:
            raise WhatsappApiException(
                message="Failed to parse JSON response",
                endpoint=self.messages_endpoint,
                method="POST",
                payload=payload,
                status_code=response.status_code,
                details=str(e),
            ) from e

        try:
            message_id = data["messages"][0]["id"]
        except (IndexError, KeyError):
            raise WhatsappApiException(
                message="Missing message_id in successful response",
                endpoint=url,
                method="POST",
                payload=payload,
                status_code=response.status_code,
                response_json=data,
            )

        return message_id

    async def _send_mark_as_read_payload(self, payload: dict) -> None: 
        response = await self._send_payload(self.messages_endpoint, payload)
        try:
            data = response.json()
        except ValueError as e:
            raise WhatsappApiException(
                message="Failed to parse JSON response",
                endpoint=self.messages_endpoint,
                method="POST",
                payload=payload,
                status_code=response.status_code,
                details=str(e),
            ) from e
        success = data.get("success")
        if not success:
            raise WhatsappApiException(
                message="Failed to mark message as read",
                endpoint=self.messages_endpoint,
                method="POST",
                payload=payload,
                status_code=response.status_code,
                response_json=data,
            )

    async def _send_payload(self, endpoint: str, payload: dict) -> httpx.Response:
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.post(url, json=payload, headers=self.default_headers)
        except httpx.RequestError as e:
            raise WhatsappApiException(
                message="Network error while sending payload",
                endpoint=url,
                method="POST",
                payload=payload,
                details=str(e),
            ) from e

        # Non-2xx -> raise a structured exception with parsed error body when possible
        if response.status_code < 200 or response.status_code >= 300:
            raise WhatsappApiException.from_httpx_response(
                response,
                endpoint=url,
                method="POST",
                payload=payload,
            )

        return response
