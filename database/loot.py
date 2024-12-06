import sqlite3
from typing import List
from loots.models import Loot
from users.models import User


class LootTrackerDB:
    def __init__(self, db_path="loot_tracker.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                discord_id INTEGER UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loot_with_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loot_id INTEGER NOT NULL,
                cycle_id INTEGER NOT NULL,
                FOREIGN KEY(loot_id) REFERENCES loot(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loot_with_participant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(loot_with_participant_id) REFERENCES loot_with_participants(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        self.conn.commit()

    def start_new_cycle(self) -> int:
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE cycles
            SET cycle_id = cycle_id + 1
            WHERE id = 1
        """)

        cursor.execute("""
            SELECT cycle_id FROM cycles WHERE id = 1
        """)
        new_cycle_id = cursor.fetchone()[0]
        self.conn.commit()
        return new_cycle_id

    def get_current_cycle(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cycle_id FROM cycles WHERE id = 1
        """)
        current_cycle_id = cursor.fetchone()[0]
        return current_cycle_id

    def add_user(self, user: User):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, discord_id)
            VALUES (?, ?)
        """,
            (user.username, user.discord_id),
        )
        self.conn.commit()

    def add_loot(self, loot: Loot) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO loot (item, quantity)
            VALUES (?, ?)
        """,
            (loot.item, loot.quantity),
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_loot_with_participants(
        self, loot: Loot, participants: List[User], cycle_id: int
    ):
        loot_id = self.add_loot(loot)
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO loot_with_participants (loot_id, cycle_id)
            VALUES (?, ?)
        """,
            (loot_id, cycle_id),
        )
        loot_with_participant_id = cursor.lastrowid

        for user in participants:
            self.add_user(user)
            cursor.execute(
                """
                INSERT INTO participants (loot_with_participant_id, user_id)
                VALUES (
                    ?, 
                    (SELECT id FROM users WHERE discord_id = ?)
                )
            """,
                (loot_with_participant_id, user.discord_id),
            )

        self.conn.commit()

    def get_user_loot(self, user: User, cycle_id: int = None) -> List[Loot]:
        cursor = self.conn.cursor()

        query = """
            SELECT l.item, l.quantity / (
                SELECT COUNT(*) 
                FROM participants p 
                WHERE p.loot_with_participant_id = lw.id
            ) as split_quantity
            FROM loot l
            JOIN loot_with_participants lw ON l.id = lw.loot_id
            JOIN participants p ON lw.id = p.loot_with_participant_id
            WHERE p.user_id = (SELECT id FROM users WHERE discord_id = ?)
        """
        params = [user.discord_id]
        if cycle_id:
            query += " AND lw.cycle_id = ?"
            params.append(cycle_id)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [Loot(item=row[0], quantity=row[1]) for row in rows]

    def calculate_user_loot(self, participants: List[User], loots: List[Loot]) -> dict:
        if not participants or not loots:
            return {}

        results = {}
        for participant in participants:
            results[participant.discord_id] = {
                "username": participant.username,
                "cycle_id": self.get_current_cycle(),
                "loots": [],
            }

        for loot in loots:
            split_quantity = loot.quantity / len(participants)
            for participant in participants:
                results[participant.discord_id]["loots"].append(
                    {"item": loot.item, "quantity": split_quantity}
                )

        return results
