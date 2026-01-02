from modulitiz_nano.exceptions.ExceptionBase import ExceptionBase


class ExceptionGit(ExceptionBase):
	
	def __init__(self,*args):
		super().__init__(*args)
