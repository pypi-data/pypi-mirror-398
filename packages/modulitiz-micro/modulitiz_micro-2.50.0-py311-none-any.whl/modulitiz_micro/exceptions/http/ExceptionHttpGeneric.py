from modulitiz_micro.exceptions.http.ExceptionHttp import ExceptionHttp


class ExceptionHttpGeneric(ExceptionHttp):
	
	def __init__(self):
		super().__init__(None)
