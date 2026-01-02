from functools import wraps

from cachetools import TTLCache
from cachetools import cached

from modulitiz_nano.ModuloNumeri import ModuloNumeri


def cacheRam(minsBeforeExpiry: int|float|None):
	"""
	Usare questo decorator per mettere in cache delle informazioni.
	Alla base usa una libreria di terze parti.
	:param minsBeforeExpiry: se null mantiene i dati in memoria per 1 giorno
	"""
	
	__secsBeforeExpiry=24*3600 if minsBeforeExpiry is None else ModuloNumeri.decimalNumbersTruncate(minsBeforeExpiry*60,2)
	__cache=cached(TTLCache(20,__secsBeforeExpiry))
	
	def decorator(funzione):
		__funzione=__cache(funzione)
		
		@wraps(funzione)
		def wrapped(*args,**kwargs):
			return __funzione(*args,**kwargs)
		return wrapped
	return decorator
