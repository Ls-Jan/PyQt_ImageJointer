__version__='1.0.0'
__author__='Ls_Jan'
__all__=['XJQ_Main']

from PyQt5.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QApplication,QMenu,QMessageBox,QFileDialog
from PyQt5.QtCore import QSize,Qt
from PyQt5.QtGui import QMovie,QPixmap,QCursor

from XJ.Widgets.XJQ_GarbageBin import XJQ_GarbageBin
from XJ.Widgets.XJQ_ClipboardDrag import XJQ_ClipboardDrag
from XJ.Widgets.XJQ_ScreenCapture import XJQ_ScreenCapture
from XJQ_PictJointer import XJQ_PictJointer
import os

class XJQ_Main(QWidget):
	def __init__(self):
		super().__init__()
		mv=QMovie('./加载动画-1.gif')
		mv.setScaledSize(QSize(64,64))
		pixFail=QPixmap('./图标-文件丢失.png').scaled(64,64)
		pixArrow=QPixmap('./箭头-上.png')
		jtr=XJQ_PictJointer(mv,pixFail,pixArrow)
		gb=XJQ_GarbageBin()
		sc=XJQ_ScreenCapture()
		cd=XJQ_ClipboardDrag()
		menu=QMenu()
		sc.captured.connect(lambda pix:jtr.Opt_InsertPict(-1,None,pix))#可以在此处进行截图的本地化保存，只不过单纯懒得搞，直接默认用hash值
		gb.dropped.connect(lambda data:jtr.Opt_RemovePict([],True))
		menuActions={
			'save':menu.addAction('保存拼接结果',self.Opt_Save),
			'remove':menu.addAction('移除选中的图片',lambda:jtr.Opt_RemovePict([],True)),
			'direction':menu.addAction('横向排列',lambda:jtr.Set_Direction(not jtr.Get_Direction())),
			}
		hbox=QHBoxLayout(self)
		vbox=QVBoxLayout()
		vbox.addWidget(cd)
		vbox.addWidget(sc)
		vbox.addWidget(gb)
		vbox.addStretch(1)
		hbox.addLayout(vbox)
		hbox.addWidget(jtr,1)

		self.__jtr=jtr
		self.__menu=menu
		self.__menuActions=menuActions
		jtr.Set_AntiJitter(40)
	def mousePressEvent(self,event):
		if(event.button()==Qt.MouseButton.RightButton):
			self.__menu.popup(QCursor.pos())
			self.__menuActions['save'].setDisabled(self.__jtr.Get_PictCount()==0)
			self.__menuActions['direction'].setText(f'{"纵向" if self.__jtr.Get_Direction() else "横向"}排列')
	def Opt_Save(self,path:str=None):
		'''
			保存拼接结果
		'''
		if(path==None):
			path=QFileDialog.getSaveFileName(None,'','./','*.png')[0]
		if(path):
			pix=self.__jtr.Get_JointPix()
			if(pix.save(path)):
				mbox=QMessageBox(QMessageBox.Icon.NoIcon,"保存成功","接下来")
				mbox.addButton("打开图片",QMessageBox.ButtonRole.ActionRole)
				mbox.addButton("打开路径",QMessageBox.ButtonRole.ActionRole)
				mbox.addButton("取消",QMessageBox.ButtonRole.RejectRole)
				rst=mbox.exec()
				path=path.replace('/',os.path.sep)#把win“最喜欢”的反斜杠换上，要不然explorer无法顺利打开路径
				if(rst==0):
					os.system(f'explorer {path}')
				elif(rst==1):
					os.system(f'explorer {os.path.split(path)[0]}')


if True:
	app=QApplication([])
	win=XJQ_Main()
	win.resize(600,800)
	win.show()
	app.exec()




