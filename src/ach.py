import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from src.util import create_cache_dir, cache

CREDENTIALS_PATH_GOOGLE = 'google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET = '1nkczsf-EeEWVzoNjD3UdB2Xr2W4jD7YEXD_ImRbXHNc'  # GARY SHEETS
ACH_SHEETS = "achmusik.pkl"


class Ach:

    def __init__(self):
        create_cache_dir()

    def __load_from_cache(self):
        return pd.read_pickle(cache(ACH_SHEETS))

    def __load_from_google(self):
        # Load service account credentials.
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH_GOOGLE, scopes=SCOPES)

        # Creates Google Sheets API (v4/latest) service.
        service = build('sheets', 'v4', credentials=credentials)
        # Gets values from Ach! Musik: Notations sheet.
        values = service.spreadsheets().values()\
            .get(spreadsheetId=SPREADSHEET, range='Notations')\
            .execute()['values']
        headers = values.pop(0)
        ach = pd.DataFrame.from_records(values)
        if ach.shape[1] > len(headers):
            ach.drop(ach.columns[len(headers):], axis=1, inplace=True)
        # Format data as pd.DataFrame
        ach.columns = headers
        ach.set_index(['genre', 'sub_genre', 'artist', 'album', 'song'],
                      inplace=True)
        return ach

    def get_sheets(self):
        try:
            ach = self.__load_from_google()
            ach.to_pickle(cache(ACH_SHEETS))
        except Exception:
            ach = self.__load_from_cache()
        return ach

    def update_missing(self, missing):
        pass
