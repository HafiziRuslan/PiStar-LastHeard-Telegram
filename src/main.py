#!/usr/bin/python3

"""PiStar LastHeard Telegram - Telegram bot to monitor the last transmissions of a Pi-Star gateway"""

import asyncio
import datetime as dt
import glob
import logging
import os
import re
import threading
from datetime import datetime
from typing import Optional

import humanize
from dotenv import load_dotenv
from telegram.ext import Application as TelegramApplication
from telegram.ext import ApplicationBuilder

TG_BOTTOKEN: str = ''
TG_CHATID: str = ''
TG_TOPICID: str = ''
GW_IGNORE_TIME_MESSAGES: bool = True
TG_APP: Optional[TelegramApplication] = None
shutdown_flag = threading.Event()


def configure_logging():
	logging.basicConfig(
		level=logging.INFO, datefmt='%Y-%m-%dT%H:%M:%S', format='%(asctime)s | %(levelname)s | %(message)s'
	)


class MMDVMLogLine:
	timestamp: Optional[datetime] = None
	mode: str = ''
	callsign: str = ''
	destination: str = ''
	block: int = 0
	duration: float = 0.0
	packet_loss: int = 0
	ber: float = 0.0
	rssi: str = 'S0'
	rssi1: int = 0
	rssi2: int = 0
	rssi3: int = 0
	qrz_url: str = ''
	slot: int = 2
	is_voice: bool = True
	is_kerchunk: bool = False
	is_network: bool = True
	is_watchdog: bool = False

	def __init__(self, logline: str):
		"""Parses an MMDVM log line and initializes the attributes."""
		dmr_gw_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'DMR Slot (?P<slot>\d), received (?P<source>network) (?:late entry|voice header|end of voice transmission) '
			r'from (?P<callsign>[\w\d]+) to (?P<destination>(TG [\d\w]+)|[\d\w]+)'
			r'(?:, (?P<duration>[\d\.]+) seconds, (?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%)'
		)
		dmr_rf_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'DMR Slot (?P<slot>\d), received (?P<source>RF) (?:late entry|voice header|end of voice transmission) '
			r'from (?P<callsign>[\w\d]+) to (?P<destination>(TG [\d\w]+)|[\d\w]+)'
			r'(?:, (?P<duration>[\d\.]+) seconds, BER: (?P<ber>[\d\.]+)%, RSSI: (?P<rssi1>-[\d]+)/(?P<rssi2>-[\d]+)/(?P<rssi3>-[\d]+) dBm)'
		)
		dmr_data_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'DMR Slot (?P<slot>\d), received (?P<source>network|RF) data header '
			r'from (?P<callsign>[\w\d]+) to (?P<destination>(TG [\d\w]+)|[\d\w]+)'
			r'(?:, (?P<block>[\d]+) blocks)'
		)
		dstar_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'D-Star, (?:received )?(?P<source>network|RF) end of transmission '
			r'from (?P<callsign>[\w\d\s/]+) to (?P<destination>[\w\d\s]+)'
			r'(?:, | , )(?P<duration>[\d\.]+) seconds,\s+(?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%'
		)
		dstar_watchdog_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'D-Star, (?P<source>network|RF) watchdog has expired'
			r', (?P<duration>[\d\.]+) seconds,\s+(?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%'
		)
		ysf_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'YSF, received (?P<source>network|RF) end of transmission '
			r'from (?P<callsign>[\w\d\-/]+) to DG-ID (?P<dgid>\d+)'
			r', (?P<duration>[\d\.]+) seconds, (?P<packet_loss>[\d\.]+)% packet loss, BER: (?P<ber>[\d\.]+)%'
		)
		ysf_network_data_pattern = (
			r'^M: (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) '
			r'YSF, received network data '
			r'from (?P<callsign>[\w\d\-/]+)\s+to DG-ID (?P<dgid>\d+) at (?P<location>\S+)'
		)

		match = re.match(dmr_gw_pattern, logline)
		if match:
			self.mode = 'DMR'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.slot = int(match.group('slot'))
			self.is_network = match.group('source') == 'network'
			self.callsign = match.group('callsign').strip()
			self.destination = match.group('destination').strip()
			self.duration = float(match.group('duration'))
			self.packet_loss = int(match.group('packet_loss'))
			self.ber = float(match.group('ber'))
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign}'
			return
		match = re.match(dmr_rf_pattern, logline)
		if match:
			self.mode = 'DMR'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.slot = int(match.group('slot'))
			self.is_network = match.group('source') == 'network'
			self.callsign = match.group('callsign').strip()
			self.destination = match.group('destination').strip()
			self.duration = float(match.group('duration'))
			self.ber = float(match.group('ber'))
			self.rssi3 = int(match.group('rssi3'))
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign}'
			return
		match = re.match(dmr_data_pattern, logline)
		if match:
			self.mode = 'DMR-D'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.slot = int(match.group('slot'))
			self.is_network = match.group('source') == 'network'
			self.is_voice = False
			self.callsign = match.group('callsign').strip()
			self.destination = match.group('destination').strip()
			self.block = int(match.group('block'))
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign}'
			return
		match = re.match(dstar_pattern, logline)
		if match:
			self.mode = 'D-Star'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.is_network = match.group('source') == 'network'
			self.callsign = remove_double_spaces(match.group('callsign').strip())
			self.destination = match.group('destination').strip()
			self.duration = float(match.group('duration'))
			self.packet_loss = int(match.group('packet_loss'))
			self.ber = float(match.group('ber'))
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign.split("/")[0].strip()}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign.split("/")[0].strip()}'
			return
		match = re.match(dstar_watchdog_pattern, logline)
		if match:
			self.mode = 'D-Star'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.is_network = match.group('source') == 'network'
			self.duration = float(match.group('duration'))
			self.packet_loss = int(match.group('packet_loss'))
			self.ber = float(match.group('ber'))
			self.is_watchdog = True
			return
		match = re.match(ysf_pattern, logline)
		if match:
			self.mode = 'YSF'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.is_network = match.group('source') == 'network'
			self.is_voice = True
			self.callsign = match.group('callsign').strip()
			self.destination = f'DG-ID {match.group("dgid")}'
			self.duration = float(match.group('duration'))
			self.packet_loss = int(match.group('packet_loss'))
			self.ber = float(match.group('ber'))
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign.split("-")[0].strip()}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign.split("-")[0].strip()}'
			return
		match = re.match(ysf_network_data_pattern, logline)
		if match:
			self.mode = 'YSF-D'
			self.timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f')
			self.is_network = match.group('source') == 'network'
			self.is_voice = False
			self.callsign = match.group('callsign').strip()
			self.destination = f'DG-ID {match.group("dgid")} at {match.group("location").strip()}'
			if self.callsign.isnumeric():
				self.url = f'https://database.radioid.net/database/view?id={self.callsign.split("-")[0].strip()}'
			else:
				self.url = f'https://www.qrz.com/db/{self.callsign.split("-")[0].strip()}'
			return
		raise ValueError(f'Log line does not match expected format: {logline}')

	def __str__(self):
		"""Returns a string representation of the log line."""
		if self.rssi3 >= -93:
			self.rssi = '🟩S9'
		elif -99 <= self.rssi3 < -93:
			self.rssi = '🟩S8'
		elif -105 <= self.rssi3 < -99:
			self.rssi = '🟩S7'
		elif -111 <= self.rssi3 < -105:
			self.rssi = '🟨S6'
		elif -117 <= self.rssi3 < -111:
			self.rssi = '🟨S5'
		elif -123 <= self.rssi3 < -117:
			self.rssi = '🟨S4'
		elif -129 <= self.rssi3 < -123:
			self.rssi = '🟨S3'
		elif -135 <= self.rssi3 < -129:
			self.rssi = '🟥S2'
		elif -141 <= self.rssi3 < -135:
			self.rssi = '🟥S1'
		else:
			self.rssi = '🟥S0'
		self.rssi += f'+{93 + self.rssi3}dB ({self.rssi3}dBm)'
		self.is_kerchunk = True if self.duration < 2 else False
		base = f'Timestamp: {self.timestamp}, Mode: {self.mode}, Callsign: {self.callsign}, Destination: {self.destination}'
		if self.mode == 'DMR' or self.mode == 'DMR-D':
			base += f', Slot: {self.slot}'
			if self.is_voice:
				base += ', Type: Voice'
				if self.is_network:
					base += ', Source: Network'
					base += f', Duration: {self.duration}s, PL: {self.packet_loss}%, BER: {self.ber}%'
				else:
					base += ', Source: RF'
					base += f', Duration: {self.duration}s, BER: {self.ber}%, RSSI: {self.rssi}'
			else:
				base += ', Type: Data'
				if self.is_network:
					base += ', Source: Network'
				else:
					base += ', Source: RF'
				base += f', Blocks: {self.block}'
		return base

	def get_talkgroup_name(self) -> str:
		"""Returns the talkgroup name based on the destination."""
		tg_files = glob.glob('/usr/local/etc/TGList_*.txt')
		tg_name = ''
		if self.destination.startswith('TG '):
			for tg_file in tg_files:
				if os.path.isfile(tg_file):
					try:
						with open(tg_file, 'r', encoding='UTF-8', errors='replace') as file:
							for line in file:
								if line.startswith('#') or len(line.strip()) == 0:
									continue
								parts = line.strip().split(';')
								tgid = parts[0].strip()
								if tg_file.endswith('_BM.txt'):
									name = parts[2].strip()
								else:
									name = parts[1].strip()
								if tgid == self.destination.split()[-1] and name != '':
									tg_name = f' ({name})'
									break
					except IndexError:
						pass
					except Exception as e:
						logging.error('Error reading talkgroup file %s: %s', tg_file, e)
		return tg_name

	def get_caller_location(self) -> str:
		"""Returns the location of the caller based on the callsign."""
		caller_file = '/usr/local/etc/stripped.csv'
		caller = ''
		try:
			with open(caller_file, 'r', encoding='UTF-8', errors='replace') as file:
				for line in file:
					parts = line.strip().split(',')
					# id = parts[0].strip()
					call = parts[1].strip()
					fname = parts[2].strip()
					# city = parts[3].strip()
					# state = parts[4].strip()
					country = parts[5].strip()
					if call == self.callsign:
						caller = f' ({fname}-{country})'
						break
		except Exception as e:
			logging.error('Error reading caller file %s: %s', caller_file, e)
		return caller

	def get_telegram_message(self) -> str:
		"""Returns a formatted message for Telegram with emojis."""
		if self.mode == 'DMR':
			mode_icon = '📻'
		elif self.mode == 'DMR-D':
			mode_icon = '📟'
		elif self.mode == 'D-Star':
			mode_icon = '⭐'
		elif self.mode == 'YSF':
			mode_icon = '📡'
		elif self.mode == 'YSF-D':
			mode_icon = '📟'
		else:
			mode_icon = '📶'
		message = f'{mode_icon} <b>Mode</b>: {self.mode}'
		if self.mode == 'DMR' or self.mode == 'DMR-D':
			message += f' (Slot {self.slot})'
		message += f'\n🕒 <b>Time</b>: {datetime.strftime(self.timestamp.replace(tzinfo=dt.timezone.utc), "%d-%b-%Y %H:%M:%S %Z") if self.timestamp else dt.datetime.now(dt.timezone.utc).strftime("%d-%b-%Y %H:%M:%S %Z")}'
		if self.url:
			message += f'\n📡 <b>Caller</b>: <a href="{self.url}">{self.callsign}</a>{self.get_caller_location()}'
		else:
			message += f'\n📡 <b>Caller</b>: {self.callsign}{self.get_caller_location()}'
		message += f'\n🎯 <b>Target</b>: {self.destination}{self.get_talkgroup_name()}'
		message += f' [{"RF" if not self.is_network else "NET"}]'
		if self.is_voice:
			message += '\n🗣️ <b>Type</b>: Voice'
			if self.is_kerchunk:
				message += ' (Kerchunk)'
			else:
				message += f'\n⏰ <b>Duration</b>: {humanize.precisedelta(dt.timedelta(seconds=self.duration), minimum_unit="seconds", format="%0.0f")}'
				if self.ber > 0:
					message += f'\n📊 <b>BER</b>: {self.ber}%'
				if self.is_network:
					if self.packet_loss > 0:
						message += f'\n📈 <b>PL</b>: {self.packet_loss}%'
				else:
					message += f'\n📶 <b>RSSI</b>: {self.rssi}'
		else:
			message += '\n💾 <b>Type</b>: Data'
			message += f'\n📦 <b>Blocks</b>: {self.block}'
		if self.is_watchdog:
			message += '\n\n⚠️ <b>Warning</b>: Network watchdog expired'
		if self.mode == 'D-Star':
			if self.destination.startswith('CQCQCQ'):
				message += '\n\n📢 <b>Action</b>: Call to all stations'
			elif self.destination.endswith('L'):
				message += f'\n\n🔗 <b>Action</b>: Link to {self.destination[:-1]}'
			elif self.destination.endswith('U'):
				message += '\n\n❌ <b>Action</b>: Unlink reflector'
			elif self.destination.endswith('I'):
				message += '\n\nℹ️ <b>Action</b>: Get repeater info'
			elif self.destination.endswith('E'):
				message += '\n\n🔄 <b>Action</b>: Echo test'
		return message


def get_latest_mmdvm_log_path() -> str:
	"""Finds and returns the path to the most recent MMDVM log file."""
	logdir = '/var/log/pi-star'
	log_files = glob.glob(os.path.join(logdir, 'MMDVM-*.log'))
	if not log_files:
		raise ValueError(f'No MMDVM log files found in {logdir}')
	log_files.sort(key=os.path.getmtime, reverse=True)
	latest_log = log_files[0]
	# logging.info("Latest MMDVM log file: %s", latest_log)
	return latest_log


def get_last_line_of_file(file_path: str) -> str:
	"""Reads the last line of a file."""
	with open(file_path, 'r', encoding='UTF-8', errors='replace') as file:
		content = file.readlines()
		last_line = ''
		while len(last_line) < 10 and content:
			last_line = content.pop()
		if len(last_line) < 10:
			return ''
		last_line = last_line.replace('\n', '')
		last_line = last_line.strip()
		return last_line


async def logs_to_telegram(tg_message: str):
	"""Sends the log line to the Telegram bot."""
	global TG_APP
	if TG_APP:
		try:
			botmsg = await TG_APP.bot.send_message(
				chat_id=TG_CHATID,
				message_thread_id=TG_TOPICID,
				text=tg_message,
				parse_mode='HTML',
				link_preview_options={'is_disabled': True, 'prefer_small_media': True, 'show_above_text': True},
			)
			logging.info('Sent message to Telegram: %s/%s/%s', botmsg.chat_id, botmsg.message_thread_id, botmsg.message_id)
		except Exception as e:
			logging.error('Failed to send message to Telegram: %s', e)


def remove_double_spaces(text: str) -> str:
	"""Removes double spaces from a string."""
	while '  ' in text:
		text = text.replace('  ', ' ')
	return text


def load_env_variables():
	"""Load environment variables from .env file."""
	load_dotenv()
	global TG_BOTTOKEN, TG_CHATID, TG_TOPICID, GW_IGNORE_TIME_MESSAGES
	TG_BOTTOKEN = os.getenv('TG_BOTTOKEN', '')
	TG_CHATID = os.getenv('TG_CHATID', '')
	TG_TOPICID = os.getenv('TG_TOPICID', '0')
	GW_IGNORE_TIME_MESSAGES = os.getenv('GW_IGNORE_MESSAGES', 'True').lower() == 'true'
	if not TG_BOTTOKEN:
		logging.warning('TG_BOTTOKEN is not set in the environment variables.')
	if not TG_CHATID:
		logging.warning('TG_CHATID is not set in the environment variables.')
	if GW_IGNORE_TIME_MESSAGES:
		logging.info('GW_IGNORE_MESSAGES is set to true, messages from the gateway will be ignored.')
	logging.info('Environment variables loaded successfully.')


async def mmdvm_logs_observer():
	"""Watches the MMDVM logs and sends updates to the Telegram bot."""
	global TG_APP
	logging.info('Starting MMDVM log file retrieval...')
	last_event: Optional[datetime] = None
	current_log_path: Optional[str] = None
	try:
		while not shutdown_flag.is_set():
			try:
				latest_log = get_latest_mmdvm_log_path()
				if current_log_path != latest_log:
					logging.info('Switching to new log file: %s', latest_log)
					current_log_path = latest_log
				if current_log_path is None:
					logging.error('No log file path available')
					await asyncio.sleep(1)
					continue
				last_line = get_last_line_of_file(current_log_path)
				logging.debug('Last line of log file: %s', last_line)
				if not any(
					x in last_line
					for x in [
						'end of voice transmission',
						'end of transmission',
						'watchdog has expired',
						'received RF data header',
						'received network data header',
					]
				):
					logging.debug('Line does not contain transmission end marker, skipping.')
					await asyncio.sleep(1)
					continue
				parsed_line = MMDVMLogLine(last_line)
				logging.debug('Parsed log line: %s', parsed_line)
				if parsed_line.timestamp is not None and (last_event is None or parsed_line.timestamp > last_event):
					logging.info('New log entry: %s', parsed_line)
					last_event = parsed_line.timestamp
					if GW_IGNORE_TIME_MESSAGES and '/TIME' in parsed_line.callsign:
						logging.info('Ignoring time message from gateway.')
						continue
					tg_message = parsed_line.get_telegram_message()
					if tg_message and TG_APP:
						await logs_to_telegram(tg_message)
				else:
					logging.debug('No new log entry found.')
			except ValueError as e:
				logging.debug('Could not parse log line: %s', e)
			except OSError as e:
				logging.error('File system error reading log file: %s', e)
			except RuntimeError as e:
				logging.error('Runtime error reading log file: %s', e)
			finally:
				await asyncio.sleep(1)
	except Exception as e:
		logging.error('Error: %s', e)


async def main():
	"""Main function to initialize and run the Telegram bot and logs observer."""
	global TG_APP
	load_env_variables()
	tg_app_built = False
	while not tg_app_built:
		try:
			TG_APP = ApplicationBuilder().token(TG_BOTTOKEN).build()
			tg_app_built = True
			logging.info('Telegram application built successfully.')
		except Exception as e:
			logging.error('Error building Telegram application: %s', e)
			await asyncio.sleep(5)
	assert TG_APP is not None
	async with TG_APP:
		tg_app_started = False
		while not tg_app_started:
			try:
				logging.info('Starting Telegram bot...')
				await TG_APP.initialize()
				await TG_APP.start()
				tg_app_started = True
				logging.info('Telegram bot started successfully.')
			except Exception as e:
				logging.error('Error starting Telegram bot: %s', e)
				await asyncio.sleep(5)
		try:
			logging.info('Starting MMDVM logs observer...')
			await mmdvm_logs_observer()
		except asyncio.CancelledError:
			logging.info('MMDVM logs observer cancelled.')
		finally:
			await TG_APP.stop()


if __name__ == '__main__':
	configure_logging()
	try:
		logging.info('Starting the application...')
		asyncio.run(main())
	except KeyboardInterrupt:
		logging.info('Stopping application...')
	except Exception as e:
		logging.error('An error occurred: %s', e)
	finally:
		logging.info('Exiting script...')
