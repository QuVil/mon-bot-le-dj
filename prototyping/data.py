import pandas as pd

# from oauth2client.service_account import ServiceAccountCredentials 
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

CREDENTIALS_PATH_GOOGLE = 'google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET = '1b75J-QTGrujSgF9r0_JPOKkcXAwzFVwpETOAyVBw8ak'

DATA_PATH = "data/csv/achmusik.csv"
TRANSITIONS_PATH = "data/csv/transitions.csv"

def load_from_api(sheet="Notations", fallback=DATA_PATH):
    try:
        # Load service account credentials.
        __credentials = Credentials.from_service_account_file(CREDENTIALS_PATH_GOOGLE, scopes=SCOPES)

        # Creates Google Sheets API (v4/latest) service.
        service = build('sheets', 'v4', credentials=__credentials)
        # Gets values from Ach! Musik: Notations sheet.
        values = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET, range=sheet).execute()['values']
        headers = values.pop(0)
        # Format data as pd.DataFrame
        return pd.DataFrame(values, columns=headers)
    except Exception as ex:
        print("No valid Google credentials found or fetch exception. Falling back on csv file...")
        return load_from_cache(fallback)


def load_from_cache(fallback=DATA_PATH):
    return pd.read_csv(fallback)


if __name__ == '__main__':
    print(load_from_api())
