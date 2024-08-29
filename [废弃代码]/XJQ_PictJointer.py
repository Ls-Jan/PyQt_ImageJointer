
__version__='1.0.0'
__author__='Ls_Jan'
__all__=['XJQ_PictJointer']

from PyQt5.QtWidgets import QUndoStack,QWidget,QBoxLayout,QLabel
from PyQt5.QtCore import QUrl,QMimeData,Qt
from PyQt5.QtGui import QDrag,QPixmap,QMovie

from XJ.Deprecated.XJQ_PreviewMask.XJQ_SelectedPreviewMask import XJQ_SelectedPreviewMask
from XJ.Deprecated.XJQ_PreviewMask.XJQ_InsertPreviewMask import XJQ_InsertPreviewMask
from XJ.Deprecated.XJQ_UrlPict import XJQ_UrlPict
from XJ.Deprecated.XJQ_UrlPict import UrlPictConfig
from XJ.Structs.XJ_MouseStatus import XJ_MouseStatus
from XJ.Functions.GetRealPath import GetRealPath
from typing import Union

# from .Command import WidgetMove
# from .Command import MultiCmds
from Command import WidgetMove
from Command import MultiCmds

class XJQ_PictJointer(QWidget):
	'''
		图片拼接器。
		能将图片以行或列的方式进行显示。
		使用到的控件为XJQ_UrlPict。
		需额外使用QScrollArea之类的容器进行显示。

		没有做数据清理工作，程序使用一段时间后需要显式退出。
		做是可以做，略烦说实话，毕竟有撤回行为导致不少数据和控件不能直接删。
		懒了，摸了
	'''
	def __init__(self,config:UrlPictConfig=None):
		'''
			传入config，如果无则使用默认配置。
		'''
		super().__init__()
		box=QBoxLayout(QBoxLayout.Direction.TopToBottom,self)
		config=config if config else UrlPictConfig((64,64),QMovie(GetRealPath('./加载动画-1.gif')),QPixmap(GetRealPath('./图标-文件丢失.png')))
		mskSe=XJQ_SelectedPreviewMask(self)
		mskIn=XJQ_InsertPreviewMask(self)
		ms=XJ_MouseStatus(self)
		box.addStretch(1)#盒子必有一个空元素，其余元素均是控件
		ms.Set_AntiJitter(50)#防抖打高点，省的随随便便就被拖走
		mskIn.Set_DetectRadius(40)
		mskIn.Set_ValidDire(False,True)
		mskIn.Set_UpArrowPict(QPixmap(GetRealPath('./箭头-上.png')))
		mskIn.Set_IncludeLayout(box)
		mskIn.hide()
		mskSe.show()

		self.__mskIn=mskIn
		self.__mskSe=mskSe
		self.__stk=QUndoStack(self)
		self.__ms=ms
		self.__box=box
		self.__config=config
		self.setAcceptDrops(True)
	def dragEnterEvent(self,event):
		mData=event.mimeData()
		if(mData.hasImage() or mData.hasUrls()):
			self.__mskIn.show()
			self.__mskIn.update()
			event.acceptProposedAction()
	def dragLeaveEvent(self,event):
		self.__mskIn.hide()
	def dragMoveEvent(self,event):
		self.__mskIn.update()
	def dropEvent(self,event):
		layout,target,dire=self.__mskIn.Get_InsertPos()
		if(layout!=None and dire%5!=0):#不是0或5，确定插入数据。虽然dire有效时layout必然不为空，但还是小防一手
			mData=event.mimeData()
			insertIndex=layout.indexOf(target)+(0 if dire<5 else 1) if(target!=None) else 0
			if(self.__mskSe.Get_IsPressed()):#内部拖拽，移动控件
				lst=[]
				cmds=[]
				for wid in self.__mskSe.Get_SelectedWidgets():
					index=layout.indexOf(wid)
					if(index>=0):
						lst.append((index,wid))
				lst.sort(key=lambda item:item[0])
				for item in reversed(lst):
					index,wid=item
					cmds.append(WidgetMove(wid,insertIndex,layout))
					if(index<insertIndex):
						insertIndex-=1#不可能会出现小于0的情况
				self.__stk.push(MultiCmds(*cmds))
				self.__mskSe.Opt_Clear()
			else:#外部拖拽，创建控件
				cmds=[]
				if(mData.hasUrls()):
					for url in reversed(mData.urls()):
						pict=XJQ_UrlPict(self.__config,url)
						cmds.append(WidgetMove(pict,insertIndex,self.__box,True))
				elif(mData.hasImage()):

					img=mData.imageData()
					data=QByteArray()
					pix=QPixmap()
					print(img)
					pix.fromImage(img)
					pix.save(QBuffer(data),'png')

					pict=XJQ_UrlPict(self.__config,None,data)
					cmds.append(WidgetMove(pict,insertIndex,self.__box,True))
				if(cmds):
					self.__stk.push(MultiCmds(*cmds))
		self.__mskIn.hide()
	def mousePressEvent(self,event):
		self.__ms.Opt_Update(event)
		if(event.button()==Qt.LeftButton):
			self.__mskSe.Opt_Press(bool(event.modifiers() & Qt.Modifier.CTRL))
	def mouseMoveEvent(self,event):
		self.__ms.Opt_Update(event)
		self.__mskIn.update()
		lastPressedWid:QLabel=self.__mskSe.Get_LastPressedWidget()
		if(lastPressedWid!=None):
			self.__ms.Opt_Update(event)
			if(self.__ms.Get_HasMoved(True)):#发生拖拽，发送QDrag。事实上一旦调用了QDrag.exec，控件将不会再收到鼠标事件，对应的会收到拖拽事件
				self.__mskSe.Opt_Drag()
				urls=[]
				for wid in self.__mskSe.Get_SelectedWidgets():
					pict:XJQ_UrlPict=wid
					urls.append(QUrl(pict.Get_Url()))
				if(urls):
					dg=QDrag(self)
					mData=QMimeData()
					mData.setUrls(urls)
					dg.setPixmap(lastPressedWid.pixmap())
					dg.setMimeData(mData)
					dg.exec(Qt.MoveAction)
	def mouseReleaseEvent(self,event):
		self.__ms.Opt_Update(event)
		self.__mskSe.Opt_Release()
	def Set_Direction(self,horizontal:bool):
		'''
			设置排列方向以及对齐方向。
			如果horizontal为真则水平(左到右)排列，否则竖直(上到下)排列。
			调用后需要额外调用Set_Alignment以设置控件对齐方向。
		'''
		if(horizontal):
			self.__box.setDirection(QBoxLayout.Direction.LeftToRight)
			self.__mskIn.Set_ValidDire(True,False)
		else:
			self.__box.setDirection(QBoxLayout.Direction.TopToBottom)
			self.__mskIn.Set_ValidDire(False,True)
	def Set_Alignment(self,align:int):
		'''
			设置图片的对齐方向，align可能取值为-1、0、1。
			水平排列时上(-1)、中(0)、下(1)对齐。
			竖直排列时左(-1)、中(0)、右(1)对齐。
		'''
		box=self.__box
		dire=box.direction()
		if(dire==QBoxLayout.Direction.TopToBottom or dire==QBoxLayout.Direction.BottomToTop):#竖向
			if(align<0):
				align=Qt.AlignmentFlag.AlignLeft
			elif(align>0):
				align=Qt.AlignmentFlag.AlignRight
			else:
				align=Qt.AlignmentFlag.AlignHCenter
		else:#横向
			if(align<0):
				align=Qt.AlignmentFlag.AlignTop
			elif(align>0):
				align=Qt.AlignmentFlag.AlignBottom
			else:
				align=Qt.AlignmentFlag.AlignVCente
		box.setAlignment(align)
	def Opt_InsertPict(self,pict:Union[XJQ_UrlPict,QPixmap],index:int=-1):
		'''
			在指定位置插入图片。
			如果index为负数则插入到末尾
		'''
		if(index<0):
			index=self.__box.count()-1#盒子必有一个空元素，其余元素均是控件
		if(isinstance(pict,QPixmap)):
			pict=XJQ_UrlPict(self.__config,None,pict)
		self.__stk.push(WidgetMove(pict,index,self.__box,True))
	def Opt_RemovePict(self,index:int):
		'''
			移除指定位置的图片
		'''
		item=self.__box.itemAt(index)
		if(item!=None):
			pict=item.widget()
			self.__stk.push(WidgetMove(pict,None,None,False))
	def Opt_RemoveSelectedPicts(self):
		'''
			移除选中的图片
		'''
		cmds=[]
		for wid in self.__mskSe.Get_SelectedWidgets():
			cmds.append(WidgetMove(wid,None,None,False))
		self.__stk.push(MultiCmds(*cmds))
		self.__mskSe.Opt_Clear()
	def Get_UndoStack(self):
		'''
			返回撤回重做栈，以进行更多的细化操作
		'''
		return self.__stk
	def Get_JointPict(self):
		'''
			获取拼接图，返回QPixmap对象
		'''
		pixLst=[]
		for pict in self.__box.children():
			if(isinstance(pict,XJQ_UrlPict)):
				pixLst.append(pict.Get_Pixmap())
		if(not pixLst):
			return QPixmap()
		
		dire=self.__box.direction()
		align=self.__box.alignment()
		horizontal=bool(dire&QBoxLayout.Direction.LeftToRight)
		align=0 if align&(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop) else 1 if align&Qt.AlignmentFlag.AlignCenter else 2

		mW,mH,tW,tH=0,0,0,0
		for pix in pixLst:
			w,h=pix.width(),pix.height()
			mW=max(mW,w)
			mH=max(mH,h)
			tW+=w
			tH+=h

		rst=QPixmap(tW,mH) if horizontal else QPixmap(mW,tH)
		rst.fill(Qt.GlobalColor.transparent)
		ptr=QPainter(rst)
		x,y=0,0
		for pix in pixLst:
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
		return rst





from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from XJ.Widgets.XJQ_GarbageBin import XJQ_GarbageBin
from XJ.Widgets.XJQ_ClipboardDrag import XJQ_ClipboardDrag
from XJ.Widgets.XJQ_ScreenCapture import XJQ_ScreenCapture


class Main(QWidget):
	def __init__(self):
		super().__init__()
		config:UrlPictConfig=UrlPictConfig((64,64))
		hbox=QHBoxLayout(self)
		vboxL=QVBoxLayout()
		cd=XJQ_ClipboardDrag(None,QPixmap(GetRealPath('./空白文件.ico')),QSize(96,96))
		pj=XJQ_PictJointer(config)
		gb=XJQ_GarbageBin(None,QSize(96,96))
		sc=XJQ_ScreenCapture()
		gb.dropped.connect(lambda mData:pj.Opt_RemoveSelectedPicts())
		sc.captured.connect(lambda pix:pj.Opt_InsertPict(pix))
		# sc.captured.connect(self.Opt_AppendPict)

		vboxL.addWidget(sc)
		vboxL.addWidget(cd)
		vboxL.addWidget(gb)
		vboxL.addStretch(1)
		hbox.addLayout(vboxL)
		hbox.addWidget(pj,1)
		self.__pj=pj
	# def Opt_InsertPict(self,pix:QPixmap,index:int):
		# XJQ_UrlPict()
		# self.__pj.Opt_InsertPict(index)

if True:
	app=QApplication([])
	win=Main()
	win.show()
	win.resize(640,480)
	app.exec()


exit()

if True:
	app=QApplication([])

	config=UrlPictConfig((64,64))
	jtr=XJQ_PictJointer(config)
	# pict=XJQ_UrlPict(config,QUrl(GetRealPath('./箭头-上.png')))
	# pict=XJQ_UrlPict(config,QUrl('./箭头-上.png'))
	# print(">>>",pict.size())
	# pict.resize(320,240)
	# pict.show()
	# lb=QLabel()
	# lb.show()
	# jtr.Opt_InsertPict(0,XJQ_UrlPict(config,'./箭头-上.png'))
	# jtr.Opt_InsertPict(0,XJQ_UrlPict(config,QUrl(GetRealPath('./图标-文件丢失.png'))))
	# jtr.Opt_InsertPict(0,XJQ_UrlPict(config,QUrl(GetRealPath('./加载动画-1.gif'))))
	# jtr.Opt_InsertPict(0,pict)
	jtr.resize(640,480)
	jtr.show()


	app.exec()

