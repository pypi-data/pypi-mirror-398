import base64
from email.mime.text import MIMEText
from typing import List, Optional
from authenticate import authenticate
from label_manager import LabelManager

# Import settings from consts file
from consts import EMAIL_ADDRESS

class EmailSender:
    def __init__(self):
        """
        Initialize the EmailSender instance.
        """
        self.email_address: str = EMAIL_ADDRESS

    def send_email(self, subject: str, body: str, recipient: List[str] = [EMAIL_ADDRESS], cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, label_names: Optional[List[str]] = None):
        """
        Sends an email using the Gmail API.
        :param recipient: Recipient email address.
        :param subject: Email subject.
        :param body: Email body content.
        :param cc: The CC recipient of the email.
        :param bcc: The BCC recipient of the email.
        :param label_names: Name of the labels to add to the email message.
        """
        raw_msg = self._create_message(subject, body, recipient, cc, bcc)
        service = authenticate()
        sent_message: dict[str, List[str]] = service.users().messages().send(userId="me", body=raw_msg).execute()
        print(f"Email sent successfully. Message ID: {sent_message['id']}")
        if label_names:
            LabelManager(service).add_label_to_email(sent_message['id'], label_names)

    def _create_message(self, subject: str, body: str, recipient: List[str] = EMAIL_ADDRESS, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> dict:
        """
        Creates an email message.
        :param recipient: Recipient email address.
        :param subject: Email subject.
        :param body: Email body content.
        :param cc: The CC recipient of the email.
        :param bcc: The BCC recipient of the email.
        :return: Encoded email message.
        """

        msg = MIMEText(body)
        msg['From'] = self.email_address
        msg['To'] = self.handel_email_addresses(recipient)
        if cc:
            msg['Cc'] = self.handel_email_addresses(cc)
        if bcc:
            msg['Bcc'] = self.handel_email_addresses(bcc)
        msg['Subject'] = subject
        return {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}


    @staticmethod
    def handel_email_addresses(addresses: List[str]) -> str:
        """
        Return a string of email addresses separated by commas.
        :param addresses: A list of email addresses.
        :return: A string of email addresses separated by commas.
        """
        return ", ".join(addresses)
