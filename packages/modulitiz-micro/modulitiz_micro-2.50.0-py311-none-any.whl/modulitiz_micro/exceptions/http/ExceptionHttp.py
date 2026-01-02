from modulitiz_nano.exceptions.ExceptionBase import ExceptionBase


class ExceptionHttp(ExceptionBase):
	
	def __init__(self,httpCode:int|None,*args):
		super().__init__(*args)
		self.httpCode=httpCode
