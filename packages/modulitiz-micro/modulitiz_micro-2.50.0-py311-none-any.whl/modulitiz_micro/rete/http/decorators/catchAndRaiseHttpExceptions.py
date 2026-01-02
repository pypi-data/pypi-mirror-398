import socket
from functools import wraps
from urllib.error import URLError

import requests

from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric


def catchAndRaiseHttpExceptions(funzione):
	"""
	Cattura tutte le eccezioni http di vario tipo e rilancia un'eccezione custom
	"""
	
	@wraps(funzione)
	def wrapped(*args,**kwargs):
		try:
			return funzione(*args,**kwargs)
		except (ConnectionError,TimeoutError,URLError,
				requests.exceptions.ConnectionError,socket.gaierror) as ex:
			raise ExceptionHttpGeneric() from ex
	return wrapped
