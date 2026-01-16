# 🎮 Discord PC Remote Controller

A powerful, secure, and feature-rich Discord bot that allows you to remotely control and monitor your Windows PC from anywhere using Discord slash commands.

## ✨ Features

* **🛡️ Secure Authentication:** Session-based access with a secret passphrase and auto-lockout timer.
* **📸 Visuals:** Take screenshots (`/screen`) and webcam photos (`/cam`) instantly.
* **🔊 Audio Control:** Adjust volume, play/pause media, and make the PC speak (`/say`).
* **💻 System Control:** Remote locking (`/lock`), sleep (`/sleep`), and monitor blackout (`/blackout`).
* **📍 Anti-Theft:** Get approximate (IP) or precise (GPS/Wi-Fi) location (`/locate`, `/gps`).
* **🛠️ Power User Tools:** Execute shell commands (`/cmd`), launch apps (`/launch`), and view system health (`/status`).
* **🚫 Intruder Trap:** Automatically blacklists and alerts the owner if someone guesses the password.

## ⚠️ Requirements

* **OS:** Windows 10/11 (Required for audio/shell commands)
* **Python:** 3.8 or higher
* **Discord Account:** with Developer Mode enabled

## 🚀 Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/[REPO_NAME].git
    cd [REPO_NAME]
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**
    Create a file named `.env` in the main folder and add your credentials:
    ```ini
    DISCORD_TOKEN=your_bot_token_here
    OWNER_ID=your_discord_user_id_here
    SECRET_PHRASE=your_secret_password_here
    ```

4.  **Run the Bot**
    ```bash
    python bot.py
    ```

## 📖 Usage Guide

1.  **Start the Bot:** Run the script on your PC.
2.  **Authenticate:** In Discord, type `/auth password:[your_secret_phrase]`.
    * *Note: You have 10 minutes (default) before the session expires.*
3.  **Control:** Use commands like `/vol level:50` or `/screen`.

### Command List
| Command | Description |
| :--- | :--- |
| `/auth` | Unlocks the bot for a set time (10 min). |
| `/lockdown` | Instantly locks the bot and ends the session. |
| `/screen` | Sends a screenshot of the main monitor. |
| `/cam` | Takes a photo using the default webcam. |
| `/cmd` | Executes a Windows CMD command (Admin only). |
| `/say` | Uses TTS to speak a message on the PC speakers. |
| `/locate` | Finds the PC location via IP Address. |

## 🛡️ Security Features

This bot is designed with "Paranoid Security" in mind:
* **Hard-coded Owner Check:** Even with the password, only the `OWNER_ID` can log in.
* **Honeypot System:** Strangers who guess the password are instantly banned.
* **Owner Immunity:** The code prevents the owner from accidentally banning themselves.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---
**Disclaimer:** This tool is intended for personal use on your own devices. The author is not responsible for misuse or damages caused by remote execution commands.