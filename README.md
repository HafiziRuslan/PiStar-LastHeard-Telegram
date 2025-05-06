# Pi-Star Last Heard Telegram Bot

This project is a Python-based Telegram bot that monitors DStar logs and sends updates to a specified Telegram chat. It uses the `python-telegram-bot` library to interact with Telegram and parses DStar log files to extract relevant information.

## Features

- Monitors DStar log files for new entries.
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
git clone https://github.com/iu2frl/pistar-lastheard-telegram
cd pistar-lastheard-telegram
```

2. Create a `.env` file in the project directory and add the following environment variables:

```
TG_BOTTOKEN=<your-telegram-bot-token>
TG_CHATID=<your-telegram-chat-id>
GW_ADDRESS=172.16.0.1
```

## Usage

The bot can be launched using the following command:

```bash
./main.sh
```

The script will:
- Create and activate a virtual environment (if not already created).
- Install the required dependencies.
- Start the bot and monitor the DStar logs.

## Automatic execution

To run the script at boot, add an entry in cron:

```bash
@reboot cd /home/pi-star/lastheard && chmod +x ./main.sh  && ./main.sh > /tmp/lastheard.txt 2>&1
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
- `dotenv`: For loading environment variables from a `.env` file.

Install them using:

```bash
pip install -r requirements.txt
```

## Logging

The bot uses Python's `logging` module to log events and errors. Logs are displayed in the console for easy debugging.

## Contributing

Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the GNU GPL v3 License. See the `LICENSE` file for details.
