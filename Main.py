

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from XJ.Functions.GetRealPath import GetRealPath
from XJ.Widgets.XJQ_ClipboardDrag import XJQ_ClipboardDrag
from XJ.Widgets.XJQ_GarbageBin import XJQ_GarbageBin
# from XJQ_PictJointer import XJQ_PictJointer

class Main(QWidget):
	def __init__(self):
		super().__init__()
		hbox=QHBoxLayout(self)
		vboxL=QVBoxLayout()
		vboxL.addWidget(XJQ_ClipboardDrag(None,QSize(96,96)))
		vboxL.addWidget(XJQ_GarbageBin(None,QSize(96,96)))
		vboxL.addStretch(1)
		hbox.addLayout(vboxL)
		# hbox.addWidget(XJQ_PictJointer(),1)


if True:
	app=QApplication([])
	cb=QApplication.clipboard()
	# mData=cb.mimeData()
	mData=QMimeData()
	im=QImage('./XJQ_PictJointer/空白文件.ico')
	mData.setImageData(im)
	cb.setMimeData(mData)

	print(im.size())
	print(cb.mimeData().imageData().size())
	exit()
	# win=Main()
	# win.show()
	# win.resize(640,480)
	app.exec()



