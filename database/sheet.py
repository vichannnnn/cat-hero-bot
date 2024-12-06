import gspread
from loots.models import Loot
from users.models import User


class GoogleSheetsHelper:
    def __init__(self, credentials_path: str, spreadsheet_name: str):
        self.gc = gspread.service_account(filename=credentials_path)
        self.spreadsheet = self.gc.open(spreadsheet_name)

    def add_cycle_subsheet(self, cycle_id: int):
        sheet_name = f"Week {cycle_id}"
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name, rows=100, cols=20
            )
            worksheet.append_row(["User", "Item", "Quantity"])
        return worksheet

    def add_loot_to_sheet(
        self, cycle_id: int, user_participants: list[User], loots: list[Loot]
    ):
        worksheet = self.add_cycle_subsheet(cycle_id)
        for participant in user_participants:
            for loot in loots:
                worksheet.append_row([participant.username, loot.item, loot.quantity])
