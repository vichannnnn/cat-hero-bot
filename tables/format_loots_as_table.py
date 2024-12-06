from loots.models import Loot


def format_loots_as_table(res: list[Loot]):
    if not res:
        return "No loot items to display."

    max_item_length = max((len(loot.item) for loot in res), default=4)
    item_col_width = max(max_item_length, len("Item")) + 4

    table = "```diff\n"
    table += f"  | {'Item':<{item_col_width}} | Quantity |\n"
    table += f"  |{'-' * item_col_width}--|----------|\n"
    for loot in res:
        table += f"~ | {loot.item:<{item_col_width}} | {loot.quantity:<8} |\n"
    table += "```"
    return table
