from modulitiz_nano.exceptions.ExceptionBase import ExceptionBase


class ExceptionTooManyLogins(ExceptionBase):
	
	def __init__(self,*args):
		super().__init__(*args)
