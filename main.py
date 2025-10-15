#!/usr/bin/env python3

import os
import re
import glob
import logging
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
from telegram.ext import Application as TelegramApplication
from typing import Optional

# Environment variables
TG_BOTTOKEN: str = ""
TG_CHATID: str = ""
GW_IGNORE_TIME_MESSAGES: bool = True

# Project variables
TG_APP: Optional[TelegramApplication] = None
shutdown_flag = threading.Event() # Create a shutdown flag


def configure_logging():
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    # handlers=[
    #   logging.FileHandler("dstar_log_parser.log"),
    #   logging.StreamHandler()
    # ]
  )
  logging.getLogger("hpack").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.getLogger("asyncio").setLevel(logging.WARNING)
  logging.getLogger("telegram").setLevel(logging.WARNING)
  logging.getLogger("httpx").setLevel(logging.WARNING)


class MMDVMLogLine:
  timestamp: Optional[datetime] = None
  mode: str = "" # "DMR" or "DSTAR" or "YSF"
  callsign: str = ""
  destination: str = ""
  block: str = ""
  duration: str = ""
  packet_loss: str = ""
  ber: str = ""
  rssi: str = ""
  qrz_url: str = ""
  slot: str = "" # For DMR
  is_voice: bool = True # False for data
  is_network: bool = True
  is_watchdog: bool = False

  def __init__(self, logline: str):
    """
    Parses an MMDVM log line and initializes the attributes.
    """

    # Check if it's a DMR line
    dmr_gw_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"DMR Slot (?P<slot>\d), received (?P<source>network) (?:late entry|voice header|end of voice transmission) "
      r"from (?P<callsign>[\w\d]+) to (?P<destination>(TG \d+)|[\d\w]+)"
      r"(?:, (?P<duration>[\d\.]+) seconds, (?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%)"
    )
    dmr_rf_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"DMR Slot (?P<slot>\d), received (?P<source>RF) (?:late entry|voice header|end of voice transmission) "
      r"from (?P<callsign>[\w\d]+) to (?P<destination>(TG \d+)|[\d\w]+)"
      r"(?:, (?P<duration>[\d\.]+) seconds, BER: (?P<ber>[\d\.]+)%, RSSI: (?P<rssi>[-\d\/]+) dBm)?"
    )
    dmr_data_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"DMR Slot (?P<slot>\d), (?:received|ended) (?P<source>network|RF) (?:Data Preamble CSBK|data header|data transmission) (?:\(\d+ to follow\)) "
      r"from (?P<callsign>[\w\d]+) to (?P<destination>(TG \d+)|[\d\w]+)"
      r"(?:, (?P<block>[\d]+) blocks)"
    )

    # Check if it's a D-Star line (with "from...to")
    dstar_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"D-Star, (?:received )?(?P<source>network|RF) end of transmission "
      r"from (?P<callsign>[\w\d\s/]+) to (?P<destination>[\w\d\s]+)"
      r"(?:, | , )(?P<duration>[\d\.]+) seconds,\s+(?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%"
    )

    # Check if it's a D-Star watchdog line (without "from...to")
    dstar_watchdog_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"D-Star, (?P<source>network|RF) watchdog has expired"
      r", (?P<duration>[\d\.]+) seconds,\s+(?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%"
    )

    # Check if it's a YSF end of transmission line
    ysf_pattern = (
      r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
      r"YSF, received (?P<source>network|RF) end of transmission "
      r"from (?P<callsign>[\w\d\-/]+) to DG-ID (?P<dgid>\d+)"
      r", (?P<duration>[\d\.]+) seconds, (?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%"
    )
    # Check if it's a YSF network data line (without statistics)
    ysf_network_data_pattern = (
        r"^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
        r"YSF, received network data "
        r"from (?P<callsign>[\w\d\-/]+)\s+to DG-ID (?P<dgid>\d+) at (?P<location>\S+)"
    )

    match = re.match(dmr_gw_pattern, logline)
    if match:
      self.mode = "DMR"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.slot = match.group("slot")
      self.is_network = match.group("source") == "network"
      self.is_voice = True
      self.callsign = match.group("callsign").strip()
      self.destination = match.group("destination").strip().replace("TG ", "TG")
      self.duration = match.group("duration")
      self.packet_loss = match.group("packet_loss")
      self.ber = match.group("ber")
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign}"
      return

    match = re.match(dmr_rf_pattern, logline)
    if match:
      self.mode = "DMR"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.slot = match.group("slot")
      self.is_network = match.group("source") == "network"
      self.is_voice = True
      self.callsign = match.group("callsign").strip()
      self.destination = match.group("destination").strip().replace("TG ", "TG")
      self.duration = match.group("duration")
      self.ber = match.group("ber")
      self.rssi = match.group("rssi")
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign}"
      return

    match = re.match(dmr_data_pattern, logline)
    if match:
      self.mode = "DMR"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.slot = match.group("slot")
      self.is_network = match.group("source") == "network"
      self.is_voice = False
      self.callsign = match.group("callsign").strip()
      self.destination = match.group("destination").strip().replace("TG ", "TG")
      self.block = match.group("block")
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign}"
      return

    match = re.match(dstar_pattern, logline)
    if match:
      self.mode = "D-Star"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.is_network = match.group("source") == "network"
      self.callsign = remove_double_spaces(match.group("callsign").strip())
      self.destination = match.group("destination").strip()
      self.duration = match.group("duration")
      self.packet_loss = match.group("packet_loss")
      self.ber = match.group("ber")
      self.is_watchdog = False
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign.split('/')[0].strip()}"
      return

    match = re.match(dstar_watchdog_pattern, logline)
    if match:
      self.mode = "D-Star"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.is_network = match.group("source") == "network"
      self.callsign = "Unknown"
      self.destination = "Unknown"
      self.duration = match.group("duration")
      self.packet_loss = match.group("packet_loss")
      self.ber = match.group("ber")
      self.is_watchdog = True
      self.qrz_url = ""
      return

    match = re.match(ysf_pattern, logline)
    if match:
      self.mode = "YSF"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.is_network = match.group("source") == "network"
      self.callsign = match.group("callsign").strip()
      self.destination = f"DG-ID {match.group('dgid')}"
      self.duration = match.group("duration")
      self.packet_loss = match.group("packet_loss")
      self.ber = match.group("ber")
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign.split('-')[0].strip()}"
      return

    match = re.match(ysf_network_data_pattern, logline)
    if match:
      self.mode = "YSF"
      self.timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S.%f")
      self.is_network = True  # Always network for this type
      self.callsign = match.group("callsign").strip()
      self.destination = f"DG-ID {match.group('dgid')} at {match.group('location').strip()}"
      self.duration = "N/A"
      self.packet_loss = "N/A"
      self.ber = "N/A"
      self.qrz_url = f"https://www.qrz.com/db/{self.callsign.split('-')[0].strip()}"
      return

    raise ValueError(f"Log line does not match expected format: {logline}")

  def __str__(self):
    """
    Returns a string representation of the log line.
    """
    base = f"Timestamp: {self.timestamp}, Mode: {self.mode}, Callsign: {self.callsign}, Destination: {self.destination}"
    if self.mode == "DMR":
      base += f", Slot: {self.slot}"
      if self.is_voice:
        base += ", Type: Voice"
        if self.is_network:
          base += ", Source: Network"
          base += f", Duration: {self.duration}s, PL: {self.packet_loss}%, BER: {self.ber}%"
        else:
          base += ", Source: RF"
          base += f", Duration: {self.duration}s, BER: {self.ber}%, RSSI: {self.rssi}dBm"
      else:
        base += ", Type: Data"
        if self.is_network:
          base += ", Source: Network"
        else:
          base += ", Source: RF"
        base += f", Blocks: {self.block}"
    return base

  def get_telegram_message(self) -> str:
    """
    Returns a formatted message for Telegram with emojis.
    """
    # Mode icon
    if self.mode == "DMR":
      mode_icon = "📻"
    elif self.mode == "D-Star":
      mode_icon = "⭐"
    elif self.mode == "YSF":
      mode_icon = "📡"
    else:
      mode_icon = "📶"

    message = f"{mode_icon} <b>Mode</b>: {self.mode}"

    if self.mode == "DMR":
      message += f" (Slot {self.slot})"

    message += f"\n🕒 <b>Time</b>: {self.timestamp.isoformat(sep='T', timespec='seconds') if self.timestamp else 'Unknown'}\n"

    # Add callsign with or without QRZ link
    if self.qrz_url:
      message += f"\n📡 <b>Caller</b>: <a href=\"{self.qrz_url}\">{self.callsign}</a>"
    else:
      message += f"\n📡 <b>Caller</b>: {self.callsign}"

    message += f" ({'RF' if not self.is_network else 'NET'})"
    message += f"\n🎯 <b>Target</b>: {self.destination}"
    if self.is_voice:
      message += "\n\n🗣️ <b>Type</b>: Voice"
      message += f"\n⏱️ <b>Duration</b>: {self.duration} seconds"
      message += f"\n📊 <b>BER</b>: {self.ber} %"
      if self.is_network:
        message += f"\n📈 <b>PL</b>: {self.packet_loss} %"
      else:
        message += f"\n📶 <b>RSSI</b>: {self.rssi} dBm"
    else:
      message += "\n\n💾 <b>Type</b>: Data"
      message += f"\n📦 <b>Blocks</b>: {self.block}"

    if self.is_watchdog:
      message += "\n\n⚠️ <b>Warning</b>: Network watchdog expired"

    # Check for special D-Star destinations
    if self.mode == "D-Star":
      if self.destination.startswith("CQCQCQ"):
        message += "\n\n📢 <b>Action</b>: Call to all stations"
      elif self.destination.endswith("L"):
        message += f"\n\n🔗 <b>Action</b>: Link to {self.destination[:-1]}"
      elif self.destination.endswith("U"):
        message += "\n\n❌ <b>Action</b>: Unlink reflector"
      elif self.destination.endswith("I"):
        message += "\n\nℹ️ <b>Action</b>: Get repeater info"
      elif self.destination.endswith("E"):
        message += "\n\n🔄 <b>Action</b>: Echo test"

    return message


def get_latest_mmdvm_log_path() -> str:
  """
  Finds and returns the path to the most recent MMDVM log file.
  """
  logdir = "/var/log/pi-star"

  # Find all MMDVM-*.log files
  log_files = glob.glob(os.path.join(logdir, "MMDVM-*.log"))

  if not log_files:
    raise ValueError(f"No MMDVM log files found in {logdir}")

  # Sort by modification time (most recent first)
  log_files.sort(key=os.path.getmtime, reverse=True)

  latest_log = log_files[0]
  # logging.info("Latest MMDVM log file: %s", latest_log)

  return latest_log


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
  Sends the log line to the Telegram bot.
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
    except Exception as e:
      logging.error("Failed to send message to Telegram: %s", e)


def remove_double_spaces(text: str) -> str:
  """
  Removes double spaces from a string.
  """
  while " " in text:
    text = text.replace(" ", " ")
  return text

### Environment variables ###


def load_env_variables():
  """
  Load environment variables from .env file.
  """
  # Load environment variables from .env file
  load_dotenv()

  # Load environment variables
  global TG_BOTTOKEN, TG_CHATID, GW_IGNORE_TIME_MESSAGES

  TG_BOTTOKEN = os.getenv("TG_BOTTOKEN", "")
  TG_CHATID = os.getenv("TG_CHATID", "")
  GW_IGNORE_TIME_MESSAGES = os.getenv("GW_IGNORE_MESSAGES", "True").lower() == "true"

  # Validate environment variables
  if not TG_BOTTOKEN:
    raise ValueError("TG_BOTTOKEN is not set in the environment variables.")
  if not TG_CHATID:
    raise ValueError("TG_CHATID is not set in the environment variables.")
  if GW_IGNORE_TIME_MESSAGES:
    logging.warning("GW_IGNORE_MESSAGES is set to True, messages from the gateway will be ignored.")

  logging.info("Environment variables loaded successfully.")


async def mmdvm_logs_observer():
  """
  Watches the MMDVM logs and sends updates to the Telegram bot.
  """
  global TG_APP

  logging.info("Starting MMDVM log file retrieval...")

  last_event: Optional[datetime] = None
  current_log_path: Optional[str] = None

  try:
    while not shutdown_flag.is_set():
      try:
        # Check if we need to update the log file path
        latest_log = get_latest_mmdvm_log_path()
        if current_log_path != latest_log:
          logging.info("Switching to new log file: %s", latest_log)
          current_log_path = latest_log

        # Parse the last line of the log file
        if current_log_path is None:
            logging.error("No log file path available")
            await asyncio.sleep(1)
            continue
        last_line = get_last_line_of_file(current_log_path)
        logging.debug("Last line of log file: %s", last_line)

        # Skip lines that don't match our patterns
        if not any(x in last_line for x in ["end of voice transmission", "end of transmission", "ended RF data transmission", "watchdog has expired", "received network data"]):
          logging.debug("Line does not contain transmission end marker, skipping.")
          await asyncio.sleep(1)
          continue

        # Create a MMDVMLogLine object
        parsed_line = MMDVMLogLine(last_line)
        logging.debug("Parsed log line: %s", parsed_line)

        # Check if the timestamp is new (ensure parsed_line.timestamp is not None)
        if parsed_line.timestamp is not None and (last_event is None or parsed_line.timestamp > last_event):
          logging.info("New log entry: %s", parsed_line)
          last_event = parsed_line.timestamp

          # Check if the message should be ignored
          if GW_IGNORE_TIME_MESSAGES and "/TIME" in parsed_line.callsign:
            logging.info("Ignoring time message from gateway.")
            continue

          # Build the Telegram message
          tg_message = parsed_line.get_telegram_message()
          if tg_message and TG_APP:
            await logs_to_telegram(tg_message)
        else:
          logging.debug("No new log entry found.")
      except ValueError as e:
        # Log parsing errors at debug level (expected for non-matching lines)
        logging.debug("Could not parse log line: %s", e)
      except OSError as e:
        logging.error("File system error reading log file: %s", e)
      except RuntimeError as e:
        logging.error("Runtime error reading log file: %s", e)
      finally:
        # Sleep for a while before checking again
        await asyncio.sleep(1)
  except Exception as e:
    logging.error("Error: %s", e)


async def main():
  """
  Main function to initialize and run the Telegram bot and logs observer.
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
      logging.error("Error building Telegram application: %s", e)
      await asyncio.sleep(5)

  assert TG_APP is not None
  async with TG_APP:
    tg_app_started = False
    while not tg_app_started:
      try:
        logging.info("Starting Telegram bot...")
        await TG_APP.initialize()
        await TG_APP.start()
        tg_app_started = True
        logging.info("Telegram bot started successfully.")
      except Exception as e:
        logging.error("Error starting Telegram bot: %s", e)
        await asyncio.sleep(5)

    try:
      # Run the MMDVM logs observer in parallel
      logging.info("Starting MMDVM logs observer...")
      await mmdvm_logs_observer()
    except asyncio.CancelledError:
      logging.info("MMDVM logs observer cancelled.")
    finally:
      # Stop the Telegram bot
      await TG_APP.stop()


if __name__ == "__main__":
  configure_logging()

  try:
    logging.info("Starting the application...")
    asyncio.run(main())
  except KeyboardInterrupt:
    logging.info("Stopping application...")
  except Exception as e:
    logging.error("An error occurred: %s", e)
  finally:
    logging.info("Exiting script...")
