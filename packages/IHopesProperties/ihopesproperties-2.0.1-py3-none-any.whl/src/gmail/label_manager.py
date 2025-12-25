from authenticate import authenticate
from typing import List

class LabelManager:
    def __init__(self, service = authenticate()):
        """
        Initialize the LabelManager instance.
        """
        self.service = service

    def add_label_to_email(self, message_id: str, label_names: List[str]):
        """
        Adds labels to an email and returns True if successful, otherwise False.
        :param message_id: ID of the email.
        :param label_names: List of label names to add.
        """
        try:
            # Step 1: Get the list of labels
            labels = self._get_labels()
            label_ids = []

            # Step 2: Find or create the label
            for label_name in label_names:
                label_id = None
                for label in labels:
                    if label["name"] == label_name:
                        label_id = label["id"]
                        break

                if not label_id:
                    new_label = self._create_label(label_name)
                    label_id = new_label["id"]

                label_ids.append(label_id)

            # Step 3: Add the label to the email
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": label_ids}
            ).execute()
            print(f"Labels {', '.join(label_names)} added successfully to email")
            return True
        except Exception as e:
            print(f"Error adding label: {e}")
            return False

    def _get_labels(self):
        """
        Retrieves all labels in the user's Gmail account.
        :return: List of labels.
        """
        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])
        return labels

    def _create_label(self, label_name):
        """
        Creates a new label.
        :param label_name: Name of the label.
        :return: Created label details.
        """
        label_body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        return self.service.users().labels().create(userId="me", body=label_body).execute()
