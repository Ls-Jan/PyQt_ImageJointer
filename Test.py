
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from XJ.Structs.XJ_MouseStatus import XJ_MouseStatus

class Box(QWidget):
	'''
		图片显示，
		能将图片以行或列的方式进行显示
	'''
	def __init__(self,dire:QBoxLayout.Direction=QBoxLayout.Direction.TopToBottom):
		super().__init__()
		self.setAcceptDrops(True)
	def dragEnterEvent(self,event):
		mData=event.mimeData()
		if(mData.hasImage()):
			img=mData.imageData()
			print(img)
		elif(mData.hasUrls()):
			urls=mData.urls()
			print(urls)
		else:
			# print(">>>>>",mData.text())
			pass
			# return
		event.acceptProposedAction()
	# def dragMoveEvent(self,event):
	# def dropEvent(self,event):


class Test(QLabel):
	def __init__(self):
		super().__init__()
		self.__ms=XJ_MouseStatus(self)
	def mousePressEvent(self,event):
		self.__ms.Opt_Update(event)
		# print(event)
	def mouseMoveEvent(self,event):
		self.__ms.Opt_Update(event)
		if(self.__ms.Get_HasMoved()):
			print("!!!")

if True:
	app=QApplication([])

	# win=Box()
	win=Test()
	win.show()
	win.resize(640,480)

	app.exec()


