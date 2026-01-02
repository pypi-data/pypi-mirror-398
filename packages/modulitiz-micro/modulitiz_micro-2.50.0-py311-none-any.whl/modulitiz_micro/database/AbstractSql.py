import threading
from abc import ABC

from modulitiz_nano.ModuloStringhe import ModuloStringhe


class AbstractSql(ABC):
	def __init__(self):
		self.connDb=None
		self.lock=threading.Lock()
	
	def commit(self):
		"""
		Use to make modifications permanents.
		"""
		with self.lock:
			self.commitNoLock()
	
	def commitNoLock(self):
		"""
		Use only if lock is made externally.
		"""
		self.connDb.commit()
	
	def rollback(self):
		"""
		Undo last uncommitted operations.
		"""
		with self.lock:
			self.connDb.rollback()
	
	def initCursor(self):
		"""
		Creates cursor objects, it's needed to read/write database.
		"""
		with self.lock:
			cursoreDb=self.connDb.cursor()
		return cursoreDb
	
	def fetchOne(self,cursoreDb):
		"""
		Retrieve first row of query
		"""
		with cursoreDb:
			with self.lock:
				result=cursoreDb.fetchone()
		if not result:
			return None
		return result[0]
	
	def count(self,cursoreDb)->int:
		with cursoreDb:
			with self.lock:
				result=cursoreDb.fetchone()
		if not result:
			return 0
		return result[0]
	
	def close(self):
		with self.lock:
			if self.connDb is not None:
				self.connDb.close()
				self.connDb=None
	
	@staticmethod
	def ifEmptyThenNull(testo:str|None)->str|None:
		if ModuloStringhe.isEmpty(testo) or testo=="NULL":
			return None
		return testo
