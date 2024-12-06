from loots.models import Loot


def format_loot_table_for_user(username: str, loots: list[Loot]) -> str:
    if not loots:
        return "No loot items to display."

    max_item_length = max((len(loot.item) for loot in loots), default=4)
    item_col_width = max(max_item_length, len("Item")) + 4

    table = "```diff\n"
    table += f"  | {'User':<20} | {'Item':<{item_col_width}} | Quantity |\n"
    table += f"  |{'-' * 20}--|{'-' * item_col_width}--|----------|\n"

    for loot in loots:
        table += f"~ | {username:<20} | {loot.item:<{item_col_width}} | {loot.quantity:<8.2f} |\n"

    table += "```"
    return table
