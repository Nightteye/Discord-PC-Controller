import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import io
import subprocess
import json
import requests
import cv2
import shutil
import pyttsx3
import psutil
import ctypes
import os
import time
import pyautogui
import secrets
from dotenv import load_dotenv
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- CONFIGURATION ---
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
AUTHORIZED_USER_ID = int(os.getenv('OWNER_ID'))
SECRET_PHRASE = os.getenv('SECRET_PHRASE')
SESSION_TIMEOUT = 600  # 10 Minutes
BLACKLIST_FILE = "blacklist.json"

# Global variable to track session expiry
session_expiry_time = 0 

# --- SETUP DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- 🔒 SECURITY & BLACKLIST LOGIC ---

def load_blacklist():
    """Loads banned IDs from file."""
    if not os.path.exists(BLACKLIST_FILE):
        return []
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def ban_intruder(user_id):
    """Permanently adds a user ID to the blacklist file."""
    # 🛡️ LEVEL 1: OWNER IMMUNITY (HARD-CODED)
    # This prevents accidental bans of the owner.
    if user_id == AUTHORIZED_USER_ID:
        print("⚠️ SYSTEM: Attempted to ban Owner. Action blocked.")
        return False
    
    banned_ids = load_blacklist()
    
    if user_id not in banned_ids:
        banned_ids.append(user_id)
        # Write immediately to disk for persistence
        with open(BLACKLIST_FILE, "w") as f:
            json.dump(banned_ids, f)
        print(f"🚨 USER BANNED: {user_id}")
        return True
    return False

async def send_security_alert(interaction: discord.Interaction, context: str):
    """Sends a DM to the owner about a security breach."""
    try:
        owner = await bot.fetch_user(AUTHORIZED_USER_ID)
        if owner:
            await owner.send(
                f"🚨 **INTRUDER CAUGHT & BANNED** 🚨\n"
                f"👤 **User:** {interaction.user.name} (`{interaction.user.id}`)\n"
                f"📝 **Context:** {context}\n"
                f"🛡️ **Status:** ID added to Blacklist permanently."
            )
    except Exception as e:
        print(f"Failed to send alert DM: {e}")

# --- 🛡️ ACCESS GATES ---

def check_session(interaction: discord.Interaction) -> bool:
    """
    The Ultimate Gatekeeper for functional commands.
    Order of checks is critical: Blacklist -> Owner -> Timer.
    """
    user_id = interaction.user.id
    
    # 1. BLACKLIST CHECK (The Wall)
    if user_id in load_blacklist():
        return False # Banned users rejected immediately
        
    # 2. OWNER CHECK
    if user_id != AUTHORIZED_USER_ID:
        return False # Strangers rejected
        
    # 3. SESSION TIMER CHECK
    global session_expiry_time
    if time.time() > session_expiry_time:
        return False # Expired session rejected
        
    return True

# --- SYSTEM FUNCTIONS ---
def lock_windows():
    ctypes.windll.user32.LockWorkStation()

# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot connected as {bot.user}')
    print('🛡️ Security Systems: ACTIVE')
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# --- 🔑 AUTHENTICATION (THE HONEYPOT) ---

@bot.tree.command(name="auth", description="Unlock the bot")
async def auth(interaction: discord.Interaction, password: str):
    user_id = interaction.user.id
    
    # 1. CHECK BLACKLIST FIRST
    if user_id in load_blacklist():
        await interaction.response.send_message("⛔ **ACCESS DENIED.** You are blacklisted.", ephemeral=True)
        return

    global session_expiry_time
    
    # 2. PASSWORD LOGIC
    if secrets.compare_digest(password, SECRET_PHRASE):
        # 3. OWNER CHECK (Even with right password, only YOU can enter)
        if user_id == AUTHORIZED_USER_ID:
            session_expiry_time = time.time() + SESSION_TIMEOUT
            logout_time = int(session_expiry_time)
            await interaction.response.send_message(f"🔓 **Welcome Back.**\nSession expires <t:{logout_time}:R>.", ephemeral=True)
        else:
            # 🛑 CRITICAL FIX APPLIED HERE 🛑
            # Stranger guessed the password! We must BAN them so they don't know they got it right.
            ban_intruder(user_id) 
            await interaction.response.send_message("⛔ **SECURITY VIOLATION.** Unauthorized Device ID. Banned.", ephemeral=True)
            await send_security_alert(interaction, "Guessed CORRECT Password (BANNED)")
    else:
        # 4. WRONG PASSWORD LOGIC
        if user_id == AUTHORIZED_USER_ID:
            # You made a typo
            await interaction.response.send_message(f"⚠️ **Wrong Password.**", ephemeral=True)
        else:
            # STRANGER made a typo -> INSTANT BAN
            ban_intruder(user_id)
            await interaction.response.send_message("⛔ **SECURITY VIOLATION.** Your ID has been Blacklisted.", ephemeral=True)
            await send_security_alert(interaction, "Failed Password Attempt")

@bot.tree.command(name="lockdown", description="Immediately lock the bot")
@app_commands.check(check_session)
async def lockdown(interaction: discord.Interaction):
    global session_expiry_time
    session_expiry_time = 0 
    await interaction.response.send_message("🔒 **System Locked.** Authorization required.", ephemeral=True)

# --- UTILITY COMMANDS (Protected by check_session) ---

@bot.tree.command(name="lock", description="Locks the Windows workstation")
@app_commands.check(check_session)
async def lock(interaction: discord.Interaction):
    await interaction.response.send_message("🔒 Locking workstation...")
    lock_windows()

@bot.tree.command(name="sleep", description="Puts the computer to sleep")
@app_commands.check(check_session)
async def sleep(interaction: discord.Interaction):
    await interaction.response.send_message("💤 Going to sleep...")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

@bot.tree.command(name="screen", description="Takes a screenshot")
@app_commands.check(check_session)
async def screen(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        screenshot = pyautogui.screenshot()
        image_buffer = io.BytesIO()
        screenshot.save(image_buffer, format='PNG')
        image_buffer.seek(0)
        await interaction.followup.send("📷 Here is your screen:", file=discord.File(fp=image_buffer, filename="scr.png"))
    except Exception as e:
        await interaction.followup.send(f"❌ Error taking screenshot: {e}")

@bot.tree.command(name="media", description="Control media")
@app_commands.describe(action="choose: play, pause, next, prev, mute")
@app_commands.choices(action=[
    app_commands.Choice(name="Play/Pause", value="playpause"),
    app_commands.Choice(name="Next Track", value="nexttrack"),
    app_commands.Choice(name="Previous Track", value="prevtrack"),
    app_commands.Choice(name="Mute Audio", value="volumemute")
])
@app_commands.check(check_session)
async def media(interaction: discord.Interaction, action: app_commands.Choice[str]):
    pyautogui.press(action.value)
    await interaction.response.send_message(f"⏯️ Media command sent: {action.name}")

@bot.tree.command(name="cam", description="Takes a photo using the webcam")
@app_commands.check(check_session)
async def cam(interaction: discord.Interaction):
    await interaction.response.defer() 
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await interaction.followup.send("❌ Could not open webcam.")
        return
    ret, frame = cap.read()
    cap.release()
    if ret:
        success, buffer = cv2.imencode('.jpg', frame)
        io_buf = io.BytesIO(buffer)
        await interaction.followup.send("📸 Say cheese!", file=discord.File(io_buf, "webcam.jpg"))
    else:
        await interaction.followup.send("❌ Failed to capture image.")

@bot.tree.command(name="say", description="Makes the laptop speak text out loud")
@app_commands.check(check_session)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"🗣️ Speaking: {message}")
    def speak():
        try:
            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()
            engine.stop()
            del engine 
        except Exception as e:
            print(f"TTS Error: {e}")
    await bot.loop.run_in_executor(None, speak)

@bot.tree.command(name="status", description="Shows Battery, CPU, and RAM status")
@app_commands.check(check_session)
async def status(interaction: discord.Interaction):
    battery = psutil.sensors_battery()
    plugged = "🔌 Plugged In" if battery.power_plugged else "🔋 On Battery"
    percent = battery.percent
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    msg = f"**🖥️ System Status:**\n{plugged}: {percent}%\n🧠 CPU Usage: {cpu}%\n💾 RAM Usage: {ram}%"
    await interaction.response.send_message(msg)

@bot.tree.command(name="locate", description="Finds approximate location")
@app_commands.check(check_session)
async def locate(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        response = requests.get("http://ip-api.com/json/").json()
        if response['status'] == 'fail':
            await interaction.followup.send("❌ Could not determine location.")
            return
        lat = response.get('lat', 0)
        lon = response.get('lon', 0)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        message = f"📍 **Location:** {response.get('city')}, {response.get('country')}\n🔗 **Map:** [Open Google Maps]({maps_link})"
        await interaction.followup.send(message)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="gps", description="Get precise location")
@app_commands.check(check_session)
async def gps(interaction: discord.Interaction):
    await interaction.response.defer()
    ps_script = """
    Add-Type -AssemblyName System.Device
    $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
    $GeoWatcher.Start()
    $start = Get-Date
    while (($GeoWatcher.Status -ne 'Ready') -and ((Get-Date) - $start).TotalSeconds -lt 5) { Start-Sleep -Milliseconds 100 }
    $Loc = $GeoWatcher.Position.Location
    if ($Loc.IsUnknown) { Write-Output "Unknown" } else {
        $result = @{ lat = $Loc.Latitude; lon = $Loc.Longitude; acc = $Loc.HorizontalAccuracy }
        $result | ConvertTo-Json
    }
    """
    try:
        process = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        output = process.stdout.strip()
        if "Unknown" in output or not output:
            await interaction.followup.send("❌ Could not get GPS data.")
            return
        data = json.loads(output)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={data['lat']},{data['lon']}"
        await interaction.followup.send(f"🎯 **GPS:** Within {int(data['acc'])}m\n🔗 [Open Google Maps]({maps_link})")
    except Exception as e:
        await interaction.followup.send(f"❌ GPS Error: {e}")

@bot.tree.command(name="message", description="Pops up a Windows Dialog Box")
@app_commands.check(check_session)
async def message(interaction: discord.Interaction, title: str, text: str):
    await interaction.response.send_message(f"💬 Sent popup: **{title}**")
    def show_popup():
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x40 | 0x1)
    await bot.loop.run_in_executor(None, show_popup)

@bot.tree.command(name="wallpaper", description="Change desktop wallpaper")
@app_commands.check(check_session)
async def wallpaper(interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer()
    try:
        file_path = os.path.join(os.getcwd(), "wallpaper_temp.jpg")
        await image.save(file_path)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, file_path, 0)
        await interaction.followup.send("🖼️ Wallpaper changed!")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed: {e}")

@bot.tree.command(name="blackout", description="Turns the monitor OFF")
@app_commands.check(check_session)
async def blackout(interaction: discord.Interaction):
    await interaction.response.send_message("🌑 Monitor going dark...")
    def turn_off():
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
    await bot.loop.run_in_executor(None, turn_off)

@bot.tree.command(name="cmd", description="Execute a Windows CMD command")
@app_commands.check(check_session)
async def cmd(interaction: discord.Interaction, command: str):
    await interaction.response.defer()
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        decoded_output = output.decode('utf-8', errors='ignore')
        if len(decoded_output) > 1900: decoded_output = decoded_output[:1900] + "\n... (Output Truncated)"
        await interaction.followup.send(f"💻 **Command:** `{command}`\n```bat\n{decoded_output}\n```")
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(f"❌ Command failed:\n```\n{e.output.decode('utf-8')}\n```")

@bot.tree.command(name="launch", description="Launch an application")
@app_commands.choices(app=[
    app_commands.Choice(name="Spotify", value="spotify"),
    app_commands.Choice(name="Google Chrome", value="chrome"),
    app_commands.Choice(name="Notepad", value="notepad"),
    app_commands.Choice(name="Calculator", value="calc"),
    app_commands.Choice(name="Task Manager", value="taskmgr")
])
@app_commands.check(check_session)
async def launch(interaction: discord.Interaction, app: app_commands.Choice[str]):
    await interaction.response.send_message(f"🚀 Launching **{app.name}**...")
    if app.value == "chrome": os.system("start chrome")
    elif app.value == "spotify": os.system("start spotify") 
    else: os.system(f"start {app.value}")

# --- GLOBAL ERROR HANDLER ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        user_id = interaction.user.id
        
        # 1. Is it a Banned User? (The Loophole Closer)
        if user_id in load_blacklist():
            await interaction.response.send_message("⛔ **Access Denied.** (Blacklisted)", ephemeral=True)
            return

        # 2. Is it the Owner?
        if user_id == AUTHORIZED_USER_ID:
            global session_expiry_time
            if time.time() > session_expiry_time:
                 await interaction.response.send_message("🔒 **Session Expired.**\nPlease run `/auth [password]` to unlock.", ephemeral=True)
            else:
                 await interaction.response.send_message("❌ **Auth Error.**", ephemeral=True)
        else:
             # 3. Unauthorized Stranger
             await interaction.response.send_message("⛔ **Unauthorized.** Logged.", ephemeral=True)
    else:
        print(f"Bot Error: {error}")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
    else:
        bot.run(TOKEN)