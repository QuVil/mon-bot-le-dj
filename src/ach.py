import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from src.util import create_cache_dir, cache

CREDENTIALS_PATH_GOOGLE = 'google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET = '1nkczsf-EeEWVzoNjD3UdB2Xr2W4jD7YEXD_ImRbXHNc'  # GARY SHEETS
ACH_SHEETS = "achmusik.pkl"
API_PREFIX = "api:"


class Ach:

    def __init__(self):
        create_cache_dir()

    def __column_to_letter(self, idx):
        character = chr(ord('A') + idx % 26)
        remainder = idx // 26
        if idx >= 26:
            return self.__column_to_letter(remainder-1) + character
        else:
            return character

    def __get_api_columns(self, headers):
        api_col = {}
        for idx, name in enumerate(headers):
            if API_PREFIX in name:
                api_col[name] = {
                    "letter": self.__column_to_letter(idx),
                    "index": idx
                }
        self.api_columns = api_col
        print(self.api_columns)

    def __drop_api_columns(self, ach):
        return ach.drop(self.api_columns, axis=1)

    def __load_from_cache(self):
        print("Reading from cache")
        return pd.read_pickle(cache(ACH_SHEETS))

    def __load_from_google(self):
        # Load service account credentials.
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH_GOOGLE, scopes=SCOPES)

        # Creates Google Sheets API (v4/latest) service.
        self.service = build('sheets', 'v4', credentials=credentials)
        # Gets values from Ach! Musik: Notations sheet.
        values = self.service.spreadsheets().values()\
            .get(spreadsheetId=SPREADSHEET, range='Notations')\
            .execute()['values']
        headers = values.pop(0)
        self.__get_api_columns(headers)
        ach = pd.DataFrame.from_records(values)
        if ach.shape[1] > len(headers):
            ach.drop(ach.columns[len(headers):], axis=1, inplace=True)
        # Format data as pd.DataFrame
        ach.columns = headers
        ach.set_index(['genre', 'sub_genre', 'artist', 'album', 'song'],
                      inplace=True)
        ach = self.__drop_api_columns(ach)
        return ach

    def get_sheets(self):
        try:
            ach = self.__load_from_google()
            ach.to_pickle(cache(ACH_SHEETS))
        except Exception:
            print("Error while reading from google")
            ach = self.__load_from_cache()
        return ach

    def update_missing(self, ids):
        column = self.api_columns["api:Spotify"]
        range_ = f"{ACH_SHEET_NAME}!{column['letter']}2:"\
            f"{column['letter']}{len(ids)+1}"
        ordered_index = self.__load_from_cache().index
        ids_strings = ids.fillna("none").reindex(ordered_index)
        payload = {
            "majorDimension": "ROWS",
            "values": ids_strings.values.reshape(-1, 1).tolist()
        }
        print(range_)
        print("lol")
        self.service.spreadsheets()\
                    .values()\
                    .update(spreadsheetId=SPREADSHEET,
                            range=range_,
                            valueInputOption="RAW",
                            body=payload)\
                    .execute()
        self.__update_cell_note(column)

    def __update_cell_note(self, column):
        notes = {
            "updateCells": {
                "fields": "note",
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": column['index'],
                    "endColumnIndex": column['index'] + 1
                },
                "rows": [
                    {
                        "values": [
                            {
                                "note": "my note"
                            }
                        ]
                    }
                ],
            }
        }
        body = {"requests": [notes]}
        self.service.spreadsheets()\
            .batchUpdate(spreadsheetId=SPREADSHEET,
                         body=body)\
            .execute()
