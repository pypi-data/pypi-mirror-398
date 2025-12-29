import time
import gspread
import pandas as pd
from gspread import utils
from datetime import date
from decimal import Decimal
from typing import Dict, Optional
from gspread.utils import ValueRenderOption
from oauth2client.service_account import ServiceAccountCredentials
from tenacity import (
    retry,
    wait_incrementing,
    stop_after_attempt,
)
from gspread_formatting import (
    format_cell_range,
    CellFormat,
    Color,
    TextFormat,
)


class GoogleDocs:
    def __init__(self, keyfile=None):
        """
        Initializes the GoogleDocs class with credentials for Google API.
        :param keyfile: Path to the JSON file containing Google service account credentials.
        Defaults to "./credentials.json" if not provided.
        """
        if keyfile is None:
            keyfile = "./credentials.json"

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
        self.spreadsheet = None
        self.gc = gspread.authorize(credentials)
        self.gc.set_timeout((300, 300))

    @staticmethod
    @retry(wait=wait_incrementing(start=60, increment=30, max=300), stop=stop_after_attempt(5))
    def safe_execute(func, *args, **kwargs):
        time.sleep(2)
        return func(*args, **kwargs)

    @staticmethod
    def serialize_value(value):
        if isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif pd.isna(value):
            return ""
        return value

    def format_worksheet(self, worksheet, headers):
        header_range = utils.rowcol_to_a1(1, 1) + ":" + utils.rowcol_to_a1(1, len(headers))
        header_format = CellFormat(
            backgroundColor=Color(201 / 255, 218 / 255, 248 / 255),
            textFormat=TextFormat(bold=True),
            verticalAlignment="MIDDLE",
            horizontalAlignment="CENTER",
            wrapStrategy="WRAP"
        )
        self.safe_execute(format_cell_range, worksheet, header_range, header_format)
        worksheet.freeze(rows=1)

    def get_dataframe(
            self, spreadsheet_key, worksheet_index=0, worksheet_title=None,
            value_render_option: Optional[ValueRenderOption] = None
    ) -> pd.DataFrame:
        """
        Returns a worksheet from a Google Spreadsheet as a pandas DataFrame.
        :param spreadsheet_key: ID of the Google Spreadsheet.
        :param worksheet_index: Index of the worksheet (default: 0).
        :param worksheet_title: Title of the worksheet (overrides index if set).
        :param value_render_option: (optional) Determines how values should
            be rendered in the output. See `ValueRenderOption`_ in
            the Sheets API.
        :return: pandas DataFrame with the worksheet data.
        """
        spreadsheet = self.gc.open_by_key(spreadsheet_key)
        if worksheet_title:
            worksheet = spreadsheet.worksheet(worksheet_title)
        else:
            worksheet = spreadsheet.get_worksheet(worksheet_index)
        data = worksheet.get_all_values(value_render_option=value_render_option)
        return pd.DataFrame(data[1:], columns=data[0])

    def init_spreadsheet(self, spreadsheet_key=None, spreadsheet_title=None, folder_id=None):
        if spreadsheet_key:
            return self.gc.open_by_key(spreadsheet_key)
        else:
            return self.gc.create(
                title=spreadsheet_title,
                folder_id=folder_id
            )

    def write_worksheet(self, dataframe, worksheet_title, default_dataframe_formatting):
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=worksheet_title, rows=100, cols=20)

        columns = dataframe.columns.values.tolist()
        values = dataframe.map(self.serialize_value).values.tolist()

        worksheet.clear()
        self.safe_execute(worksheet.update, [columns] + values)

        if default_dataframe_formatting and not dataframe.empty:
            columns = dataframe.columns.values.tolist()
            self.format_worksheet(worksheet=worksheet, headers=columns)

    def write_dataframe(
            self, dataframe: pd.DataFrame, worksheet_title, default_dataframe_formatting: bool = False,
            spreadsheet_key=None, spreadsheet_title=None, folder_id=None
    ):
        self.spreadsheet = self.init_spreadsheet(spreadsheet_key, spreadsheet_title, folder_id)
        self.write_worksheet(dataframe, worksheet_title, default_dataframe_formatting)

        if spreadsheet_key is None:
            self.spreadsheet.del_worksheet_by_id(0)

        return self.spreadsheet

    def write_dataframes(
            self, dataframes: Dict[str, pd.DataFrame], spreadsheet_key: str = None, spreadsheet_title: str = None,
            folder_id: str = None, default_dataframe_formatting: bool = False, drop_existing_sheets: bool = True
    ):
        self.spreadsheet = self.init_spreadsheet(spreadsheet_key, spreadsheet_title, folder_id)

        for worksheet_title in dataframes:
            self.write_worksheet(dataframes[worksheet_title], worksheet_title, default_dataframe_formatting)

        if drop_existing_sheets:
            for worksheet in self.spreadsheet.worksheets():
                if worksheet.title not in dataframes.keys():
                    self.spreadsheet.del_worksheet(worksheet)

        return self.spreadsheet
