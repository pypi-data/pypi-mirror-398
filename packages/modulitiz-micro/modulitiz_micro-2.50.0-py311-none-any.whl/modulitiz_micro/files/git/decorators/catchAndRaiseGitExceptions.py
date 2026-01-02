from functools import wraps

from git import GitCommandError

from modulitiz_micro.files.git.exceptions.ExceptionGit import ExceptionGit


def catchAndRaiseGitExceptions(function):
	"""
	Cattura tutte le eccezioni git di vario tipo e rilancia un'eccezione custom
	"""
	
	@wraps(function)
	def wrapped(*args,**kwargs):
		try:
			return function(*args,**kwargs)
		except (GitCommandError,) as ex:
			raise ExceptionGit() from ex
	return wrapped
