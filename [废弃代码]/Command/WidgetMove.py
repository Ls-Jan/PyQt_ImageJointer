

__version__='1.0.0'
__author__='Ls_Jan'
__all__=['WidgetMove']

from PyQt5.QtWidgets import QUndoCommand,QWidget,QBoxLayout

class WidgetMove(QUndoCommand):
	'''
		控件移动命令，将控件移动到盒布局的指定位置，同时具有可见恢复功能
	'''
	def __init__(self,wid:QWidget,index:int,box:QBoxLayout=None,visible:bool=True):
		'''
			wid为所需移动的控件，该控件要么不在布局中，要么只能在盒布局中；
			box为目标布局，会将wid移动至box布局中，如果为None则在wid所在的盒布局内移动；
			index为目标位置，会将wid移动到box布局的指定位置，如果为None则将wid移出布局；
			visible决定可见状态；

			补充：
				当在同个盒布局中移动位置时，会自动调整插入位置，也就是调用方只需关心插入点即可。
				例如[A,<B>,C,D,E]，将B移动到3位置，会变为[A,C,D,<B>,E]
		'''
		super().__init__()
		currBox=self.__Get_ParentLayout(wid)
		nextBox=box
		if(index==None):
			nextBox=None
		elif(box==None):
			nextBox=currBox
		self.__wid=wid
		self.__currBox=currBox
		self.__nextBox=nextBox
		self.__currIndex=currBox.indexOf(wid) if currBox else 0
		self.__nextIndex=index
		self.__currVisible=wid.isVisible()
		self.__nextVisible=visible
	@staticmethod
	def __Get_ParentLayout(wid:QWidget):
		'''
			返回指定控件的父控件的布局，
			父控件不存在、布局不存在、布局不是QBoxLayout，均返回None
		'''
		parent=wid.parentWidget()
		box=parent.layout() if parent else None
		return box if isinstance(box,QBoxLayout) else None
	def redo(self):
		currBox=self.__currBox
		nextBox=self.__nextBox
		currIndex=self.__currIndex
		nextIndex=self.__nextIndex
		wid=self.__wid
		if(currBox!=None):
			if(currBox==nextBox and currIndex==nextIndex):
				return
			currBox.removeWidget(wid)
		if(nextBox!=None):
			index=nextIndex
			if(currBox==nextBox and currIndex<index):
				index-=1
			nextBox.insertWidget(index,wid)
		wid.setVisible(self.__nextVisible)
	def undo(self):
		currBox=self.__currBox
		nextBox=self.__nextBox
		currIndex=self.__currIndex
		nextIndex=self.__nextIndex
		wid=self.__wid
		if(nextBox!=None):
			if(currBox==nextBox and currIndex==nextIndex):
				return
			nextBox.removeWidget(wid)
		if(currBox!=None):
			index=currIndex
			if(currBox==nextBox and nextIndex<index):
				index-=1
			currBox.insertWidget(index,wid)
		wid.setVisible(self.__currVisible)



