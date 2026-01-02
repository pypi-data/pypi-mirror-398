from modulitiz_nano.exceptions.ExceptionBase import ExceptionBase


class ExceptionKeyLogger(ExceptionBase):
	
	def __init__(self):
		super().__init__("Ricevuto comando da tastiera di chiusura programma")
