import time

import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from src.util import create_cache_dir, cache

CREDENTIALS_PATH_GOOGLE = 'google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET = '1b75J-QTGrujSgF9r0_JPOKkcXAwzFVwpETOAyVBw8ak'
ACH_SHEETS = "achmusik.pkl"
ACH_SHEET_NAME = "Notations"
ACH_SHEET_ID = 0
API_PREFIX = "api:"


class Ach:

    def __init__(self):
        create_cache_dir()

    def __check_empty_row(self):
        df_index = self.ach.index.to_frame(index=False)
        empty = df_index[
            df_index.replace(r"^\s$", value=np.NaN, regex=True)
                    .isnull()
                    .all(axis=1)
        ].index
        if len(empty) > 0:
            print("WARNING some empty rows in the datasheet:")
            for idx in empty:
                print(f"Empty row at index {idx + 2}")

    def __check_for_duplicates(self):
        duplicates = self.ach.index[self.ach.index.duplicated()].tolist()
        if len(duplicates) > 0:
            print("WARNING some duplicated in the datasheet:")
            for duplicate in duplicates:
                print(duplicate)

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
            .get(spreadsheetId=SPREADSHEET, range=ACH_SHEET_NAME)\
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
        self.updated = False
        try:
            self.ach = self.__load_from_google()
            self.ach.to_pickle(cache(ACH_SHEETS))
            self.updated = True
        except Exception:
            print("Error while reading from google")
            self.ach = self.__load_from_cache()
        self.__check_empty_row()
        self.__check_for_duplicates()
        return self.ach

    def update_missing(self, ids: pd.Series, api_name):
        if not self.updated:
            raise Exception("Cannot update tracks from a not "
                            "updated version of the sheet")
        print("Updating missing songs...")
        ordered_index = self.ach.index
        column = self.api_columns[f"{API_PREFIX}{api_name}"]
        ids_strings = ids.reindex(ordered_index, fill_value="none")
        payload = {
            "majorDimension": "ROWS",
            "values": ids_strings.values.reshape(-1, 1).tolist()
        }
        range_ = (f"{ACH_SHEET_NAME}!{column['letter']}2:"
                  f"{column['letter']}{len(ids_strings)+1}")
        self.service.spreadsheets()\
                    .values()\
                    .update(spreadsheetId=SPREADSHEET,
                            range=range_,
                            valueInputOption="RAW",
                            body=payload)\
                    .execute()
        self.__update_cell_note(column)

    def __update_cell_note(self, column):
        print("Updating update note...")
        note = f"Last updated : {time.ctime()}"
        notes = {
            "updateCells": {
                "fields": "note",
                "range": {
                    "sheetId": ACH_SHEET_ID,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": column['index'],
                    "endColumnIndex": column['index'] + 1
                },
                "rows": [
                    {
                        "values": [
                            {
                                "note": note
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
