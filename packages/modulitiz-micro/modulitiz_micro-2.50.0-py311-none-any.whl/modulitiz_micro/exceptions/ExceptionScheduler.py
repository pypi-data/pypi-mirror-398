from modulitiz_nano.exceptions.ExceptionBase import ExceptionBase


class ExceptionScheduler(ExceptionBase):
	
	def __init__(self,*args):
		super().__init__(*args)
