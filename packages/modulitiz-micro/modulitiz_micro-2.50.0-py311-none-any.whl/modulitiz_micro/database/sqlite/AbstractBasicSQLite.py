from abc import abstractmethod

from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_micro.database.sqlite.ModuloSQLite import AbstractSqlite


class AbstractBasicSqlite(AbstractSqlite):
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		if not self.isDbNew:
			return
		sql_str=ModuloStringhe.normalizzaEol(self.schemaBasicTables())
		with self.initCursor() as cursoreDb:
			with self.lock:
				cursoreDb.executescript(sql_str)
			sql_insertBasicTables=self.insertBasicTables()
			if not ModuloStringhe.isEmpty(sql_insertBasicTables):
				sql_insertBasicTables=ModuloStringhe.normalizzaEol(sql_insertBasicTables)
				with self.lock:
					cursoreDb.executescript(sql_insertBasicTables)
		self.commit()
	
	@abstractmethod
	def insertBasicTables(self):
		"""
		Inserire le istruzioni sql che vanno eseguite alla fine di tutto
		"""
	
	def schemaBasicTables(self):
		return """

CREATE TABLE tb_params(
	id						INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	type					TEXT NOT NULL,
	key						TEXT NULL,
	desc					TEXT NOT NULL,
	enabled					INTEGER NOT NULL,
	lang_code				TEXT NULL,
	data_insert				TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX PARAMS__UK1 ON tb_params(
	type,
	IFNULL(key, 0),
	IFNULL(lang_code, 0)
);

"""
	
	
	#############################################################################################################################
	#############################################################################################################################
	#############################################################################################################################
	def selectParamDescByEntries(self,paramType,paramKey)->str|None:
		with self.selectParamByEntries(paramType, paramKey, None, True) as cursoreDb:
			results=cursoreDb.fetchall()
		if len(results)==0:
			return None
		return results[0]['desc']
	
	def selectParamByEntries(self,paramType,paramKey,langCode,enabled):
		addParamKey=ModuloStringhe.isEmpty(paramKey) is False
		addLangCode=ModuloStringhe.isEmpty(langCode) is False
		addEnabled=ModuloStringhe.isEmpty(enabled) is False
		
		sql="""
SELECT *
FROM tb_params
WHERE type=:paramType
"""+("AND key=:paramKey" if addParamKey is True else "")+"""
"""+("AND langCode=:langCode" if addLangCode is True else "")+"""
"""+("AND enabled=:enabled" if addEnabled is True else "")+"""
;
"""
		params={'paramType':paramType}
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
	
	
	def updateParamDesc(self,paramType,paramKey,newDesc):
		addParamKey=ModuloStringhe.isEmpty(paramKey) is False
		addNewDesc=ModuloStringhe.isEmpty(newDesc) is False
		
		sql_set=[]
		if addNewDesc is True:
			sql_set.append("desc=:newDesc")
		sql_set=", ".join(sql_set)
		
		sql="""
UPDATE tb_params
SET """+sql_set+"""
WHERE type=:paramType
"""+("AND key=:paramKey" if addParamKey is True else "")+"""
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
	
