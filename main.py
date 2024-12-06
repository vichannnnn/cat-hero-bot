import asyncio.exceptions
from typing import Optional

import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
from database.loot import LootTrackerDB
from database.sheet import GoogleSheetsHelper
from loots.models import Loot
from loots.main import parse_cv_result_into_loots, upload_image_and_get_cv
from tables.format_loots_as_table import format_loots_as_table
from tables.format_user_contributions_as_table import format_users_contribution_as_table
from tables.format_loot_table_for_user import format_loot_table_for_user
from users.models import User
import os

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

TESTING_GUILD_ID = 1139405183810551948

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, default_guild_ids=[TESTING_GUILD_ID])

loot_tracker = LootTrackerDB()


async def process_loot_message(
    message: nextcord.Message, res: list[Loot], sheets_helper: GoogleSheetsHelper
):
    formatted_table = format_loots_as_table(res)
    loot_message = await message.channel.send(
        f"This are the loots detected. Please mention all the participants involved by @ing them:\n\n{formatted_table}",
        delete_after=60,
    )

    def check(msg):
        return msg.author == message.author and msg.channel == message.channel

    participants = None
    while not participants:
        try:
            participants_msg = await bot.wait_for("message", timeout=60, check=check)
            participants = participants_msg.mentions
            if not participants:
                await message.channel.send(
                    "No participants mentioned. Please mention the participants correctly.",
                    delete_after=10,
                )
        except asyncio.exceptions.TimeoutError:
            await message.channel.send(
                "No response received. Operation timed out.", delete_after=10
            )
            return

    await loot_message.delete()

    user_participants = [
        User(username=member.name, discord_id=member.id) for member in participants
    ]

    participants_table = format_users_contribution_as_table(
        loots=res, participants=user_participants
    )

    await message.channel.send(
        f"Participants involved: "
        f"{''.join(['<@' + str(participant.discord_id) + '>' for participant in user_participants])}\n\n"
        f"{participants_table}\n\n"
    )
    confirmation_message = await message.channel.send(
        "Is this correct? Please react to confirm (✅) or decline (❌)."
    )
    await confirmation_message.add_reaction("✅")
    await confirmation_message.add_reaction("❌")

    def reaction_check(reaction, user):
        return (
            user == message.author
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == confirmation_message.id
        )

    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=60, check=reaction_check
        )
        await confirmation_message.delete()
        if str(reaction.emoji) == "✅":
            for loot in res:
                loot_tracker.add_loot_with_participants(
                    loot, user_participants, loot_tracker.get_current_cycle()
                )
            sheets_helper.add_loot_to_sheet(
                loot_tracker.get_current_cycle(), user_participants, res
            )
            await message.channel.send(
                "Great! The data has been saved.", delete_after=10
            )
        else:
            await message.channel.send("Operation cancelled.", delete_after=10)
    except asyncio.exceptions.TimeoutError:
        await message.channel.send(
            "No confirmation received. Operation timed out.", delete_after=10
        )


@bot.event
async def on_ready():
    guild = bot.get_guild(TESTING_GUILD_ID)
    if guild:
        await guild.delete_application_commands()
        print("Deleted old commands.")
        await bot.sync_all_application_commands()
        print("Commands synced successfully!")


@bot.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and "image" in attachment.content_type:
                loading = await message.channel.send(
                    "<a:1792loading:1314611528795684874>  Processing request. Please wait for a moment!  "
                    "<a:1792loading:1314611528795684874>"
                )

                cv = upload_image_and_get_cv(attachment.url)
                res = parse_cv_result_into_loots(cv)

                await loading.delete()

                sheets_helper = GoogleSheetsHelper(
                    credentials_path="cat-heroes-443916-c29b27de5dae.json",
                    spreadsheet_name="Loot Tracker",
                )
                await process_loot_message(message, res, sheets_helper)


@bot.slash_command(description="Start a new loot cycle", guild_ids=[TESTING_GUILD_ID])
async def start_cycle(interaction: nextcord.Interaction):
    new_cycle_id = loot_tracker.start_new_cycle()
    await interaction.response.send_message(f"New cycle started: Cycle {new_cycle_id}")


@bot.slash_command(description="Get a user's loot", guild_ids=[TESTING_GUILD_ID])
async def user_loot(
    interaction: nextcord.Interaction,
    member: nextcord.Member,
    cycle_id: Optional[int] = None,
):
    user = User(username=member.name, discord_id=member.id)
    try:
        loots = loot_tracker.get_user_loot(user, cycle_id=cycle_id)
        if not loots:
            await interaction.response.send_message(
                f"No loot found for user {member.mention}."
            )
            return

        combined_loots = {}
        for loot in loots:
            if loot.item in combined_loots:
                combined_loots[loot.item] += loot.quantity
            else:
                combined_loots[loot.item] = loot.quantity

        combined_loot_list = [
            Loot(item=item, quantity=quantity)
            for item, quantity in combined_loots.items()
        ]

        week_statement = f"on week **{cycle_id}**"
        table = format_loot_table_for_user(member.name, combined_loot_list)
        await interaction.response.send_message(
            f"Loot for {member.mention} {week_statement if cycle_id else ""}:\n\n{table}"
        )
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


bot.run(token=BOT_TOKEN)
