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

        if not user_participants or not loots:
            return

        split_loots = {}
        for loot in loots:
            split_quantity = loot.quantity / len(user_participants)
            for participant in user_participants:
                if participant.discord_id not in split_loots:
                    split_loots[participant.discord_id] = {
                        "username": participant.username,
                        "loots": [],
                    }
                split_loots[participant.discord_id]["loots"].append(
                    {"item": loot.item, "quantity": split_quantity}
                )

        for participant_data in split_loots.values():
            username = participant_data["username"]
            for loot in participant_data["loots"]:
                worksheet.append_row([username, loot["item"], loot["quantity"]])
