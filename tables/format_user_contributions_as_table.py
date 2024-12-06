from users.models import User
from database.loot import LootTrackerDB
from loots.models import Loot


def format_users_contribution_as_table(
    loots: list[Loot], participants: list[User]
) -> str:
    if not participants or not loots:
        return "No participants or loot items to display."

    max_user_length = max((len(user.username) for user in participants), default=4)
    max_item_length = max((len(loot.item) for loot in loots), default=4)
    user_col_width = max(max_user_length, len("User")) + 4
    item_col_width = max(max_item_length, len("Item")) + 4

    table = "```diff\n"
    table += (
        f"  | {'User':<{user_col_width}} | {'Item':<{item_col_width}} | Quantity |\n"
    )
    table += f"  |{'-' * user_col_width}--|{'-' * item_col_width}--|----------|\n"

    loot_tracker = LootTrackerDB()
    calculated_loots = loot_tracker.calculate_user_loot(participants, loots)

    for participant in participants:
        participant_data = calculated_loots.get(participant.discord_id)
        if participant_data:
            for loot in participant_data["loots"]:
                table += f"~ | {participant.username:<{user_col_width}} | {loot['item']:<{item_col_width}} | {loot['quantity']:<8.2f} |\n"
        else:
            table += f"- | {participant.username:<{user_col_width}} | {'No Loot':<{item_col_width}} | {'0':<8} |\n"

    table += "```"
    return table
