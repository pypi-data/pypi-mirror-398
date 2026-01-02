class HttpResponseBean(object):
	def __init__(self,status:int,responseBody:bytes,responseHeaders:dict):
		self.status=status
		self.responseBody=responseBody
		self.responseHeaders=responseHeaders
