from typing import Optional

from mysql.connector import FieldType
from mysql.connector.conversion import MySQLConverter
from mysql.connector.types import DescriptionType
from mysql.connector.types import MySQLConvertibleType
from mysql.connector.types import MySQLProducedType
from mysql.connector.types import PythonProducedType


class MysqlCommonConverter(MySQLConverter):
	def __init__(self,charset: str|None = None,
			use_unicode: bool = True,
			str_fallback: bool = False):
		super().__init__(charset,use_unicode,str_fallback)
	
	def to_mysql(self,value) -> MySQLProducedType:
		value=self.__to_mysql(value)
		# default behavior
		return super().to_mysql(value)
	
	@staticmethod
	def __to_mysql(value):
		"""
		Gestione custom, ad esempio per IntEnum e StrEnum
		"""
		if value.__class__ in MySQLConvertibleType.__args__:
			return value
		# inizio gestione custom
		if isinstance(value,int):
			typePrimitive=int
		elif isinstance(value,str):
			typePrimitive=str
		else:
			return value
		value.__class__.__name__=typePrimitive.__name__
		return value
	
	def to_python(
			self,
			vtype: DescriptionType,
			value: Optional[bytes],
	) -> PythonProducedType:
		if vtype[1] == FieldType.BIT:
			return value==b'\x01'
		# default behavior
		return super().to_python(vtype, value)
