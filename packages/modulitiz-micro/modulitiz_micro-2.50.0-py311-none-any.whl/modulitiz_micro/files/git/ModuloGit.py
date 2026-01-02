import git

from modulitiz_micro.files.git.decorators.catchAndRaiseGitExceptions import catchAndRaiseGitExceptions


class ModuloGit(object):
	def __init__(self, repoPath:str):
		self.inner=git.Repo(repoPath)
	
	@catchAndRaiseGitExceptions
	def getWorkingCopyRevision(self)->str:
		return self.inner.head.object.hexsha
	
	@catchAndRaiseGitExceptions
	def getRemoteRevision(self)->str:
		return self.inner.remotes[0].fetch()[0].ref.object.hexsha
	
	@catchAndRaiseGitExceptions
	def addFile(self,filenamePath:str):
		self.inner.index.add(filenamePath)
	
	@catchAndRaiseGitExceptions
	def removeFile(self,filenamePath:str):
		self.inner.index.remove(filenamePath,working_tree=True)
	
	@catchAndRaiseGitExceptions
	def update(self)->str:
		return self.inner.remotes[0].pull()[0].ref.object.hexsha
