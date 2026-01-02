from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric


class ExceptionHttpRetriesExceeded(ExceptionHttpGeneric):
	
	def __init__(self):
		super().__init__()
