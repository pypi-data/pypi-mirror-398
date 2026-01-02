import threading
from abc import ABC

from modulitiz_nano.files.ModuloLogging import ModuloLogging


class AbstractDatabaseService(ABC):
	
	def __init__(self,logger:ModuloLogging):
		self._logger=logger
		self.lock=threading.Lock()
		
		self.database=None
