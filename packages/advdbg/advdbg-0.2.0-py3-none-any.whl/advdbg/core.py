'''
Welcome to Advanced Debug.
Core module.
'''

import os
from datetime import datetime
import random
from typing import Dict, Any, Optional, List

from .colors import Colors

listPhrases = ['Writting some lines.', "Don't forgot to define!", 'Waiting for your command.']
randomPhrase = random.choice(listPhrases)

class AdvDBG:
	_category_store: Dict[str, Dict[str, Any]] = {}
	_defined_categories: Dict[str, 'AdvDBG'] = {}
	
	def __init__(self, title='DEBUG', activated=False, notify=False, logging=True, legacy=False):
		if isinstance(title, str) and isinstance(activated, bool) and isinstance(notify, bool):
			self.title = title
			self.activated = False
			self._defed = False
			self.notify = notify
			self.logging = logging
			self.legacy = legacy
		else:
			raise ValueError('Some parameters do not match required types')
			
		if title not in self._category_store:
			self._category_store[title] = {}
		if title not in self._defined_categories:
			self._defined_categories[title] = self
		
	@classmethod
	def define(cls, title='DEBUG', activated=True, notify=False, logging=True, legacy=False):
		'''Defines your debug category.
		:param title: Title of your category
		:param activated: Toggle availability of category
		:param notify: Toggles notification if category is not activated
		:param logging: Toggles is it logging
		:param legacy: Use old style?'''
		inst = cls(title, activated, notify, logging, legacy)
		inst.title = title
		inst.activated = True
		inst.notify = notify
		inst.logging = logging
		inst.legacy = legacy
		inst._defed = True
		
		cls._category_store[title] = {
			'title': title,
			'activated': activated,
			'notify': notify,
			'logging': logging,
			'legacy': legacy,
			'created_at': datetime.now()
		}
		cls._defined_categories[title] = inst
		return inst
		
	@classmethod
	def get_category_settings(cls, category: str) -> Optional[Dict[str, Any]]:
		if category in cls._category_store:
			return cls._category_store[category].copy()
		return None
	
	@classmethod
	def get_all_categories(cls) -> List[str]:
		return list(cls._category_store.keys())
		
	@classmethod
	def export_all_data(cls) -> Dict[str, Any]:
		return {
			'categories': cls._category_store.copy(),
			'total_categories': len(cls._category_store),
			'export_timestamp': datetime.now().isoformat(),
			'version': '1.0'
		}
	
	def _write_to_log(self, text, log_type='INFO'):
		'''For-Module only method.'''
		if not self.logging:
			return
		
		try:
			# Creating logs directory relative to the current working directory
			logs_dir = os.path.join(os.getcwd(), 'logs')
			os.makedirs(logs_dir, exist_ok=True)
			
			current_date = datetime.now().strftime("%d.%m.%Y")
			filename = f"log_{current_date}.txt"
			filepath = os.path.join(logs_dir, filename)
			
			current_time = datetime.now().strftime("%H:%M:%S")
			log_entry = f"{self.title} {current_time} | {text}\n"
			
			file_exists = os.path.exists(filepath)
			
			with open(filepath, 'a', encoding='utf-8') as f:
				if not file_exists:
					f.write(f"/// Advanced Debugger\n")
					f.write(f"Category: {self.title}\n")
					f.write(randomPhrase)
					f.write("\n\n")
				
				f.write(log_entry)
				
		except Exception as e:
			print(f"\033[33mWARNING\033[0m | Failed to write to log file: {e}")
		
	def info(self, text):
			"""Print debug information
			Type: INFO
		
			:param text: Text to show"""
			if not isinstance(text, str):
				try:
						text = str(text)
				except Exception as e:
						text = f"Cannot convert to string format: {e}"
		
			if self.activated:
				if self.legacy:
					print(f'[\033[90mINFO \033[95m{self.title} at {datetime.now().strftime("%D, %H:%M:%S")}\033[0m] {text} \033[0m')
				elif not self.legacy:
					print(f'{Colors.INFO} Info - {self.title} ({datetime.now().strftime("%D, %H:%M:%S")}) | {text}')
				if self.logging:
					self._write_to_log(text, 'INFO')
			elif self.notify:
				print(f'Notification from {self.title}: Tryed to output when disactivated.\n\033[93mTip: \033[0mIf you are did not want to saw these notifications, turn off NOTIFY property with using notify=False\033[0m')
			else:
				return
				
	def warn(self, text):
			if not isinstance(text, str):
					try:
						text = str(text)
					except Exception as e:
						text = f"Cannot convert to string format: {e}"
			
			if self.activated:
				if self.legacy:
					print(f'[\033[90mWARN \033[95m{self.title} at {datetime.now().strftime("%D, %H:%M:%S")}\033[0m] {text} \033[0m')
				elif not self.legacy:
					print(f'{Colors.WARN} Warn - {self.title} ({datetime.now().strftime("%D, %H:%M:%S")}) | {text}')
				if self.logging:
					self._write_to_log(text, 'WARN')
			elif self.notify:
				print(f'Notification from {self.title}: Tryed to output when disactivated.\n\033[93mTip: \033[0mIf you are did not want to saw these notifications, turn off NOTIFY property with using notify=False')
			else:
				return
				
	def error(self, text):
			if not isinstance(text, str):
					try:
						text = str(text)
					except Exception as e:
						text = f"Cannot convert to string format: {e}"
						
			if self.activated:
				if self.legacy:
					print(f'[\033[33mERROR \033[95m{self.title} at {datetime.now().strftime("%D, %H:%M:%S")}\033[0m] {text} \033[0m')
				elif not self.legacy:
					print(f'{Colors.ERROR} Error - {self.title} ({datetime.now().strftime("%D, %H:%M:%S")}) | {text}')
				if self.logging:
					self._write_to_log(text, 'ERROR')
			elif self.notify:
				print(f'Notification from {self.title}: Tryed to output when disactivated.\n\033[93mTip: \033[0mIf you are did not want to saw these notifications, turn off NOTIFY property with using notify=False')
			else:
				return
		
	def notification(self, text):
			if not isinstance(text, str):
					try:
						text = str(text)
					except Exception as e:
						text = f"Cannot convert to string format: {e}"
						
			if self.activated:
				print(f'[\033[94mNOTIFICATION \033[0m{self.title} at {datetime.now().strftime("%D, %H:%M:%S")}\033[0m] \033[94m{text}\033[0m')
				if self.logging:
					self._write_to_log(text, 'NOTIFICATION')
			elif self.notify:
				print(f'Notification from {self.title}: Tryed to output when disactivated.\n\033[93mTip: \033[0mIf you are did not want to saw these notifications, turn off NOTIFY property with using notify=False')
			else:
				return
		
	def cfg(self, activated=None, title='DEBUG', notify=True, logging=True):
		'''Configure existing category'''
		if activated is not None:
			self.activated = activated
			if self.activated is False:
				self.notify = notify
		elif title is not None:
			self.title = title
		elif logging is not None:
			self.logging = logging
			
		if self.title in self._category_store:
			self._category_store[self.title]['activated'] = self.activated
			self._category_store[self.title]["title"] = self.title
			self._category_store[self.title]["logging"] = self.logging
		
		return self
			
	def __call__(self, text):
		if not isinstance(text, str):
					try:
						text = str(text)
					except Exception as e:
						text = f"Cannot convert to string format: {e}"
		self.info(text)