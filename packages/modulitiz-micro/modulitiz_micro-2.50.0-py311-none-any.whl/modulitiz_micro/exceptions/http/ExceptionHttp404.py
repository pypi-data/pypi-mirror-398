from modulitiz_micro.exceptions.http.ExceptionHttp import ExceptionHttp


class ExceptionHttp404(ExceptionHttp):
	
	def __init__(self):
		super().__init__(404)
