from pyrogram.types import ReplyKeyboardMarkup

class Buttons:
    home = ReplyKeyboardMarkup(
        [
            ["🪵 Setting"],
            ["🐝 Reaction", "🪨 View"],
            ["🐙 Auto View", "🐝 Auto React"]
        ],
        resize_keyboard=True
    )
    
    setting = ReplyKeyboardMarkup(
        [
            ["❕ Turn On/Off Proxy"],
            ["🔙 Back"]
        ],
        resize_keyboard=True
    )
    
    back = ReplyKeyboardMarkup(
        [
            ["🔙 Back"]
        ],
        resize_keyboard=True
    )
    
    delete = ReplyKeyboardMarkup(
        [
            ["🦋 Delete"],
            ["🔙 Back"]
        ],
        resize_keyboard=True
    )
        
    cancel = ReplyKeyboardMarkup(
        [
            ["🪫 Cancel"]
        ],
        resize_keyboard=True
    )