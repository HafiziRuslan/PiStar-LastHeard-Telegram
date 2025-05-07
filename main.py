import os
import re
import glob
import logging
import time
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
from telegram.ext import Application as TelegramApplication

# Environment variables
TG_BOTTOKEN = ""
TG_CHATID = ""
GW_ADDRESS = ""

# Project variables
TG_APP: TelegramApplication = None
shutdown_flag = threading.Event()  # Create a shutdown flag

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        # handlers=[
        #     logging.FileHandler("dstar_log_parser.log"),
        #     logging.StreamHandler()
        # ]
    )
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

class DstarLogLine:
    timestamp: datetime = None
    my: str = ""
    your: str = ""
    rpt1: str = ""
    rpt2: str = ""
    src: str = ""
    qrz_url: str = ""

    def __init__(self, logline: str):
        """
        Parses a DStar log line and initializes the attributes.
        """
        # Regex to extract fields from the log line
        pattern = (
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): (.*) - "
            r"My: (?P<my>[\w\s/]+)\s+Your: (?P<your>[\w\s]+)\s+"
            r"Rpt1: (?P<rpt1>[\w\s]+)\s+Rpt2: (?P<rpt2>[\w\s]+)\s+"
            r"Flags: [\w\s]+ \((?P<src>[\d\.]+:\d+)\)"
        )
        match = re.match(pattern, logline)
        if not match:
            raise ValueError(f"Log line does not match expected format: {logline}")

        # Extract and assign fields
        self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S")
        self.my = remove_double_spaces(match.group("my").strip())
        self.your = remove_double_spaces(match.group("your").strip())
        self.rpt1 = remove_double_spaces(match.group("rpt1").strip())
        self.rpt2 = remove_double_spaces(match.group("rpt2").strip())
        self.src = remove_double_spaces(match.group("src").strip())
        self.qrz_url = f"https://www.qrz.com/db/{self.my.split('/')[0].strip()}"

    def __str__(self):
        """
        Returns a string representation of the log line.
        """
        return (
            f"Timestamp: {self.timestamp}, My: {self.my}, Your: {self.your}, "
            f"Rpt1: {self.rpt1}, Rpt2: {self.rpt2}, Src: {self.src}"
        )

    def get_telegram_message(self) -> str:
        """
        Returns a formatted message for Telegram.
        """
        message = (
            f"<b>Time:</b> {self.timestamp} UTC\n"
            f"<b>Call:</b> <a href=\"{self.qrz_url}\">{self.my}</a>\n"
            f"<b>Dest:</b> {self.your}\n"
            f"<b>Rpt1:</b> {self.rpt1}\n"
            f"<b>Rpt2:</b> {self.rpt2}"
        )

        if GW_ADDRESS:
            message += f"\n<b>Src: </b> {'Local RF' if GW_ADDRESS in self.src else 'Network'}"
        
        return message

        
def get_dstar_logs_path() -> str:
    """
    Finds and returns the path to the latest DStar log file.
    Copied from: https://github.com/kencormack/pistar-lastqso/blob/main/pistar-lastqso line 444
    """
    logdir = None
    logroot = None

    # Read the /etc/mmdvmhost file to extract LogDir and LogRoot
    with open('/etc/mmdvmhost', 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.strip() == "[Log]":
                for j in range(i + 1, i + 5):  # Look at the next 4 lines
                    if lines[j].startswith("FilePath="):
                        logdir = lines[j].split("=", 1)[1].strip()
                    elif lines[j].startswith("FileRoot="):
                        logroot = lines[j].split("=", 1)[1].strip()
                break

    if not logdir or not logroot:
        raise ValueError("Log directory or root not found in /etc/mmdvmhost")

    logging.info(f"Log directory: {logdir}")

    return logdir

def get_last_line_of_file(file_path: str) -> str:
    """
    Reads the last line of a file.
    """
    with open(file_path, 'r', encoding="UTF-8", errors="replace") as file:
        # Read the entire file into memory
        content = file.readlines()

        # Extract the last line only if anything is present
        last_line = ""

        while len(last_line) < 10 and content:
            # Read the last line
            last_line = content.pop()
        
        if len(last_line) < 10:
            return ""
        
        # Remove any trailing newline characters
        last_line = last_line.replace('\n', '')
        # Remove any leading and trailing whitespace
        last_line = last_line.strip()
        # Return the last line
        return last_line

async def logs_to_telegram(tg_message: str):
    """
    Sends the DStar log line to the Telegram bot.
    """
    global TG_APP

    if TG_APP:
        try:
            # Send the message to the Telegram chat
            await TG_APP.bot.send_message(
                chat_id=TG_CHATID,
                text=tg_message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            logging.info("Message sent to Telegram.")
        except Exception as e:
            logging.error(f"Failed to send message to Telegram: {e}")

def remove_double_spaces(text: str) -> str:
    """
    Removes double spaces from a string.
    """
    while "  " in text:
        text = text.replace("  ", " ")
    return text

### Environment variables ###

def load_env_variables():
    """
    Load environment variables from .env file.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Load environment variables
    global TG_BOTTOKEN, TG_CHATID, GW_ADDRESS
    
    TG_BOTTOKEN = os.getenv("TG_BOTTOKEN")
    TG_CHATID = os.getenv("TG_CHATID")
    GW_ADDRESS = os.getenv("GW_ADDRESS")

    # Validate environment variables
    if not TG_BOTTOKEN:
        raise ValueError("TG_BOTTOKEN is not set in the environment variables.")
    if not TG_CHATID:
        raise ValueError("TG_CHATID is not set in the environment variables.")
    if not GW_ADDRESS:
        logging.warning("Invalid GW_ADDRESS, the src field will not be set.")
        GW_ADDRESS = None

    logging.info("Environment variables loaded successfully.")

async def dstar_logs_observer():
    """
    Watches the DStar logs and sends updates to the Telegram bot.
    """
    global TG_APP

    logging.info("Starting DStar log file retrieval...")

    last_event: datetime = None

    try:
        # Retrieve the latest DStar log file
        log_path = f"{get_dstar_logs_path()}/Headers.log"
        logging.info(f"Latest DStar log file: {log_path}")
        while not shutdown_flag.is_set():
            try:
                # Parse the last line of the log file
                last_line = get_last_line_of_file(log_path)
                logging.debug(f"Last line of log file: {last_line}")
                # Create a DstarLogLine object
                parsed_line = DstarLogLine(last_line)
                logging.debug(f"Parsed log line: {parsed_line}")
                # Check if the timestamp is new
                if last_event is None or parsed_line.timestamp > last_event:
                    logging.info(f"New log entry: {parsed_line}")
                    last_event = parsed_line.timestamp
                    # Build the Telegram message
                    tg_message = parsed_line.get_telegram_message()
                    if tg_message and TG_APP:
                        await logs_to_telegram(tg_message)
                else:
                    logging.debug("No new log entry found.")
            except Exception as e:
                logging.error(f"Error reading log file: {e}")
            finally:
                # Sleep for a while before checking again
                await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    """
    Main function to initialize and run the Telegram bot and DStar logs observer.
    """
    global TG_APP

    # Load environment variables
    load_env_variables()

    # Build the Telegram application
    tg_app_built = False
    while not tg_app_built:
        try:
            TG_APP = ApplicationBuilder().token(TG_BOTTOKEN).build()
            tg_app_built = True
            logging.info("Telegram application built successfully.")
        except Exception as e:
            logging.error(f"Error building Telegram application: {e}")
            await asyncio.sleep(5)

    async with TG_APP:
        tg_app_started = False
        while not tg_app_started:
            try:
                logging.info("Starting Telegram bot...")
                await TG_APP.initialize()
                await TG_APP.start()
                await TG_APP.updater.start_polling()
                tg_app_started = True
                logging.info("Telegram bot started successfully.")
            except Exception as e:
                logging.error(f"Error starting Telegram bot: {e}")
                await asyncio.sleep(5)

        try:
            # Run the DStar logs observer in parallel
            logging.info("Starting DStar logs observer...")
            await dstar_logs_observer()
        except asyncio.CancelledError:
            logging.info("DStar logs observer cancelled.")
        finally:
            # Stop the Telegram bot
            await TG_APP.updater.stop()
            await TG_APP.stop()

### Script entry point ###

if __name__ == "__main__":
    configure_logging()

    try:
        logging.info("Starting the application...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopping application...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Exiting script...")