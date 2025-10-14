# Pi-Star Last Heard Telegram Bot

This project is a Python-based Telegram bot that monitors DStar logs and sends updates to a specified Telegram chat. It uses the `python-telegram-bot` library to interact with Telegram and parses DStar or MMDVM log files to extract relevant information.

## Features

- Monitors DStar/MMDVM log files for new entries.
- Parses log entries and formats them into readable messages.
- Sends updates to a Telegram chat using a bot.
- Configurable via environment variables.

## Prerequisites

- Python 3.7 or higher
- A Telegram bot token (create one using [BotFather](https://core.telegram.org/bots#botfather)).
- A Telegram chat ID where the bot will send messages.
- Access to the DStar log files on your Pi-Star system.

## Preparation

1. Clone the repository to your Pi-Star system:

```bash
git clone https://github.com/HafiziRuslan/pistar-lastheard-telegram
cd pistar-lastheard-telegram
```

2. Create a `.env` file in the project directory and add the following environment variables:

```env
# Telegram bot token
TG_BOTTOKEN=<your-telegram-bot-token>
# Target chat where to send messages
TG_CHATID=<your-telegram-chat-id>
# Address of the RP2C device (only for dstar gateway log monitoring)
GW_ADDRESS=172.16.0.1
# Ignore the time server messages?
GW_IGNORE_TIME_MESSAGES=true
```
<!--
3. Choose the script you want to use to run the bot:
   - `main-dstargateway.py`: Run the bot which monitors the Dstar Gateway log file (for gateways running ICOM hardware).
   - `main-mmdvm.py`: Run the bot which monitors the MMDVM log file (for gateways running MMDVM hardware).

4. Rename the chosen script to `main.py`
   - For example, if you want to use the Dstar Gateway log monitoring script:

```bash
mv main-dstargateway.py main.py
```
 -->
## Usage

The bot can be launched using the following command:

```bash
sudo chmod a+x ./main.sh
./main.sh
```

The script will:

- Create and activate a virtual environment (if not already created).
- Install the required dependencies.
- Start the bot and monitor the DStar logs.

## Automatic execution

To run the script at boot, add an entry in cron:

```bash
@reboot cd /home/pi-star/lastheard && ./main.sh > /tmp/lastheard.txt 2>&1
```

## File Structure

- `main.py`: The main script that contains the bot logic and log monitoring functionality.
- `main.sh`: A shell script to set up the environment and run the bot.
- `requirements.txt`: A list of Python dependencies required for the project.

## How It Works

1. **Log Monitoring**:
    The bot reads the latest DStar log file and extracts the last line. It parses the log line using a regex pattern to extract fields like timestamp, callsigns, and repeaters.

2. **Telegram Integration**:
    The bot formats the parsed log entry into an HTML message and sends it to the specified Telegram chat using the `python-telegram-bot` library.

3. **Environment Variables**:
    The bot uses environment variables (`TG_BOTTOKEN` and `TG_CHATID`) to configure the Telegram bot token and chat ID.

## Dependencies

> [!TIP]
> If using the `main.sh` script, all dependencies and virtual environment are created automatically

The project requires the following Python libraries:

- `python-telegram-bot`: For interacting with the Telegram Bot API.
- `python-dotenv`: For loading environment variables from a `.env` file.

Install them using:

```bash
pip install -r requirements.txt
```

## Tips when running on Pi-Star

As Pi-Star starts the device in read-only mode, I suggest commenting out the `pip install ...` line in `main.sh` to avoid errors due to read-only mode

## Logging

The bot uses Python's `logging` module to log events and errors. Logs are displayed in the console for easy debugging.

## Contributing

Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the GNU GPL v3 License. See the `LICENSE` file for details.
