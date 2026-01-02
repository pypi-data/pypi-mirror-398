from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
from typing import Any

class GmailAuthenticatedContext:
    """
    A context manager for managing the authentication and retrieval of Gmail messages.

    Args:
        token_path (str): The path to the token file for storing the authentication token. Default is 'config/gmail_token.pickle'.
        creds_path (str): The path to the credentials file for Gmail API. Default is 'config/gmail_credentials.json'.
        scopes (tuple): The OAuth 2.0 scopes for the Gmail API. Default is ('https://www.googleapis.com/auth/gmail.readonly',).

    Methods:
        __enter__(): Enters the context and authenticates the Gmail API client.
        __exit__(exc_type, exc_val, exc_tb): Exits the context.
        get_messages_since_history_id(history_id, label_id): Retrieves the messages added since the specified history ID for a given label.
        authenticate(): Authenticates the Gmail API client.

    """

    def __init__(self, token_path='config/gmail_token.pickle', creds_path='config/gmail_credentials.json', scopes=('https://www.googleapis.com/auth/gmail.readonly',)):
        self.token_path = token_path
        self.creds_path = creds_path
        self.scopes = scopes

    def __enter__(self):
        self.creds = self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_label_id(self, label_name: str) -> str:
        """
        Retrieves the label ID for a given label name.

        Args:
            label_name (str): The name of the label.

        Returns:
            str: The ID of the label if found, None otherwise.
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            results = service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve label ID for '{label_name}'") from e
        
        return None
    def get_messages_since_history_id(self, history_id: int, label_name: str) -> list:
        """
        Retrieves the messages added since the specified history ID for a given label name.

        Args:
            history_id (int): The history ID to start retrieving changes from.
            label_name (str): The name of the label to filter the changes.

        Returns:
            list: A list of message objects that were added since the specified history ID.
        """
        label_id = self.get_label_id(label_name)
        if not label_id:
            raise RuntimeError(f"Failed to retrieve label ID for '{label_name}'")

        # Use history.list to get the change details
        service = build('gmail', 'v1', credentials=self.creds)
        try:
            results = service.users().history().list(userId='me', startHistoryId=history_id).execute()
            changes = results.get('history', [])

            # Get the body of the messages added
            messages = []
            for change in changes:
                messages_added = change.get('messagesAdded', [])
                for message_added in messages_added:
                    message_id = message_added['message']['id']
                    message = service.users().messages().get(userId='me', id=message_id).execute()
                    messages.append(message)

            return messages
        except Exception as e:
            raise RuntimeError("Failed to retrieve messages") from e

    def authenticate(self) -> Any:
        """
        Authenticates the user and returns the credentials.

        Returns:
            The credentials object after authentication.
        """
        creds: Any = None

        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_path, self.scopes)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds
