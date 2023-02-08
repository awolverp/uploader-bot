import sqlite3
import os # for os.environ
import time # to generate token
from pyrogram import Client, types, filters

# database connection
db_connection = sqlite3.connect("db.sqlite3")
db_cursor = db_connection.cursor()

db_cursor.execute("CREATE TABLE IF NOT EXISTS files(file_id TEXT PRIMARY KEY, token BIGINT, caption TEXT);")
db_connection.commit()

# client
API_ID = os.environ.get("API_ID", 000000)
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

bot = Client("bot", API_ID, API_HASH, bot_token=BOT_TOKEN)

def generate_token() -> int:
    """
    Generates token for saved files

    - Uses time to avoid generating exist tokens
    """
    return int(time.time())

def save_file(file_id: str, token: int, caption: str) -> bool:
    try:
        db_cursor.execute("INSERT INTO files(file_id,token,caption) VALUES(?,?,?);", (file_id, token, caption))
    except sqlite3.IntegrityError:
        db_connection.rollback()
        return False
    
    db_connection.commit()
    return True

async def share_saved_file(msg: types.Message, token: int):
    """
    Share saved files to telegram.
    """
    # select file_id and caption
    file_info = db_cursor.execute("SELECT file_id,caption FROM files WHERE token=?", (token,)).fetchone()

    if not file_info: # if not found
        return await bot.send_message("File not found!")
    
    # send that
    await bot.send_cached_media(msg.chat.id, file_info[0], caption=file_info[1])

@bot.on_message(filters.media)
async def on_media(_, msg: types.Message) -> None:
    # get file_id & token
    file_id = getattr(msg, str(msg.media.value).lower()).file_id # type: str
    token = generate_token()

    ok = save_file(file_id, token, msg.caption)
    
    if not ok:
        await bot.send_message(msg.chat.id, "File already exists, LINK: https://t.me/%s?start=%s" % (bot.me.username, token))
    
    else:
        await bot.send_message(msg.chat.id, "File saved ...\nFILE ID: `%s`\n\nLINK: https://t.me/%s?start=%s" % (file_id, bot.me.username, token))

@bot.on_message()
async def on_message(_, msg: types.Message) -> None:
    command = msg.text.split(" ", 2)
    if command[0] == "/start" and len(command) == 2:
        try:
            await share_saved_file(msg, int(command[1]))
        except ValueError:
            # invalid token
            pass

        return

    await bot.send_message(msg.chat.id, "Hi, You can share your files with me.\n\n+ send a media (any type):")

bot.run()
