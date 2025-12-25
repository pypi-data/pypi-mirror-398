import requests
import os
from typing import Optional, Dict, Any

class SafeCommsClient:
    def __init__(self, api_key: str, base_url: str = "https://api.safecomms.dev"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def moderate_text(self, content: str, language: str = "en", replace: bool = False, pii: bool = False, replace_severity: Optional[str] = None, moderation_profile_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Moderate text content.
        """
        payload = {
            "content": content,
            "language": language,
            "replace": replace,
            "pii": pii,
            "replaceSeverity": replace_severity,
            "moderationProfileId": moderation_profile_id
        }
        response = self.session.post(f"{self.base_url}/moderation/text", json=payload)
        response.raise_for_status()
        return response.json()

    def moderate_image(self, image: str, language: str = "en", moderation_profile_id: Optional[str] = None, enable_ocr: bool = False, enhanced_ocr: bool = False, extract_metadata: bool = False) -> Dict[str, Any]:
        """
        Moderate image content.
        """
        payload = {
            "image": image,
            "language": language,
            "moderationProfileId": moderation_profile_id,
            "enableOcr": enable_ocr,
            "enhancedOcr": enhanced_ocr,
            "extractMetadata": extract_metadata
        }
        response = self.session.post(f"{self.base_url}/moderation/image", json=payload)
        response.raise_for_status()
        return response.json()

    def moderate_image_file(self, file_path: str, language: str = "en", moderation_profile_id: Optional[str] = None, enable_ocr: bool = False, enhanced_ocr: bool = False, extract_metadata: bool = False) -> Dict[str, Any]:
        """
        Moderate image file.
        """
        with open(file_path, 'rb') as f:
            files = {'image': (os.path.basename(file_path), f)}
            data = {
                'language': language,
                'enableOcr': str(enable_ocr).lower(),
                'enhancedOcr': str(enhanced_ocr).lower(),
                'extractMetadata': str(extract_metadata).lower()
            }
            if moderation_profile_id:
                data['moderationProfileId'] = moderation_profile_id
            
            # Unset Content-Type so requests can set it to multipart/form-data
            headers = {"Content-Type": None}
            
            response = self.session.post(f"{self.base_url}/moderation/image/upload", files=files, data=data, headers=headers)
            response.raise_for_status()
            return response.json()

    def get_usage(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        """
        response = self.session.get(f"{self.base_url}/usage")
        response.raise_for_status()
        return response.json()
