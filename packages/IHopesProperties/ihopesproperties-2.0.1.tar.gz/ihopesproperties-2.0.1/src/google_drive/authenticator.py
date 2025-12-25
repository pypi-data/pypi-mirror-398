import os
import pickle
import sys
from functools import lru_cache
from pathlib import Path
from typing import Tuple, Optional
from functools import lru_cache

from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build, Resource
import streamlit as st

from common.utils.logger import log


def is_streamlit_runtime() -> bool:
    """
    Check if the script is running in a Streamlit runtime environment.
    :return:
    """
    return any("streamlit" in arg for arg in sys.argv)


CACHE_DECORATOR = st.cache_resource if is_streamlit_runtime() else lru_cache(maxsize=1)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class GoogleServices(metaclass=SingletonMeta):
    def __init__(self):
        self._creds = None
        self.drive: Optional[Resource] = None
        self.sheets: Optional[Resource] = None

        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        self.authenticate()

    def authenticate(self) -> None:
        # Authenticate and create the service
        import streamlit as st
        print("Authenticating with Google Drive and Sheets API...")
        creds = None
        # The file token.pickle stores the user's access and refresh tokens.
        parent_path: Path = Path(os.path.abspath(__file__)).parent
        token_file_path: Path = Path(parent_path, 'token.pickle')

        os_path_exists = os.path.exists(token_file_path)
        if os_path_exists:
            print("Loading credentials from token.pickle")
            with open(token_file_path, 'rb') as token:
                # from google.oauth2.credentials import Credentials
                # creds2 = Credentials.from_authorized_user_file('token.json', scopes=['your-scopes'])
                creds = pickle.load(token)
                print("Credentials loaded successfully.")
        else:
            print("token.pickle file not found. Starting authentication process.")

        if not creds or not creds.valid:
            try:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                log(msg="Authenticated successfully to Google Drive and Sheets API.")
            except Exception as e:
                st.write("Canot do refresh ")
            if not creds or not creds.valid:
                print("Credentials not found or invalid. Starting authentication process.")
                st.write("Credentials not found or invalid. Starting authentication process.")
                if is_streamlit_runtime():
                    print("Running in Streamlit runtime. Using OAuth 2.0 authorization flow.")
                    # Define your redirect URI based on Streamlit Cloud
                    streamlit_base_url = "https://leads-generator-ihopes25to40.streamlit.app"
                    redirect_uri = f"{streamlit_base_url}/"

                    flow = Flow.from_client_secrets_file(
                        client_secrets_file=str(parent_path / 'credentials.json'),
                        scopes=self.scopes,
                        redirect_uri=redirect_uri
                    )

                    auth_url, _ = flow.authorization_url(
                        prompt='consent',
                        access_type='offline',
                        include_granted_scopes='true'
                    )

                    st.markdown("### 🔐 Google Authentication Required")
                    st.markdown(f"[Click here here here here here to authenticate]({auth_url})")
                    code = st.text_input("Paste the authorization code from the URL after granting access:")

                    if code:
                        try:
                            flow.fetch_token(code=code)
                            creds = flow.credentials
                            with open(token_file_path, 'wb') as token:
                                pickle.dump(creds, token)
                            st.success("✅ Authentication successful!")
                        except Exception as e:
                            st.error(f"❌ Authentication failed: {e}")
                    else:
                        st.stop()
                else:
                    print("Running outside Streamlit runtime. Using local server for authentication.")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file=f'{parent_path}/credentials.json',
                        scopes=self.scopes,
                    )
                    creds = flow.run_local_server(port=8080)
                    with open(token_file_path, 'wb') as token:
                        pickle.dump(creds, token)

        # Build the Drive API service
        self.drive: Resource = build('drive', 'v3', credentials=creds)
        self.sheets: Resource = build('sheets', 'v4', credentials=creds)


def get_google_services() -> GoogleServices:
    return GoogleServices()
