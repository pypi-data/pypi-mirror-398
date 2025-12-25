from telethon import TelegramClient, events
import asyncio
import re
import json
import os
from datetime import datetime, timedelta

base_dir = os.path.dirname(__file__)
values_path = os.path.join(base_dir, "values.json")
verifieds_path = os.path.join(base_dir, "verifieds.json")
saved_posts_path = os.path.join(base_dir, "saved_posts.json")

with open(values_path, "r") as f:
    config = json.load(f)

api_id = config["api_id"]
api_hash = config["api_hash"]
bot_token = "8356485293:AAGFkQSSZ0xgNSFAxzoMx1_IiyVDcpoRJWw"

if os.path.exists(verifieds_path):
    with open(verifieds_path, "r") as f:
        verified_users = json.load(f)
else:
    verified_users = []

if os.path.exists(saved_posts_path):
    with open(saved_posts_path, "r") as f:
        saved_posts = json.load(f)
else:
    saved_posts = {}

broadcast_waiting_link = {}
broadcast_intervals = {}
broadcast_tasks = {}
userbot = None
bot = None

def save_posts():
    with open(saved_posts_path, "w") as f:
        json.dump(saved_posts, f, indent=4)

async def forward_post_to_all_groups(message_obj, sender_id):
    success, failed = 0, 0
    success_groups, failed_groups = [], []

    async for dialog in userbot.iter_dialogs():  
        if dialog.is_group:  
            try:  
                await userbot.forward_messages(dialog.id, message_obj)  
                success += 1  
                success_groups.append(dialog.name)  
            except:  
                failed += 1  
                failed_groups.append(dialog.name)  

    reply_text = (  
        f"🟢 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗥𝗲𝘀𝘂𝗹𝘁\n\n"  
        f"✅ Success: {success}\n❌ Failed: {failed}"  
    )  
    if success_groups:  
        reply_text += "\n\n✅ Groups:\n" + "\n".join(success_groups)  
    if failed_groups:  
        reply_text += "\n\n❌ Failed:\n" + "\n".join(failed_groups)  

    await bot.send_message(sender_id, reply_text)

async def start_broadcast(event, is_bot=False):
    if event.sender_id not in verified_users:
        return

    match = re.match(r"^/broadcast(?: (\d+)m)?$", event.raw_text)  
    interval = match.group(1) if match else None  

    if interval:  
        minutes = int(interval)  
        if minutes < 5 or minutes > 1000:  
            await event.reply("⚠️ Minimum 5 Minutes Required (e.g., /broadcast 10m)")  
            return  
        broadcast_intervals[event.sender_id] = minutes  
        await event.reply(f"🟢 Schedule Broadcast Every {minutes} Minutes.\n\nPlease Send Your Message Post Link (Public Group Required)")  
    else:  
        broadcast_intervals[event.sender_id] = None  
        await event.reply("🟢 One-Time Broadcast.\n\nPlease Send Your Message Post Link (Public Group Required)")  

    broadcast_waiting_link[event.sender_id] = True  
    raise events.StopPropagation

async def stop_broadcast(event, is_bot=False):
    if event.sender_id not in verified_users:
        return

    if event.sender_id in broadcast_tasks and not broadcast_tasks[event.sender_id].done():  
        broadcast_tasks[event.sender_id].cancel()  
        del broadcast_tasks[event.sender_id]  
        saved_posts.pop(str(event.sender_id), None)  
        save_posts()  
        await event.reply("🛑 Broadcast Stopped and Removed from Schedule.")  
    else:  
        await event.reply("⚠️ No Active Broadcast Found.")

async def link_handler(event, is_bot=False):
    if event.sender_id in broadcast_waiting_link and broadcast_waiting_link[event.sender_id]:
        broadcast_waiting_link[event.sender_id] = False
        interval = broadcast_intervals.get(event.sender_id)
        message_link = event.raw_text.strip()
 
        match = re.match(r"^https://t\.me/([\w\d_]+)/(\d+)$", message_link)  
        if not match:  
            await event.reply("⚠️ Invalid Link! Please Send a Valid Public Group Post Link.")  
            return  

        chat_username = match.group(1)  
        msg_id = int(match.group(2))  

        try:  
            target_chat = await userbot.get_entity(chat_username)  
            target_message = await userbot.get_messages(target_chat, ids=msg_id)  
        except Exception as e:  
            await event.reply(f"⚠️ Unable to Fetch Message: {e}")  
            return  

        await event.reply("✅ Post Fetched Successfully. Starting Broadcast...")  

        async def run_interval_broadcast(message_obj, minutes, sender_id):  
            while True:  
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                saved_posts[str(sender_id)] = {  
                    "message_link": message_link,  
                    "interval_minutes": minutes,  
                    "last_interval": now,  
                    "next_interval": (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")  
                }  
                save_posts()  
                await forward_post_to_all_groups(message_obj, sender_id)  
                await asyncio.sleep(minutes * 60)  

        if interval:  
            if event.sender_id in broadcast_tasks and not broadcast_tasks[event.sender_id].done():  
                broadcast_tasks[event.sender_id].cancel()  

            task = asyncio.create_task(run_interval_broadcast(target_message, interval, event.sender_id))  
            broadcast_tasks[event.sender_id] = task  

            saved_posts[str(event.sender_id)] = {  
                "message_link": message_link,  
                "interval_minutes": interval,  
                "last_interval": None,  
                "next_interval": (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")  
            }  
            save_posts()  
            await event.reply(f"🟢 Interval Broadcast Started ({interval}m)")  
        else:  
            await forward_post_to_all_groups(target_message, event.sender_id)  
            await event.reply("✅ One-Time Broadcast Completed")

async def restore_saved_broadcasts():
    for sender_id, data in saved_posts.items():
        try:
            sender_id = int(sender_id)
            link = data.get("message_link")
            minutes = data.get("interval_minutes")
            match = re.match(r"^https://t\.me/([\w\d_]+)/(\d+)$", link)
            if not match:
                continue
            chat_username = match.group(1)
            msg_id = int(match.group(2))
            chat = await userbot.get_entity(chat_username)
            msg = await userbot.get_messages(chat, ids=msg_id)

            async def loop_restore(m_obj, mins, s_id):  
                while True:  
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                    saved_posts[str(s_id)]["last_interval"] = now  
                    saved_posts[str(s_id)]["next_interval"] = (datetime.now() + timedelta(minutes=mins)).strftime("%Y-%m-%d %H:%M:%S")  
                    save_posts()  
                    await forward_post_to_all_groups(m_obj, s_id)  
                    await asyncio.sleep(mins * 60)  

            if msg and minutes:  
                task = asyncio.create_task(loop_restore(msg, minutes, sender_id))  
                broadcast_tasks[sender_id] = task  
        except Exception as e:  
            print("Error restoring broadcast:", e)

async def setup_clients():
    global userbot, bot

    userbot = TelegramClient("userbot_session", api_id, api_hash)
    bot = TelegramClient("bot_session", api_id, api_hash)

    await userbot.connect()
    await bot.connect()

    await userbot.start()
    await bot.start(bot_token=bot_token)

    userbot.add_event_handler(start_broadcast, events.NewMessage(pattern=r"^/broadcast(?: (\d+)m)?$"))
    userbot.add_event_handler(stop_broadcast, events.NewMessage(pattern=r"^/stopbroadcast$"))
    userbot.add_event_handler(link_handler, events.NewMessage)

    bot.add_event_handler(lambda e: start_broadcast(e, is_bot=True), events.NewMessage(pattern=r"^/broadcast(?: (\d+)m)?$"))
    bot.add_event_handler(lambda e: stop_broadcast(e, is_bot=True), events.NewMessage(pattern=r"^/stopbroadcast$"))
    bot.add_event_handler(lambda e: link_handler(e, is_bot=True), events.NewMessage)

    await restore_saved_broadcasts()
    
    print("Userbot and Bot are running...")

    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

async def main():
    await setup_clients()

if __name__ == "__main__":
    asyncio.run(main())