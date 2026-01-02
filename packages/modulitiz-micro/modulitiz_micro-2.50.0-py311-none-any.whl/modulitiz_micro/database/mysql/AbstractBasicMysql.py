from abc import abstractmethod

from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_micro.database.mysql.ModuloMysql import ModuloMysql


class AbstractBasicMysql(ModuloMysql):
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	
	def initDdlBasicTables(self):
		if not self.isDbNew:
			return
		sqlStr=ModuloStringhe.normalizzaEol(self.schemaBasicTables())
		for results in self.executeScript(sqlStr):
			yield results
		sqlInsertBasicTables=self.insertBasicTables()
		if not ModuloStringhe.isEmpty(sqlInsertBasicTables):
			sqlInsertBasicTables=ModuloStringhe.normalizzaEol(sqlInsertBasicTables)
			for results in self.executeScript(sqlInsertBasicTables):
				yield results
		self.commit()
	
	def schemaBasicTables(self):
		return """

CREATE TABLE tb_params(
	id						INT UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
	type1					CHAR(30) NOT NULL,
	key1					CHAR(30) NOT NULL,
	desc1					CHAR(100) NOT NULL,
	enabled					BOOLEAN NOT NULL,
	lang_code				CHAR(2) NULL,
	data_insert				DATETIME NOT NULL
)"""+self.TABLE_OPTIONS+""";
CREATE UNIQUE INDEX PARAMS__UK1 ON tb_params(type1,key1,lang_code);

"""
	
	@abstractmethod
	def insertBasicTables(self):
		"""
		Inserire le istruzioni sql che vanno eseguite alla fine di tutto
		"""
	
	
	
	#############################################################################################################################
	#############################################################################################################################
	#############################################################################################################################
	def selectParamDescByEntries(self,paramType:str,paramKey:str|None)->str|None:
		cursoreDb=self.selectParamByEntries(paramType, paramKey, None, True)
		results=self.fetchAll(cursoreDb)
		if len(results)==0:
			return None
		result=results[0]
		return result['desc1']
	
	def selectParamByEntries(self,paramType:str,paramKey:str|None,langCode:str|None,enabled:bool|None):
		addParamKey=ModuloStringhe.isEmpty(paramKey) is False
		addLangCode=ModuloStringhe.isEmpty(langCode) is False
		addEnabled=enabled is not None
		
		sql="""
SELECT *
FROM tb_params
WHERE type1=%(paramType)s
"""+("AND key1=%(paramKey)s" if addParamKey is True else "")+"""
"""+("AND langCode=%(langCode)s" if addLangCode is True else "")+"""
"""+("AND enabled=%(enabled)s" if addEnabled is True else "")+"""
;
"""
		params= {'paramType': paramType}
		if addParamKey is True:
			params['paramKey']=paramKey
		if addLangCode is True:
			params['langCode']=langCode
		if addEnabled is True:
			params['enabled']=enabled
		
		cursoreDb=self.initCursor()
		with self.lock:
			cursoreDb.execute(sql,params)
		return cursoreDb
	
	
	def updateParamDesc(self,paramType:str,paramKey:str|None,newDesc:str|None):
		addParamKey=ModuloStringhe.isEmpty(paramKey) is False
		addNewDesc=ModuloStringhe.isEmpty(newDesc) is False
		
		sqlSet=[]
		if addNewDesc is True:
			sqlSet.append("desc1=%(newDesc)s")
		sqlSet=", ".join(sqlSet)
		
		sql="""
UPDATE tb_params
SET """+sqlSet+"""
WHERE type1=%(paramType)s
"""+("AND key1=%(paramKey)s" if addParamKey is True else "")+"""
;
"""
		params={}
		if addNewDesc is True:
			params['newDesc']=newDesc
		params['paramType']=paramType
		if addParamKey is True:
			params['paramKey']=paramKey
		cursoreDb=self.initCursor()
		with self.lock:
			cursoreDb.execute(sql,params)
		return cursoreDb
	
