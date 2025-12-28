import pandas as pd
import requests
from typing import List, Dict, Any

class LarkSheetAPI:
    def __init__(self, access_token: str, spreadsheet_token: str, sheet_id: str):
        """
        Initializes the LarkSheetAPI client.
        allow interaction with Lark sheets.

        Args:
            access_token: Your Lark API access token.
            spreadsheet_token: The token of the spreadsheet.
            sheet_id: The ID of the specific sheet within the spreadsheet.
        """
        self.access_token = access_token
        self.spreadsheet_token = spreadsheet_token
        self.sheet_id = sheet_id
        self.base_url = "https://open.larksuite.com/open-apis"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def _get_range(self, data_range: str) -> str:
        """Constructs the full range string including sheetId."""
        return f"{self.sheet_id}!{data_range}"

    def read_sheet_to_dataframe(self, data_range: str = "A1:LAST_CELL") -> pd.DataFrame:
        """
        Reads data from a specified range in the Lark sheet and returns a pandas DataFrame.

        Args:
            data_range: The range of cells to read (e.g., "A1:D10"). Defaults to reading all data.

        Returns:
            A pandas DataFrame containing the data from the sheet.
            Returns an empty DataFrame if the sheet is empty or the range is invalid.
        """
        url = f"{self.base_url}/sheets/v2/spreadsheets/{self.spreadsheet_token}/values/{self._get_range(data_range)}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status() # Raise an exception for bad status codes

        data = response.json()
        if data.get("code") == 0 and data.get("data") and data["data"].get("valueRange"):
            values = data["data"]["valueRange"].get("values", [])
            if not values:
                return pd.DataFrame()

            # Assuming the first row is the header
            header = values[0]
            sheet_data = values[1:]
            return pd.DataFrame(sheet_data, columns=header)
        else:
            print(f"Error reading sheet: {data.get('msg', 'Unknown error')}")
            return pd.DataFrame()

    def append_row(self, row_data: List[Any], insert_data_option: str = "OVERWRITE") -> Dict[str, Any]:
        """
        Appends a new row of data to the end of the sheet.

        Args:
            row_data: A list of values representing the new row.
            insert_data_option: How to handle appending data when blank rows are encountered.
                                 "OVERWRITE" (default) or "INSERT_ROWS".

        Returns:
            The JSON response from the API.
        """
        url = f"{self.base_url}/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_append"
        payload = {
            "valueRange": {
                "range": self._get_range("A1"), # Specify a range within the sheet
                "values": [row_data]
            },
            "insertDataOption": insert_data_option
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def update_row(self, row_index: int, row_data: List[Any]) -> Dict[str, Any]:
        """
        Updates an existing row in the sheet.

        Args:
            row_index: The index of the row to update (0-based).
            row_data: A list of values to update the row with.

        Returns:
            The JSON response from the API.
        """
        # To update a specific row, we need to specify the range for that row
        # For example, if updating row 5 (index 4), the range would be Sheet1!A5: wherever the data ends
        # A simpler approach for a full row update is to update a range covering the row.
        # We need to determine the number of columns to update based on row_data length.
        # Let's assume the update range starts from column A for that row.
        end_column_letter = chr(ord('A') + len(row_data) - 1)
        update_range = f"A{row_index + 1}:{end_column_letter}{row_index + 1}"

        url = f"{self.base_url}/sheets/v2/spreadsheets/{self.spreadsheet_token}/values"
        payload = {
            "valueRange": {
                "range": self._get_range(update_range),
                "values": [row_data]
            }
        }
        response = requests.put(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def update_changes_from_df(self, dataframe: pd.DataFrame, key_column: str):
        """
        Compares a DataFrame with the sheet data (based on a key column)
        and updates the sheet with changes from the DataFrame.

        Args:
            dataframe: The pandas DataFrame with the potential changes.
            key_column: The name of the column to use as a unique identifier for matching rows.
                         This column must exist in both the DataFrame and the sheet.
        """
        # 1. Read the current sheet data into a DataFrame
        sheet_df = self.read_sheet_to_dataframe()

        if sheet_df.empty and not dataframe.empty:
            print("Sheet is empty. Appending all data from DataFrame.")
            # If the sheet is empty, just append all rows from the DataFrame
            for index, row in dataframe.iterrows():
                self.append_row(row.tolist())
            return
        elif sheet_df.empty and dataframe.empty:
             print("Both sheet and DataFrame are empty. No changes to apply.")
             return
        elif not sheet_df.empty and dataframe.empty:
             print("DataFrame is empty. No changes to apply to the sheet.")
             return


        # Ensure the key column exists in both DataFrames
        if key_column not in dataframe.columns:
            raise ValueError(f"Key column '{key_column}' not found in the provided DataFrame.")
        if key_column not in sheet_df.columns:
            raise ValueError(f"Key column '{key_column}' not found in the Lark sheet.")

        # Set the key column as index for easier comparison
        dataframe_indexed = dataframe.set_index(key_column)
        sheet_df_indexed = sheet_df.set_index(key_column)

        # Identify rows to add (in dataframe_indexed but not in sheet_df_indexed)
        rows_to_add = dataframe_indexed[~dataframe_indexed.index.isin(sheet_df_indexed.index)]
        if not rows_to_add.empty:
            print(f"Appending {len(rows_to_add)} new rows.")
            for index, row in rows_to_add.iterrows():
                self.append_row(row.tolist())

        # Identify rows to update (in both, but values are different)
        common_keys = dataframe_indexed.index.intersection(sheet_df_indexed.index)
        rows_to_update = []

        for key in common_keys:
            df_row = dataframe_indexed.loc[key]
            sheet_row = sheet_df_indexed.loc[key]

            # Compare row by row
            if not df_row.equals(sheet_row):
                # Find the original row index in the sheet_df
                original_sheet_index = sheet_df[sheet_df[key_column] == key].index[0]
                rows_to_update.append((original_sheet_index, df_row.tolist()))

        if rows_to_update:
            print(f"Updating {len(rows_to_update)} rows.")
            for row_index, row_data in rows_to_update:
                self.update_row(row_index, row_data)

        # Identify rows to potentially delete (in sheet_df_indexed but not in dataframe_indexed)
        # Note: Lark Sheets API v2 does not have a direct "delete row by value" or "delete row by index range" API.
        # Deleting rows would require a different approach, possibly reading, modifying the local DataFrame,
        # clearing the sheet, and writing the modified DataFrame back. This can be risky and is not
        # directly supported by a simple "delete_row" API call in v2.
        # For this implementation, we will only handle adding and updating.

        rows_to_consider_deletion = sheet_df_indexed[~sheet_df_indexed.index.isin(dataframe_indexed.index)]
        if not rows_to_consider_deletion.empty:
            print(f"Note: {len(rows_to_consider_deletion)} rows found in the sheet with keys not present in the DataFrame. Manual deletion might be required.")
            # You might want to add logging or a specific handling mechanism here.


# Example Usage:
if __name__ == '__main__':
    # Replace with your actual credentials and sheet details
    YOUR_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
    YOUR_SPREADSHEET_TOKEN = "YOUR_SPREADSHEET_TOKEN"
    YOUR_SHEET_ID = "YOUR_SHEET_ID"

    lark_sheet = LarkSheetAPI(YOUR_ACCESS_TOKEN, YOUR_SPREADSHEET_TOKEN, YOUR_SHEET_ID)

    # 1. Read sheet data
    print("Reading sheet data:")
    df = lark_sheet.read_sheet_to_dataframe()
    print(df)

    # 2. Append a new row
    print("\nAppending a new row:")
    new_row_data = ["New Value 1", "New Value 2", "New Value 3"] # Match your sheet columns
    append_response = lark_sheet.append_row(new_row_data)
    print("Append Response:", append_response)

    # Read again to see the appended row
    print("\nSheet data after appending:")
    df_after_append = lark_sheet.read_sheet_to_dataframe()
    print(df_after_append)

    # 3. Update an existing row (e.g., update the second row, index 1)
    if not df_after_append.empty and len(df_after_append) > 1:
        print("\nUpdating the second row:")
        updated_row_data = ["Updated Value 1", "Updated Value 2", "Updated Value 3"] # Match your sheet columns
        # Ensure the length of updated_row_data matches the number of columns you want to update
        update_response = lark_sheet.update_row(1, updated_row_data) # Update row with index 1
        print("Update Response:", update_response)

        # Read again to see the updated row
        print("\nSheet data after updating:")
        df_after_update = lark_sheet.read_sheet_to_dataframe()
        print(df_after_update)
    else:
        print("\nSkipping row update as there are not enough rows.")


    # 4. Update changes from a DataFrame
    print("\nUpdating changes from a DataFrame:")
    # Create a sample DataFrame with some changes, new rows, and potentially missing rows
    data_for_update_df = {
        'Column1': ['Existing Key 1', 'Existing Key 2', 'New Key 3'], # Assuming 'Column1' is your key column
        'Column2': ['Modified Value 1', 'Existing Value 2', 'New Value A'],
        'Column3': ['Existing Value A', 'Modified Value B', 'New Value B']
    }
    update_df = pd.DataFrame(data_for_update_df)

    print("\nDataFrame to sync:")
    print(update_df)

    # Assuming 'Column1' is the key column for matching
    try:
        lark_sheet.update_changes_from_df(update_df, key_column='Column1')
        print("\nFinished attempting to sync changes from DataFrame.")
        print("\nSheet data after syncing:")
        df_after_sync = lark_sheet.read_sheet_to_dataframe()
        print(df_after_sync)
    except ValueError as e:
        print(f"Error during sync: {e}")