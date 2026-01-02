from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_micro.database.sqlite.ModuloSQLite import AbstractSqlite


class DatabaseCache(AbstractSqlite):
	
	# costruttore
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	
	# metodi
	def schema(self):
		sql="""
CREATE TABLE tb_cache(
	id						INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	type					TEXT NOT NULL,
	key						TEXT NULL,
	valore					TEXT NOT NULL,
	data_insert				TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX IX_tb_cache__type_key ON tb_cache(type,key);

"""

		return sql
	
	def insertBasicTables(self):
		return
	
	
	#############################################################################################################################
	def select_cache_valore_by_entries(self,tipo,chiave):
		results=self.select_cache_by_entries(tipo, chiave)
		if results is None:
			return None
		return results[0]['valore']
	
	def select_cache_by_entries(self,tipo,chiave):
		with self.__query_cache_by_entries(tipo, chiave,False) as cursoreDb:
			results=cursoreDb.fetchall()
		if len(results)==0:
			return None
		return results
	
	def count_cache_by_entries(self,tipo,chiave)->int:
		cursoreDb=self.__query_cache_by_entries(tipo, chiave,True)
		return self.count(cursoreDb)
	
	def __query_cache_by_entries(self,tipo,chiave,isCount):
		add_chiave=ModuloStringhe.isEmpty(chiave) is False
		sql="SELECT "+("COUNT(*) AS conta" if isCount is True else "*")+"""
FROM tb_cache
WHERE type=:tipo
"""+("AND key=:chiave" if add_chiave is True else "")+"""
;
"""
		params={'tipo':tipo}
		if add_chiave is True:
			params['chiave']=chiave
		
		cursoreDb=self.initCursor()
		cursoreDb.execute(sql,params)
		return cursoreDb
	
	def insert_cache(self,tipo,chiave,valore):
		sql="""
INSERT INTO tb_cache(
type,key,valore,data_insert
) VALUES (
:tipo,:chiave,:valore,"""+self.DATE_TIME_NOW+"""
);
"""
		cursoreDb=self.initCursor()
		cursoreDb.execute(sql,{
			'tipo':tipo,'chiave':chiave,'valore':valore
		})
		return cursoreDb
	
	def update_cache_valore(self,tipo,chiave,valore):
		sql="""
UPDATE tb_cache
SET valore=:valore,data_insert="""+self.DATE_TIME_NOW+"""
WHERE type=:tipo AND key=:chiave
;
"""
		cursoreDb=self.initCursor()
		cursoreDb.execute(sql,{
			'valore':valore,'tipo':tipo,'chiave':chiave
		})
		return cursoreDb
	
