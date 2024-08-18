

__version__='1.0.0'
__author__='Ls_Jan'
__all__=['Move']

from PyQt5.QtWidgets import QUndoCommand,QWidget,QBoxLayout

class Move(QUndoCommand):
	'''
		控件移动命令，将控件移动到盒布局的指定位置，同时具有可见恢复功能
	'''
	def __init__(self,wid:QWidget,index:int,box:QBoxLayout=None,visible:bool=True):
		'''
			wid为所需移动的控件，该控件要么不在布局中，要么只能在盒布局中；
			box为目标布局，会将wid移动至box布局中，如果为None则在wid所在的盒布局内移动；
			index为目标位置，会将wid移动到box布局的指定位置，如果为None则将wid移出布局；
			visible决定可见状态；
		'''
		super().__init__()
		currBox=self.__Get_ParentLayout()
		nextBox=box
		if(index==None):
			nextBox=None
		elif(box==None):
			nextBox=currBox
		self.__wid=wid
		self.__currBox=currBox
		self.__nextBox=nextBox
		self.__currIndex=currBox.indexOf(wid) if currBox else None
		self.__nextIndex=index
		self.__currVisible=wid.isVisible()
		self.__nextVisible=visible
	def __Get_ParentLayout(self):
		'''
			返回父控件的布局，
			父控件不存在、布局不存在、布局不是QBoxLayout，均返回None
		'''
		parent=self.__wid.parentWidget()
		box=parent.layout() if parent else None
		return box if isinstance(box,QBoxLayout) else None
	def redo(self):
		currBox=self.__currBox
		nextBox=self.__nextBox
		wid=self.__wid
		if(currBox):
			currBox.removeWidget(wid)
		if(nextBox):
			nextBox.insertWidget(self.__nextIndex,wid)
		wid.setVisible(self.__nextVisible)
	def undo(self):
		currBox=self.__currBox
		nextBox=self.__nextBox
		wid=self.__wid
		if(nextBox):
			nextBox.removeWidget(wid)
		if(currBox):
			currBox.insertWidget(self.__currIndex,wid)
		wid.setVisible(self.__currVisible)



