from modulitiz_nano.exceptions.ExceptionNoData import ExceptionNoData


class ExceptionDbNoData(ExceptionNoData):
	
	def __init__(self,*args):
		super().__init__(*args)
