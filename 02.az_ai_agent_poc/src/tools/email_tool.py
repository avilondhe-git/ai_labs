"""
Email Tool using SendGrid API
Purpose: Enable agent to send email notifications
"""

from typing import Dict
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config.config import settings
from config.logger import app_logger as logger


class EmailTool:
    """
    Email sending tool powered by SendGrid
    
    WHY: SendGrid provides:
         - Reliable email delivery
         - Free tier (100 emails/day)
         - Simple API
         - Delivery tracking
    """
    
    def __init__(self):
        """Initialize SendGrid client"""
        
        if not settings.sendgrid_api_key:
            logger.warning("⚠️  SendGrid API key not set. Email tool disabled.")
            self.client = None
        else:
            self.client = SendGridAPIClient(settings.sendgrid_api_key)
            logger.info("EmailTool initialized")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = "agent@example.com"
    ) -> Dict:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email address
            
        Returns:
            Dictionary with send status
        """
        
        if not self.client:
            return {
                "success": False,
                "error": "Email tool not configured (missing API key)"
            }
        
        try:
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            
            response = self.client.send(message)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": f"Email sent successfully to {to_email}"
            }
            
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_definition(self) -> Dict:
        """Get tool definition for Semantic Kernel"""
        return {
            "name": "send_email",
            "description": "Send an email to a recipient. Use this to notify users, send reports, or deliver information via email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (plain text)"
                    }
                },
                "required": ["to_email", "subject", "body"]
            }
        }


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n📧 Testing Email Tool...")
    
    # Set API key for testing (get free key from https://sendgrid.com)
    # os.environ["SENDGRID_API_KEY"] = "your_key_here"
    
    tool = EmailTool()
    
    # Test email
    result = tool.send_email(
        to_email="test@example.com",
        subject="Test from AI Agent",
        body="This is a test email sent by the AI agent."
    )
    
    if result["success"]:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ Email failed: {result['error']}")
