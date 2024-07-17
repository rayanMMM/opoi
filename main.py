import os
import re
import random
import asyncio
import aiohttp

from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telethon import TelegramClient, errors
from telethon.types import ReactionEmoji
from telethon.tl.functions.messages import SendReactionRequest, GetMessagesViewsRequest

from config import ADMIN, BOT_TOKEN
from database import Database
from utils import Utils
from buttons import Buttons

ua = UserAgent()

app = Client("bot", api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627", bot_token=BOT_TOKEN)

database = Database()
utils = Utils()

admin_step = None
tmp_app = {}
force_stop = False

if not os.path.isdir("sessions"):
    os.mkdir("sessions")
    
def random_proxy():
    with open('proxy.txt', 'r') as file:
        proxies = file.read().split("\n")
        
        try:
            rand = random.choice(proxies)
            ip, port, username, password = rand.split(":")
            output = ("socks5", ip, int(port), True, username, password)
        except:
            output = None
    
    return output

@app.on_message(filters.private & filters.text)
async def handle_message(_, message: Message):
    global admin_step, force_stop
    user_id = message.from_user.id
        
    if user_id != ADMIN:
        return
    
    elif not admin_step:
        if message.text.lower() == "/start":
            await message.reply_text("🌗 Please select an option:", reply_markup=Buttons.home)
            
        elif message.text.title() == "🪵 Setting":
            admin_step = "setting"
            await message.reply_text("🌗 Please enter your setting to change:", reply_markup=Buttons.setting)
            
        elif message.text.title() == "🐝 Reaction":
            admin_step = "get_reaction_message_link"
            await message.reply_text("🌗 Please enter your message link:", reply_markup=Buttons.back)
            
        elif message.text.title() == "🕸 Vote":
            admin_step = "get_vote_message_link"
            await message.reply_text("🌗 Please enter your message link:", reply_markup=Buttons.back)
            
        elif message.text.title() == "🪨 View":
            admin_step = "get_view_message_link"
            await message.reply_text("🌗 Please enter your message link:", reply_markup=Buttons.back)
        
        elif message.text.title() == "🕷 Join":
            admin_step = "get_peer"
            await message.reply_text("🌗 Please enter your peer link:", reply_markup=Buttons.back)
        
        elif message.text.title() == "🐙 Auto View":
            admin_step = "enter_channel_id"
            all_auto = database.all_auto()
            
            buttons = []
            
            for auto in all_auto:
                buttons.append(
                    [
                        auto['chat_id']
                    ]
                )
            
            buttons.append(
                ["🔙 Back"]
            )
            
            markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            
            await message.reply_text("🌗 Please enter your channel id or forward a message to add channel else select your channel to remove:", reply_markup=markup)
        
        elif message.text.title() == "🐝 Auto React":
            admin_step = "enter_channel_id_react"
            all_auto = database.all_auto2()
            
            buttons = []
            
            for auto in all_auto:
                buttons.append(
                    [
                        auto['chat_id']
                    ]
                )
            
            buttons.append(
                ["🔙 Back"]
            )
            
            markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            
            await message.reply_text("🌗 Please enter your channel id or forward a message to add channel else select your channel to remove:", reply_markup=markup)
        
        else:
            await message.reply_text("🌗 Command is invalid, Please select an option:", reply_markup=Buttons.home)
    
    else:
        if message.text.title() == "🪫 Cancel" and admin_step in ['reaction', 'vote', 'view']:
            force_stop = True
            await message.reply_text("🌗 Please wait to cancel task ...", reply_markup=ReplyKeyboardRemove())

        elif message.text.title() == "🔙 Back":
            if tmp_app:
                tmp_app.clear()
             
            admin_step = None
            await message.reply_text("🌗 Please select an option:", reply_markup=Buttons.home)
        
        elif admin_step == "setting":
            if message.text == "❕ Turn On/Off Proxy":
                if not database.get_setting('proxy'):
                    proxy_status = 'On'
                    database.set_setting('proxy', 1)
                else:
                    proxy_status = 'Off'
                    database.set_setting('proxy', 0)
                
                await message.reply_text(f"🌗 Proxy system turned {proxy_status.lower()}.\n- Current: {proxy_status}", reply_markup=Buttons.setting)
        
            else:
                await message.reply_text(f"🌗 Setting type is invalid, Please send your setting type:", reply_markup=Buttons.setting)

        elif admin_step == "get_reaction_message_link":
            if not re.match(r"https:\/\/t\.me\/(.+)\/(.+)", message.text):
                return await message.reply_text("🌗 Message link is invalid, Please send your message link:", reply_markup=Buttons.back)
            
            tmp_app["message_link"] = message.text
            admin_step = "get_reaction_emoji"
            await message.reply_text("🌗 Please send your reaction emoji:", reply_markup=Buttons.back)
            
        elif admin_step == "get_reaction_emoji":
            tmp_app["reaction_emoji"] = message.text
            admin_step = "get_reaction_count"
            await message.reply_text("🌗 Please send your reaction count:", reply_markup=Buttons.back)
            
        elif admin_step == "get_reaction_count":
            tmp_app["reaction_count"] = int(message.text)
            admin_step = "get_reaction_sleep"
            await message.reply_text("🌗 Please send your sleep amount between reaction:", reply_markup=Buttons.back)
            
        elif admin_step == "get_reaction_sleep":
            sleep = int(message.text)
            
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👁 Emoji", callback_data="none"),
                        InlineKeyboardButton(f"{tmp_app['reaction_emoji']}", callback_data="none")
                    ],
                    [
                        InlineKeyboardButton("👁 Successfully", callback_data="none"),
                        InlineKeyboardButton("0", callback_data="none")
                    ],
                    [
                        InlineKeyboardButton("👁 Error", callback_data="none"),
                        InlineKeyboardButton("0", callback_data="none")
                    ],
                    [
                        InlineKeyboardButton("👁 Total", callback_data="none"),
                        InlineKeyboardButton(f"{message.text}", callback_data="none")
                    ]
                ]
            )
            
            success = error = 0
            admin_step = "reaction"
            
            await message.reply_text("🌗 Reaction message is starting.", reply_markup=Buttons.cancel)
            sent_message = await message.reply_text("🌗 Reaction message information:", reply_markup=keyboard)
                
            explode_data = re.match(r"https:\/\/t\.me\/(.+)\/(.+)", tmp_app['message_link'])
            peer = explode_data.group(1)
            message_id = int(explode_data.group(2))
            
            get_accounts = os.listdir("sessions")
            random.shuffle(get_accounts)
            
            for account in get_accounts:
                if success >= int(tmp_app["reaction_count"]) or force_stop:
                    break
                
                phone_number = account.split(".")[0]
                
                if database.get_emoji(phone_number, peer, message_id, tmp_app['reaction_emoji']):
                    print("vojod")
                    continue
                
                if database.get_setting('proxy'):
                    proxy = random_proxy()
                else:
                    proxy = None
                    
                with open('hasx.txt', 'r') as file:
                    lines = file.read().split("\n")

                random_api = random.choice(lines)

                API_ID = random_api.split(":")[0]
                API_HASH = random_api.split(":")[1]
      
                client = TelegramClient(
                    session=f"sessions/{phone_number}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    proxy=proxy,
                    connection_retries=1,
                    receive_updates=False
                )
            
                try:
                    await client.connect()
                    
                    await client(SendReactionRequest(
                        peer=peer,
                        msg_id=message_id,
                        reaction=[ReactionEmoji(tmp_app['reaction_emoji'])]
                    ))
                    
                    database.insert_emoji(phone_number, peer, message_id, tmp_app['reaction_emoji'])
                    success += 1
                    
                except (errors.UserDeactivatedError, errors.UserDeactivatedBanError, errors.SessionRevokedError):
                    await utils.stop_client(client)
                    
                    try:
                        os.remove(f'sessions/{account["phone_number"]}.session')
                    except:
                        pass
                    
                except Exception as e:
                    print(e)
                    error += 1
                    
                await utils.stop_client(client)
                await asyncio.sleep(sleep)
        
                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("👁 Emoji", callback_data="none"),
                            InlineKeyboardButton(f"{tmp_app['reaction_emoji']}", callback_data="none")
                        ],
                        [
                            InlineKeyboardButton("👁 Successfully", callback_data="none"),
                            InlineKeyboardButton(f"{success}", callback_data="none")
                        ],
                        [
                            InlineKeyboardButton("👁 Error", callback_data="none"),
                            InlineKeyboardButton(f"{error}", callback_data="none")
                        ],
                        [
                            InlineKeyboardButton("👁 Total", callback_data="none"),
                            InlineKeyboardButton(f"{message.text}", callback_data="none")
                        ]
                    ]
                )
            
                try:
                    await sent_message.edit_reply_markup(keyboard)
                except:
                    pass
                
            if force_stop:
                force_stop = False
                
            tmp_app.clear()
            admin_step = None
            await message.reply_text("🌗 Reaction message was successfully.", reply_markup=Buttons.home)
            
        elif admin_step == "get_view_message_link":
            if not re.match(r"https:\/\/t\.me\/(.+)\/(.+)", message.text):
                return await message.reply_text("🌗 Message link is invalid, Please send your message link:", reply_markup=Buttons.back)
            
            tmp_app["message_link"] = message.text
            admin_step = "get_view_count"
            
            with open('proxy.txt', 'r') as file:
                proxies = file.read().split("\n")
                
            await message.reply_text(f"🌗 Please send your view count:", reply_markup=Buttons.back)
            
        elif admin_step == "get_view_count":
            amount = int(message.text)
            tmp_app["amount"] = amount
            admin_step = "get_view_speed"
            
            await message.reply_text(f"🌗 Please send your time to complete", reply_markup=Buttons.back)
            
        elif admin_step == "get_view_speed":
            amount = tmp_app["amount"]
            time = int(message.text)
        
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👁 Successfully", callback_data="none"),
                        InlineKeyboardButton("0", callback_data="none")
                    ],
                    [
                        InlineKeyboardButton("👁 Error", callback_data="none"),
                        InlineKeyboardButton("0", callback_data="none")
                    ],
                    [
                        InlineKeyboardButton("👁 Total", callback_data="none"),
                        InlineKeyboardButton(amount, callback_data="none")
                    ]
                ]
            )
            
            admin_step = "view"
            
            await message.reply_text("🌗 View is starting.", reply_markup=Buttons.cancel)
            sent_message = await message.reply_text("🌗 View information:", reply_markup=keyboard)
                
            explode_data = re.match(r"https:\/\/t\.me\/(.+)\/(.+)", tmp_app['message_link'])
            channel = explode_data.group(1)
            post = int(explode_data.group(2))
            
            get_accounts = os.listdir("sessions")
            random.shuffle(get_accounts)
            
            success = error = 0
            
            for account in get_accounts:
                if success >= amount or force_stop:
                    break
                
                phone_number = account.split(".")[0]
                
                if database.get_setting('proxy'):
                    proxy = random_proxy()
                else:
                    proxy = None
                    
                with open('hasx.txt', 'r') as file:
                    lines = file.read().split("\n")

                random_api = random.choice(lines)

                API_ID = random_api.split(":")[0]
                API_HASH = random_api.split(":")[1]
      
                client = TelegramClient(
                    session=f"sessions/{phone_number}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    proxy=proxy,
                    connection_retries=1,
                    receive_updates=False
                )
            
                try:
                    await client.connect()
                    
                    await client(GetMessagesViewsRequest(
                        peer=channel,
                        id=[post],
                        increment=True
                    ))
                    
                    success += 1
                    
                except (errors.UserDeactivatedError, errors.UserDeactivatedBanError, errors.SessionRevokedError):
                    await utils.stop_client(client)
                    
                    try:
                        os.remove(f'sessions/{account["phone_number"]}.session')
                    except:
                        pass
                    
                except Exception as e:
                    print(e)
                    error += 1
                    
                await utils.stop_client(client)
                await asyncio.sleep(time / amount)

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("👁 Successfully", callback_data="none"),
                            InlineKeyboardButton(f"{success}", callback_data="none")
                        ],
                        [
                            InlineKeyboardButton("👁 Error", callback_data="none"),
                            InlineKeyboardButton(f"{error}", callback_data="none")
                        ],
                        [
                            InlineKeyboardButton("👁 Total", callback_data="none"),
                            InlineKeyboardButton(amount, callback_data="none")
                        ]
                    ]
                )

                try:    
                    await sent_message.edit_reply_markup(keyboard)
                except:
                    pass
                
            if force_stop:
                force_stop = False
                
            tmp_app.clear()
            admin_step = None
            await message.reply_text("🌗 View was successfully.", reply_markup=Buttons.home)

        elif admin_step == "enter_channel_id":
            if auto := database.get_auto(message.text):
                admin_step = "delete_view"
                tmp_app["chat_id"] = message.text
                await message.reply_text(f"🌗 Info:\n\nChannel ID: {auto['chat_id']}\nAmount: {auto['amount']}\nTime: {auto['seconds']}", reply_markup=Buttons.delete)
            else:
                if message.forward_date and message.forward_from_chat and message.forward_from_chat.username:
                    chat_id = message.forward_from_chat.username
                elif message.text.startswith("@"):
                    chat_id = message.text
                else:
                    return await message.reply_text("🌗 Channel id is invalid.", reply_markup=Buttons.back)
                
                chat_id = chat_id.replace('@', '')
                tmp_app["chat_id"] = chat_id
                    
                admin_step = "view_amount"
                await message.reply_text("🌗 Please send your view amount:", reply_markup=Buttons.back)
            
        elif admin_step == "view_amount":
            if not message.text.isnumeric() or int(message.text) <= 0:
                return await message.reply_text("🌗 View amount is invalid.", reply_markup=Buttons.back)
            
            tmp_app["amount"] = int(message.text)
            
            admin_step = "seconds"
            await message.reply_text("🌗 Please send time to complete view:", reply_markup=Buttons.back)
            
        elif admin_step == "seconds":
            if not message.text.isnumeric() or int(message.text) <= 0:
                return await message.reply_text("🌗 Time is invalid.", reply_markup=Buttons.back)
            
            database.insert_auto(tmp_app["chat_id"], tmp_app["amount"], int(message.text))
            
            tmp_app.clear()
            admin_step = None
            await message.reply_text("🌗 Auto has been added successfully.", reply_markup=Buttons.home)
            
        elif admin_step == "delete_view":
            if message.text == "🦋 Delete":
                chat_id = tmp_app["chat_id"]
                
                if database.get_auto(chat_id):
                    database.delete_auto(chat_id)
                
                tmp_app.clear()
                admin_step = None
                await message.reply_text("🌗 Auto view has been deleted successfully.", reply_markup=Buttons.home)



        elif admin_step == "enter_channel_id_react":
            if auto := database.get_auto(message.text):
                admin_step = "delete_react"
                tmp_app["chat_id"] = message.text
                await message.reply_text(f"🌗 Info:\n\nChannel ID: {auto['chat_id']}\nAmount: {auto['amount']}\nTime: {auto['seconds']}\nEmoji: {auto['emoji']}", reply_markup=Buttons.delete)
            else:
                if message.forward_date and message.forward_from_chat and message.forward_from_chat.username:
                    chat_id = message.forward_from_chat.username
                elif message.text.startswith("@"):
                    chat_id = message.text
                else:
                    return await message.reply_text("🌗 Channel id is invalid.", reply_markup=Buttons.back)
                
                chat_id = chat_id.replace('@', '')
                tmp_app["chat_id"] = chat_id
                    
                admin_step = "reaction_amount"
                await message.reply_text("🌗 Please send your reaction amount:", reply_markup=Buttons.back)
            
        elif admin_step == "reaction_amount":
            if not message.text.isnumeric() or int(message.text) <= 0:
                return await message.reply_text("🌗 Reaction amount is invalid.", reply_markup=Buttons.back)
            
            tmp_app["amount"] = int(message.text)
            
            admin_step = "reaction_seconds"
            await message.reply_text("🌗 Please send time to complete reaction:", reply_markup=Buttons.back)
            
        elif admin_step == "reaction_seconds":
            if not message.text.isnumeric() or int(message.text) <= 0:
                return await message.reply_text("🌗 Time is invalid.", reply_markup=Buttons.back)
            
            tmp_app["seconds"] = int(message.text)
            
            admin_step = "reaction_emoji"
            await message.reply_text("🌗 Please send emoji reaction:", reply_markup=Buttons.back)
            
        elif admin_step == "reaction_emoji":
            database.insert_auto2(tmp_app["chat_id"], tmp_app["amount"], tmp_app["seconds"], message.text)
            
            tmp_app.clear()
            admin_step = None
            await message.reply_text("🌗 Auto react has been added successfully.", reply_markup=Buttons.home)
            
        elif admin_step == "delete_reaction":
            if message.text == "🦋 Delete":
                chat_id = tmp_app["chat_id"]
                
                if database.get_auto2(chat_id):
                    database.delete_auto2(chat_id)
                
                tmp_app.clear()
                admin_step = None
                await message.reply_text("🌗 Auto react has been deleted successfully.", reply_markup=Buttons.home)

@app.on_message(filters.channel | filters.group)
async def handle_channel(_, message: Message):
    asyncio.create_task(complete_task(message))
    
async def complete_task(message: Message):
    chat_id = message.chat.username
    
    if not chat_id:
        return
    
    if auto := database.get_auto(chat_id):
        asyncio.create_task(complete_task1(message, auto))
    
    if auto2 := database.get_auto2(chat_id):
        asyncio.create_task(complete_task2(message, auto2))
    
async def complete_task1(message: Message, auto):
    sleep = auto['seconds'] / auto['amount']
    channel = auto['chat_id']
    post = message.id
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👁 Successfully", callback_data="none"),
                InlineKeyboardButton("0", callback_data="none")
            ],
            [
                InlineKeyboardButton("👁 Error", callback_data="none"),
                InlineKeyboardButton("0", callback_data="none")
            ],
            [
                InlineKeyboardButton("👁 Total", callback_data="none"),
                InlineKeyboardButton(auto['amount'], callback_data="none")
            ]
        ]
    )
            
    sent_message = await app.send_message(
        ADMIN,
        f"🌗 Statistic of https://t.me/{channel}/{post}",
        reply_markup=keyboard
    )
        
    success = error = 0
        
    get_accounts = os.listdir("sessions")
    random.shuffle(get_accounts)
    
    for account in get_accounts:
        if success >= auto['amount']:
            break
        
        phone_number = account.split(".")[0]
        
        if database.get_setting('proxy'):
            proxy = random_proxy()
        else:
            proxy = None
            
        with open('hasx.txt', 'r') as file:
            lines = file.read().split("\n")

        random_api = random.choice(lines)

        API_ID = random_api.split(":")[0]
        API_HASH = random_api.split(":")[1]

        client = TelegramClient(
            session=f"sessions/{phone_number}",
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy,
            connection_retries=1,
            receive_updates=False
        )
    
        try:
            await client.connect()
            
            await client(GetMessagesViewsRequest(
                peer=channel,
                id=[post],
                increment=True
            ))
            
            success += 1
            
        except (errors.UserDeactivatedError, errors.UserDeactivatedBanError, errors.SessionRevokedError):
            await utils.stop_client(client)
            
            try:
                os.remove(f'sessions/{account["phone_number"]}.session')
            except:
                pass
            
        except Exception as e:
            print(e)
            error += 1
            
        await utils.stop_client(client)
        await asyncio.sleep(sleep)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👁 Successfully", callback_data="none"),
                    InlineKeyboardButton(f"{success}", callback_data="none")
                ],
                [
                    InlineKeyboardButton("👁 Error", callback_data="none"),
                    InlineKeyboardButton(f"{error}", callback_data="none")
                ],
                [
                    InlineKeyboardButton("👁 Total", callback_data="none"),
                    InlineKeyboardButton(auto['amount'], callback_data="none")
                ]
            ]
        )

        try:    
            await sent_message.edit_reply_markup(keyboard)
        except:
            pass
        
        
async def complete_task2(message: Message, auto):
    sleep = auto['seconds'] / auto['amount']
    channel = auto['chat_id']
    post = message.id
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👁 Emoji", callback_data="none"),
                InlineKeyboardButton(auto['emoji'], callback_data="none")
            ],
            [
                InlineKeyboardButton("👁 Successfully", callback_data="none"),
                InlineKeyboardButton("0", callback_data="none")
            ],
            [
                InlineKeyboardButton("👁 Error", callback_data="none"),
                InlineKeyboardButton("0", callback_data="none")
            ],
            [
                InlineKeyboardButton("👁 Total", callback_data="none"),
                InlineKeyboardButton(auto['amount'], callback_data="none")
            ]
        ]
    )
            
    sent_message = await app.send_message(
        ADMIN,
        f"🌗 Statistic of https://t.me/{channel}/{post}",
        reply_markup=keyboard
    )
        
    success = error = 0
        
    get_accounts = os.listdir("sessions")
    random.shuffle(get_accounts)
    
    for account in get_accounts:
        if success >= auto['amount']:
            break
        
        phone_number = account.split(".")[0]
        
        if database.get_setting('proxy'):
            proxy = random_proxy()
        else:
            proxy = None
            
        with open('hasx.txt', 'r') as file:
            lines = file.read().split("\n")

        random_api = random.choice(lines)

        API_ID = random_api.split(":")[0]
        API_HASH = random_api.split(":")[1]

        client = TelegramClient(
            session=f"sessions/{phone_number}",
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy,
            connection_retries=1,
            receive_updates=False
        )
    
        try:
            await client.connect()
            
            await client(SendReactionRequest(
                peer=channel,
                msg_id=post,
                reaction=[ReactionEmoji(auto['emoji'])]
            ))
            
            success += 1
            
        except (errors.UserDeactivatedError, errors.UserDeactivatedBanError, errors.SessionRevokedError):
            await utils.stop_client(client)
            
            try:
                os.remove(f'sessions/{account["phone_number"]}.session')
            except:
                pass
            
        except Exception as e:
            print(e)
            error += 1
            
        await utils.stop_client(client)
        await asyncio.sleep(sleep)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👁 Emoji", callback_data="none"),
                    InlineKeyboardButton(auto['emoji'], callback_data="none")
                ],
                [
                    InlineKeyboardButton("👁 Successfully", callback_data="none"),
                    InlineKeyboardButton(f"{success}", callback_data="none")
                ],
                [
                    InlineKeyboardButton("👁 Error", callback_data="none"),
                    InlineKeyboardButton(f"{error}", callback_data="none")
                ],
                [
                    InlineKeyboardButton("👁 Total", callback_data="none"),
                    InlineKeyboardButton(auto['amount'], callback_data="none")
                ]
            ]
        )

        try:    
            await sent_message.edit_reply_markup(keyboard)
        except:
            pass
        
app.run()