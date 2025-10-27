import requests
import json
import logging
from typing import Dict, List, Optional, Any
from flask import current_app
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppService:
    """WhatsApp Business API service for sending and receiving messages"""
    
    def __init__(self):
        self.access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = current_app.config.get('WHATSAPP_BASE_URL')
        self.api_version = current_app.config.get('WHATSAPP_API_VERSION', 'v22.0')
        
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured properly")
    
    def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message to a WhatsApp number"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"WhatsApp message sent successfully to {to}")
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(self, to: str, template_name: str, language_code: str = "en_US", components: List[Dict] = None) -> Dict[str, Any]:
        """Send a template message to a WhatsApp number"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"WhatsApp template message sent successfully to {to}")
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp template message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp template message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_interactive_message(self, to: str, header_text: str, body_text: str, footer_text: str = None, buttons: List[Dict] = None) -> Dict[str, Any]:
        """Send an interactive message with buttons"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            interactive_data = {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": body_text
                }
            }
            
            if footer_text:
                interactive_data["footer"] = {
                    "text": footer_text
                }
            
            if buttons:
                interactive_data["action"] = {
                    "buttons": buttons
                }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": interactive_data
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"WhatsApp interactive message sent successfully to {to}")
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp interactive message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp interactive message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_webhook_message(self, webhook_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse incoming WhatsApp webhook message"""
        try:
            if webhook_data.get('field') != 'messages':
                return None
            
            value = webhook_data.get('value', {})
            messages = value.get('messages', [])
            contacts = value.get('contacts', [])
            
            if not messages or not contacts:
                return None
            
            message = messages[0]
            contact = contacts[0]
            
            # Extract message details
            parsed_message = {
                'message_id': message.get('id'),
                'from': message.get('from'),
                'timestamp': message.get('timestamp'),
                'type': message.get('type'),
                'contact_name': contact.get('profile', {}).get('name'),
                'wa_id': contact.get('wa_id'),
                'text': None,
                'raw_message': message
            }
            
            # Extract text content if it's a text message
            if message.get('type') == 'text' and 'text' in message:
                parsed_message['text'] = message['text'].get('body')
            
            return parsed_message
            
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook message: {str(e)}")
            return None
    
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"WhatsApp message {message_id} marked as read")
            return {
                'success': True,
                'response': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to mark WhatsApp message as read: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error marking WhatsApp message as read: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """Get media URL from media ID"""
        try:
            url = f"{self.base_url}/{media_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('url')
            
        except Exception as e:
            logger.error(f"Failed to get media URL: {str(e)}")
            return None
    
    def download_media(self, media_url: str) -> Optional[bytes]:
        """Download media from WhatsApp"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to download media: {str(e)}")
            return None
