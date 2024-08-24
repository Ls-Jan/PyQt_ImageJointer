
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *




class Test(QMainWindow):
	def __init__(self):
		super().__init__()
		mu=QMenu("A")
		mb=QMenuBar()
		mb.addMenu(mu)
		mb.addMenu(QMenu("A"))
		mb.addMenu(QMenu("B"))
		mb.addMenu(QMenu("C"))
		self.setMenuBar(mb)
		mb.show()

if True:
	app=QApplication([])

	t=QLabel()
	t.show()
	t.resize(640,480)

	pix=QPixmap(640,480)
	pix.fill(Qt.GlobalColor.transparent)
	target=QRect(128,128,128,128)
	target2=QRect(192,192,128,128)
	ptr=QPainter(pix)
	# ptr.setViewport(QRect(100,100,100,100))
	# ptr.setWindow(QRect(100,100,100,100))
	ptr.fillRect(target,QColor(0,255,255,128))
	ptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
	# ptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOut)
	ptr.fillRect(target2,QColor(0,0,255))
	# ptr.fillRect(target2,QColor(0,0,255,128))
	# ptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_Xor)
	# ptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
	# ptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
	# ptr.fillRect(0,0,pix.width(),pix.height(),QColor(255,0,0,192))
	# ptr.
	ptr.end()
	t.setPixmap(pix)
	app.exec()
	exit()



	lst=[
		QPixmap('./XJQ_PictJointer/加载动画-1.gif'),
		QPixmap('./XJQ_PictJointer/图标-文件丢失.png'),
		QPixmap('./XJQ_PictJointer/箭头-上.png'),
	]
	
	horizontal=False
	align=1

	mW,mH,tW,tH=0,0,0,0
	for pix in lst:
		w,h=pix.width(),pix.height()
		mW=max(mW,w)
		mH=max(mH,h)
		tW+=w
		tH+=h

	rst=QPixmap(tW,mH) if horizontal else QPixmap(mW,tH)
	rst.fill(Qt.GlobalColor.transparent)
	ptr=QPainter(rst)
	x,y=0,0
	for pix in lst:
		w,h=pix.width(),pix.height()
		px,py=x,y
		if(horizontal):
			if(align>0):
				py+=(mH-h)>>(2-align)
			x+=w
		else:
			if(align>0):
				px+=(mW-w)>>(2-align)
			y+=h
		ptr.drawPixmap(px,py,pix)
	ptr.end()
	t.setPixmap(rst)

	app.exec()


