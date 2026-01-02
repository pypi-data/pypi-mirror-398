import threading
import time
from typing import Callable

from modulitiz_nano.sistema.ModuloSystem import ModuloSystem

if ModuloSystem.isWindows():
	from pynput.keyboard import Key, Listener


class ModuloKeylogger(object):
	IS_AVAILABLE=ModuloSystem.isWindows()
	EXIT_KEY=None
	EXIT_KEY_2=None
	if IS_AVAILABLE:
		EXIT_KEY=Key.pause
		EXIT_KEY_2=Key.menu
	
	__lastKeyPressed=None
	__numKeyPressed=0
	__callbackOnKeyPress=None
	
	@staticmethod
	def getTasto(key):
		try:
			tasto=key.char
		except AttributeError:
			tasto=key
		if tasto is None:
			return str(key.vk)
		return str(tasto).replace("Key.","")
	
	@classmethod
	def start(cls,callbackOnKeyPress:Callable,runNewProcess:bool):
		"""
		Se la liberia non e' disponibile non verra' caricata, ad esempio se usi la cli
		"""
		# controllo se e' disponibile
		if not cls.IS_AVAILABLE:
			return
		# lancio gli handler
		cls.__callbackOnKeyPress=callbackOnKeyPress
		if runNewProcess:
			processo=threading.Thread(target=cls.__tStartListening,args=(cls.__onKeyPressHandler,cls.__onKeyReleaseHandler),daemon=True)
			processo.start()
			return
		cls.__startListening(cls.__onKeyPressHandler,cls.__onKeyReleaseHandler)
	
	@staticmethod
	def __startListening(onKeyPressHandler,onKeyReleaseHandler):
		with Listener(on_press=onKeyPressHandler,on_release=onKeyReleaseHandler) as listener:
			listener.join()
	@classmethod
	def __tStartListening(cls,onKeyPressHandler,onKeyReleaseHandler):
		cls.__startListening(onKeyPressHandler,onKeyReleaseHandler)
		while True:
			time.sleep(1)
	
	#
	#key handlers
	#
	@classmethod
	def __onKeyPressHandler(cls,key):
		if cls.__lastKeyPressed==key:
			return
		cls.__callbackOnKeyPress(key,cls.__numKeyPressed)
		
		cls.__lastKeyPressed=key
		cls.__numKeyPressed+=1
	@classmethod
	def __onKeyReleaseHandler(cls,key):
		cls.__lastKeyPressed=None
		cls.__numKeyPressed-=1
