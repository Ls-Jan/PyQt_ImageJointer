

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from XJQ_PictJointer import XJQ_PictJointer
from XJQ_PictJointer import UrlPict
from XJ.Functions.GetRealPath import GetRealPath

if True:
	app=QApplication([])
	dire = QBoxLayout.Direction.TopToBottom
	dire = QBoxLayout.Direction.LeftToRight
	dire = QBoxLayout.Direction.BottomToTop
	dire = QBoxLayout.Direction.RightToLeft

	win=XJQ_PictJointer(dire)
	win.resize(600,400)
	win.show()

	# url=QUrl('https://pic.lzacg.org/i/2024/02/01/65bbbd329bd2a.webp')
	# url=QUrl('C:/Users/Administrator/Desktop/XJQ_ImageJointer/XJQ_ImageJointer/A%23B%25C&D.png')
	url=QUrl('C:/Users/Administrator/Desktop/XJQ_ImageJointer/XJQ_ImageJointer/A#B%C&D.png')
	# url=QUrl('C:/Users/Administrator/Desktop/XJQ_ImageJointer/XJQ_ImageJointer/箭头-010.png')
	# url=QUrl('F:/Github_Repository/Python/XJ_Python/XJ/Scripts/#爱给网素材#/95783/icon/35毫米胶片.png')
	# QByteArray(url.url().encode()).toPercentEncoding()
	# print(QByteArray(url.url().encode()).toPercentEncoding())
	# b=QByteArray(url.url().encode()).toPercentEncoding().data()
	# print(QUrl(b.decode()))
	# url=QUrl(url.url().replace('#','%23'))
	# exit()

	# url=QUrl('file:///F:/Github_Repository/Python/XJ_Python/XJ/Widgets/XJQ_LoadingAnimation/LoadingGIF.gif')
	# url=QUrl('file:///F:/Github_Repository/Python/XJ_Python/XJ/Widgets/XJQ_LoadingAnimation/XJQ_LoadingAnimation.py')
	# url.setScheme('file')
	# print(url.url())
	# if(os.path.exists(url.url())):
		# url=QUrl(f'file:///{url.url()}')




	mv=QMovie()
	mv.setFileName(GetRealPath('./加载动画-1.gif'))
	mv.start()
	pix=QPixmap(GetRealPath('./文件错误.png'))

	pm=PictManager(mv,pix)
	wid=pm.Opt_CreatePict(url)
	wid.resize(640,480)
	wid.show()
	# lb=QLabel()
	# lb.resize(500,500)
	# lb.show()

	# win=Box()
	# win.show()
	# win.resize(640,480)



	app.exec()
	exit()





class Box(QWidget):
	'''
		图片显示，
		能将图片以行或列的方式进行显示
	'''
	def __init__(self,dire:QBoxLayout.Direction=QBoxLayout.Direction.TopToBottom):
		super().__init__()
		self.setAcceptDrops(True)
		vbox=QVBoxLayout(self)
		vbox.addWidget(Pict(None))
		self.__vbox=vbox
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
	def dropEvent(self,event):
		mData=event.mimeData()
		if(mData.hasUrls()):
			url=mData.urls()[0]
			im=Pict(url)
			self.__vbox.removeItem(self.__vbox.itemAt(0))
			self.__vbox.addWidget(im)
		# for url in mData.urls():
		# 	Image(url)


