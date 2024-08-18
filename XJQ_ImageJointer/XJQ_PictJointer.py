


__version__='1.0.0'
__author__='Ls_Jan'
__all__=['XJQ_PictJointer']

from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QUndoStack
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from XJ.Structs.XJ_MouseStatus import XJ_MouseStatus
from .InsertPreview import InsertPreview
from .Command import Move



class XJQ_UrlPict(QLabel):
	'''
		外链图片，记录url链接以及图片是否可用。
		同时重载了左键拖拽，允许拖拽图片。

		注意：
			- 即用即弃，应当将其作为只读数据使用，不允许调用setPixmap、setText、setMovie；
			- 图片数据至多是无效→有效，不能来回切换，这也是即用即弃的一个原因；
			- 初始化时传入的url与实际url并不一致，需获调用XJQ_UrlPict.Get_Url获取实际的url；
	'''
	def __init__(self,pix:QPixmap):
		'''
			传入的url会经过一次处理以保证顺利得到数据，因此以XJQ_UrlPict.Get_Url返回的url为准。

			如果已经有图片二进制数据(内存数据/bytes)，那么传入的data的hash值将决定url(因为url要作为标识id使用)，
			此时url格式为：hash:XXXXXXX
		'''
		self.__selected=False
		self.__valid=[]
		self.__url=''
		self.setPixmap(pix)
		self.__valid=pix!=None
	def paintEvent(self,event):
		super().paintEvent(event)
		if(self.__selected):
			ptr=QPainter(self)
			ptr.fillRect(QRect(QPoint(0,0),self.size()),QColor(0,0,0,128))
	def Set_Selected(self,flag:bool,invert:bool=False):
		'''
			设置选中状态，会影响绘制效果。
			如果invert为真，则无视flag并反转当前状态。
			当前图片无效时无法被选中
		'''
		if(self.Get_IsValid()):
			if(invert):
				flag=not self.__selected
			self.__selected=flag
			self.update()
	def Get_IsSelected(self):
		'''
			获取图片的选中状态
		'''
		return self.__selected
	def Get_IsValid(self):
		'''
			判断图片数据是否有效
		'''
		return bool(self.__valid)
	def Get_Url(self):
		'''
			获取图片链接(str)
		'''
		return self.__url
	def Get_Pict(self):
		'''
			获取图片数据(QPixmap)。
			如果图片无效则返回None
		'''
		return self.pixmap() if self.Get_IsValid() else None




class XJQ_PictJointer(QWidget):
	'''
		图片拼接器。
		能将图片以行或列的方式进行显示。
		使用到的控件为XJQ_UrlPict。
	'''
	def __init__(self):
		'''
			将配置好的UrlManager传进去。
		'''
		super().__init__()
		self.__pv=InsertPreview(self)
		self.__stk=QUndoStack(self)
		self.__ms=XJ_MouseStatus(self)
		self.__box=QBoxLayout(QBoxLayout.Direction.TopToBottom,self)
		self.__selected=[]
		self.__drag=False
		self.__clickedPict:XJQ_UrlPict=None
		self.__pictSelected=False#记录当前选中状态，用于反转
		self.setAcceptDrops(True)
	def dragEnterEvent(self,event):
		mData=event.mimeData()
		if(mData.hasImage() or mData.hasUrls()):
			self.__pv.show()
			event.acceptProposedAction()
	def dragMoveEvent(self,event):
		self.__pv.Opt_PosChange(event.pos())
	def dropEvent(self,event):
		mData=event.mimeData()
		if(mData.hasImage()):
			img=mData.imageData()
			# pict=UrlPict(hash(img))
			self.__stk.push()
			# self.__pictManager.Set_UrlPict(pict)
			# print(img)
		elif(mData.hasUrls()):
			for url in mData.urls():
				pass
				# pict=UrlPict(url)
				# self.__pictManager.Set_UrlPict(pict)
				# Move(pict,)
		self.__pv.hide()
	def mousePressEvent(self,event):
		self.__clickedPict=None
		self.__drag=False
		if(event.button()==Qt.LeftButton):
			if(not (event.modifiers() & Qt.Modifier.CTRL)):
				self.__selected.clear()
			pict=QApplication.widgetAt(QCursor.pos())
			if(isinstance(pict,XJQ_UrlPict)):
				if(pict.Get_IsValid()):#仅图片有效才进行下一步处理
					self.__clickedPict=pict
					self.__pictSelected=pict.Get_IsSelected()
					self.__selected.append(pict)
					self.__ms.Opt_Update(event)
	def mouseMoveEvent(self,event):
		if(not self.__drag and self.__clickedPict):
			self.__ms.Opt_Update(event)
			if(self.__ms.Get_HasMoved()):#发生拖拽，发送QDrag
				self.__drag=True
				for pict in self.__selected:
					pict.hide()
				dg=QDrag(self)
				mData=QMimeData()
				mData.setUrls([pict.Get_Url() for pict in self.__selected])
				dg.setPixmap(self.__clickedPict.Get_Pict())
				dg.setMimeData(mData)
				dg.exec(Qt.MoveAction)
	def mouseReleaseEvent(self,event):
		if(not self.__drag):#没拖拽，仅点击，如果按下了CTRL则对点击的控件进行反选
			if(self.__clickedPict):
				if(event.modifiers() & Qt.Modifier.CTRL):
					self.__clickedPict.Set_Selected(not self.__pictSelected)
		self.__clickedPict=None

	def Set_Direction(self,dire:QBoxLayout.Direction):
		'''
			dire决定盒布局方向(四向)。
			调用后最好额外调用Set_Alignment以设置控件对齐方向。
		'''
		self.__box.setDirection(dire)
	def Set_Alignment(self,align:int):
		'''
			设置图片的对齐方向。
			align有以下三种值可选：
				-1：左/上；
				0：中；
				1：右/下
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
	def Opt_InsertPict(self,index,pict:XJQ_UrlPict):
		'''
			在指定位置插入图片
		'''
		self.__stk.push(Move(pict,index,self.__box,True))
	def Opt_RemovePict(self,index:int):
		'''
			移除指定位置的图片
		'''
		item=self.__box.itemAt(index)
		if(item!=None):
			pict=item.widget()
			self.__stk.push(Move(pict,None,None,False))


