import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = "booking@example.com"
    sender_password: str = ""
    use_tls: bool = True

class EmailService:
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self.logger = logging.getLogger(__name__)
        
    async def send_booking_confirmation(self, booking_data: Dict[str, Any], recipient_email: str = "user@example.com") -> bool:
        """Send booking confirmation email"""
        try:
            subject = f"Booking Confirmation - {booking_data.get('service_type', 'Appointment')}"
            
            # Create email content
            html_content = self._create_confirmation_email_html(booking_data)
            text_content = self._create_confirmation_email_text(booking_data)
            
            # Send email
            success = await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                self.logger.info(f"Booking confirmation email sent to {recipient_email}")
            else:
                self.logger.error(f"Failed to send booking confirmation email to {recipient_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending booking confirmation email: {e}")
            return False
    
    async def send_reminder_email(self, booking_data: Dict[str, Any], recipient_email: str = "user@example.com") -> bool:
        """Send appointment reminder email"""
        try:
            subject = f"Appointment Reminder - {booking_data.get('service_type', 'Appointment')}"
            
            html_content = self._create_reminder_email_html(booking_data)
            text_content = self._create_reminder_email_text(booking_data)
            
            success = await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                self.logger.info(f"Reminder email sent to {recipient_email}")
            else:
                self.logger.error(f"Failed to send reminder email to {recipient_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending reminder email: {e}")
            return False
    
    async def _send_email(self, recipient_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = recipient_email
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            if self.config.sender_password:  # Real email sending
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        server.starttls()
                    server.login(self.config.sender_email, self.config.sender_password)
                    server.send_message(msg)
            else:  # Mock email sending for development
                self.logger.info(f"MOCK EMAIL SENT:")
                self.logger.info(f"To: {recipient_email}")
                self.logger.info(f"Subject: {subject}")
                self.logger.info(f"Content: {text_content[:200]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def _create_confirmation_email_html(self, booking_data: Dict[str, Any]) -> str:
        """Create HTML content for confirmation email"""
        service_type = booking_data.get('service_type', 'Appointment')
        date = booking_data.get('date', 'Unknown')
        time = booking_data.get('time', 'Unknown')
        duration = booking_data.get('duration_minutes', 60)
        confirmation_number = booking_data.get('confirmation_number', 'N/A')
        location = booking_data.get('location', 'Main Office')
        user_name = booking_data.get('user_name', 'Valued Customer')
        instructions = booking_data.get('instructions', 'Please arrive 5 minutes before your scheduled time.')
        cancellation_policy = booking_data.get('cancellation_policy', 'Free cancellation up to 24 hours before the appointment.')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #f9f9f9; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background-color: white; margin: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .booking-details {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #4CAF50; border-radius: 5px; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .detail-label {{ font-weight: bold; color: #555; }}
                .detail-value {{ color: #333; }}
                .important {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background-color: #f8f9fa; }}
                .confirmation-number {{ font-size: 18px; font-weight: bold; color: #4CAF50; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Booking Confirmed!</h1>
                    <p>Your appointment has been successfully scheduled</p>
                </div>
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Your <strong>{service_type}</strong> has been successfully booked!</p>
                    
                    <div class="confirmation-number">
                        Confirmation #: {confirmation_number}
                    </div>
                    
                    <div class="booking-details">
                        <h3>📋 Booking Details:</h3>
                        <div class="detail-row">
                            <span class="detail-label">Service Type:</span>
                            <span class="detail-value">{service_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date:</span>
                            <span class="detail-value">{date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Time:</span>
                            <span class="detail-value">{time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Duration:</span>
                            <span class="detail-value">{duration} minutes</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Location:</span>
                            <span class="detail-value">{location}</span>
                        </div>
                    </div>
                    
                    <div class="important">
                        <h4>📝 Important Information:</h4>
                        <p><strong>Instructions:</strong> {instructions}</p>
                        <p><strong>Cancellation Policy:</strong> {cancellation_policy}</p>
                    </div>
                    
                    <p>We look forward to seeing you!</p>
                    
                    <p>If you have any questions or need to make changes, please contact us at least 24 hours before your appointment.</p>
                </div>
                <div class="footer">
                    <p>This is an automated confirmation email. Please do not reply to this message.</p>
                    <p>© 2024 AI Booking Agent. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_confirmation_email_text(self, booking_data: Dict[str, Any]) -> str:
        """Create text content for confirmation email"""
        service_type = booking_data.get('service_type', 'Appointment')
        date = booking_data.get('date', 'Unknown')
        time = booking_data.get('time', 'Unknown')
        duration = booking_data.get('duration_minutes', 60)
        confirmation_number = booking_data.get('confirmation_number', 'N/A')
        location = booking_data.get('location', 'Main Office')
        user_name = booking_data.get('user_name', 'Valued Customer')
        instructions = booking_data.get('instructions', 'Please arrive 5 minutes before your scheduled time.')
        cancellation_policy = booking_data.get('cancellation_policy', 'Free cancellation up to 24 hours before the appointment.')
        
        text = f"""
BOOKING CONFIRMED!

Hello {user_name},

Your {service_type} has been successfully booked!

CONFIRMATION NUMBER: {confirmation_number}

BOOKING DETAILS:
================
Service Type: {service_type}
Date: {date}
Time: {time}
Duration: {duration} minutes
Location: {location}

IMPORTANT INFORMATION:
=====================
Instructions: {instructions}
Cancellation Policy: {cancellation_policy}

We look forward to seeing you!

If you have any questions or need to make changes, please contact us at least 24 hours before your appointment.

---
This is an automated confirmation email. Please do not reply to this message.
© 2024 AI Booking Agent. All rights reserved.
        """
        return text.strip()
    
    def _create_reminder_email_html(self, booking_data: Dict[str, Any]) -> str:
        """Create HTML content for reminder email"""
        service_type = booking_data.get('service_type', 'Appointment')
        date = booking_data.get('date', 'Unknown')
        time = booking_data.get('time', 'Unknown')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .reminder-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #FF9800; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Appointment Reminder</h1>
                </div>
                <div class="content">
                    <h2>Don't forget your upcoming {service_type}!</h2>
                    
                    <div class="reminder-details">
                        <h3>Appointment Details:</h3>
                        <p><strong>Service:</strong> {service_type}</p>
                        <p><strong>Date:</strong> {date}</p>
                        <p><strong>Time:</strong> {time}</p>
                    </div>
                    
                    <p>Please arrive 5 minutes before your scheduled time. If you need to reschedule or cancel, please contact us as soon as possible.</p>
                    
                    <p>We look forward to seeing you!</p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_reminder_email_text(self, booking_data: Dict[str, Any]) -> str:
        """Create text content for reminder email"""
        service_type = booking_data.get('service_type', 'Appointment')
        date = booking_data.get('date', 'Unknown')
        time = booking_data.get('time', 'Unknown')
        
        text = f"""
APPOINTMENT REMINDER

Don't forget your upcoming {service_type}!

Appointment Details:
- Service: {service_type}
- Date: {date}
- Time: {time}

Please arrive 5 minutes before your scheduled time. If you need to reschedule or cancel, please contact us as soon as possible.

We look forward to seeing you!

---
This is an automated reminder email. Please do not reply to this message.
        """
        return text.strip() 