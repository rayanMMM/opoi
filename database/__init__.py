import sqlite3
from utils import Utils

utils = Utils()

class Database:
    def __init__(self) -> None:
        self.connection = sqlite3.connect("database/db.db", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS `reactions` (`phone_number` TEXT, `chat_id` TEXT, `message_id` INT, `emoji` TEXT);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS `auto` (`chat_id` TEXT, `amount` INT, `seconds` INT);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS `auto2` (`chat_id` TEXT, `amount` INT, `seconds` INT, `emoji` TEXT);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS `setting` (`proxy` INT);")
        
        self.connection.commit()

        self.cursor.execute("SELECT * FROM `setting`;")
        result = self.cursor.fetchone()
        
        if result is None:
            self.cursor.execute("INSERT INTO `setting` VALUES (?);", (0,))
            self.connection.commit()
           
    def all_auto(self):
        self.cursor.execute("SELECT * FROM `auto`;")
        return self.cursor.fetchall()
     
    def get_auto(self, chat_id):
        self.cursor.execute("SELECT * FROM `auto` WHERE `chat_id` = ?;", (chat_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result
        return False
        
    def insert_auto(self, chat_id, amount, seconds):
        self.cursor.execute("INSERT INTO `auto` (chat_id, amount, seconds) VALUES (?, ?, ?);", (chat_id, amount, seconds,))
        self.connection.commit()
        
    def delete_auto(self, chat_id,):
        self.cursor.execute("DELETE FROM `auto` WHERE `chat_id` = ?;", (chat_id,))
        self.connection.commit()
        
    def all_auto2(self):
        self.cursor.execute("SELECT * FROM `auto2`;")
        return self.cursor.fetchall()
     
    def get_auto2(self, chat_id):
        self.cursor.execute("SELECT * FROM `auto2` WHERE `chat_id` = ?;", (chat_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result
        return False
        
    def insert_auto2(self, chat_id, amount, seconds, emoji):
        self.cursor.execute("INSERT INTO `auto2` (chat_id, amount, seconds, emoji) VALUES (?, ?, ?, ?);", (chat_id, amount, seconds, emoji,))
        self.connection.commit()
        
    def delete_auto2(self, chat_id,):
        self.cursor.execute("DELETE FROM `auto2` WHERE `chat_id` = ?;", (chat_id,))
        self.connection.commit()
        
    def get_emoji(self, phone_number, chat_id, message_id, emoji):
        self.cursor.execute("SELECT * FROM `reactions` WHERE `phone_number` = ? AND `chat_id` = ? AND `message_id` = ? AND `emoji` = ?;", (phone_number, chat_id, message_id, emoji,))
        result = self.cursor.fetchone()
        if result is not None:
            return result
        return False
        
    def insert_emoji(self, phone_number, chat_id, message_id, emoji):
        self.cursor.execute("INSERT INTO `reactions` (phone_number, chat_id, message_id, emoji) VALUES (?, ?, ?, ?);", (phone_number, chat_id, message_id, emoji,))
        self.connection.commit()
    
    def get_setting(self, column):
        self.cursor.execute("SELECT * FROM `setting`;")
        result = self.cursor.fetchone()
        if result is not None:
            return result[column]
        return False
    
    def set_setting(self, column, value):
        self.cursor.execute(f"UPDATE `setting` SET {column} = ?;", (value,))
        self.connection.commit()