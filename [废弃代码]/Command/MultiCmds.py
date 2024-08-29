

__version__='1.0.0'
__author__='Ls_Jan'
__all__=['MultiCmds']

from PyQt5.QtWidgets import QUndoCommand

class MultiCmds(QUndoCommand):
	'''
		复数命令整合为一条命令
	'''
	def __init__(self,*cmds:QUndoCommand):
		'''
			依次执行多条命令
		'''
		super().__init__()
		self.__cmds=cmds
	def redo(self):
		for cmd in self.__cmds:
			cmd.redo()
	def undo(self):
		for cmd in reversed(self.__cmds):
			cmd.undo()


