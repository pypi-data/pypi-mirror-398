import mysql.connector

class ExceptionMysqlOffline(mysql.connector.InterfaceError):
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
