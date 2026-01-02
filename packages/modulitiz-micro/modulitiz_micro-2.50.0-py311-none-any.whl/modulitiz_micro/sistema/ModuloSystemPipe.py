import multiprocessing
import queue
import subprocess
import threading
import time

import psutil

from modulitiz_nano.files.ModuloLogging import ModuloLogging
from modulitiz_nano.multithread.ModuloThread import ModuloThread
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloSystemPipe(object):
	
	@classmethod
	def read(cls,logger: ModuloLogging,pipe: subprocess.Popen,timeout:int|float) -> str|None:
		event=threading.Event()
		q=multiprocessing.Queue()
		ModuloThread.startDaemon(logger,cls.__read,(pipe,q,event))
		
		output=""
		pauseInterval=0.1
		contaTimeout=0
		continua=True
		while continua:
			outputBefore=output
			try:
				output+=q.get_nowait()
			except queue.Empty:
				pass
			continua=(output=="" or output!=outputBefore)
			if continua:
				if output=="":
					contaTimeout+=pauseInterval
				else:
					contaTimeout=0
				time.sleep(pauseInterval)
			else:
				if contaTimeout<=timeout:
					time.sleep(pauseInterval)
					continua=True
					contaTimeout+=pauseInterval
		event.set()
		return output.rstrip()
	
	@staticmethod
	def __read(pipe: subprocess.Popen,q: multiprocessing.Queue,event: threading.Event):
		chunk=pipe.stdout.readline()
		while chunk:
			q.put_nowait(chunk.decode())
			if event.is_set():
				return
			chunk=pipe.stdout.readline()
	
	@staticmethod
	def closeAndCheck(process:psutil.Process|subprocess.Popen,alias:str,timeout:int,callbackError,callbackSuccess):
		ModuloSystem.sendCtrlcProcess(process.pid)
		try:
			exitCode=process.wait(timeout)
		except (psutil.TimeoutExpired,subprocess.TimeoutExpired):
			callbackError(alias+" non terminato correttamente nel tempo utile")
			return
		if exitCode is None or exitCode==0:
			callbackSuccess(alias+" terminato con successo")
			return
		callbackError(alias+" non terminato correttamente, esito=%s"%(exitCode,))
