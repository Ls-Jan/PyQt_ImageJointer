

__version__='1.0.0'
__author__='Ls_Jan'


from PyQt5.QtWidgets import QWidget,QBoxLayout
from PyQt5.QtCore import Qt,QPoint
from PyQt5.QtGui import QPixmap,QPainter,QTransform,QColor,QPen

from XJ.Functions.GetRealPath import GetRealPath
from XJ.Arithmetic.XJ_BinarySearch import XJ_BinarySearch
from XJ.Widgets.XJQ_PureColorIcon import XJQ_PureColorIcon

__all__=['InsertPreview']

class InsertPreview(QWidget):
	'''
		将数据插入可视化，能够清楚看到数据插入点。
		用于盒式布局控件。
		可以理解为一个遮罩。
	'''
	def __init__(self,parent:QWidget):
		super().__init__(parent)
		self.setAttribute(Qt.WA_TransparentForMouseEvents, True)#鼠标事件穿透
		self.__lst=[0]
		self.__box:QBoxLayout=parent.layout()
		self.__index=0#插入点
		self.__arrowUp=True#插入点的指示箭头方向(上)
		self.__arrowPix=XJQ_PureColorIcon(GetRealPath('箭头-010.png')).pixmap(64,64)
		self.__valid=True#判断鼠标位置是否在控件之内
		self.raise_()
		self.hide()
		self.__Update_Lst()
	def __Update_Lst(self):
		'''
			更新self.__lst
		'''
		dire=self.__Get_Dire()
		box=self.__box
		cnt=box.count()
		rng=range(0,cnt,1)
		if(dire&0b10):
			rng=range(cnt-1,-1,-1)
		lst=[0]
		if(dire&0b01):
			for i in rng:
				item=box.itemAt(i)
				val=item.geometry().height()
				lst.append(lst[-1]+val)
		else:
			for i in rng:
				item=box.itemAt(i)
				val=item.geometry().width()
				lst.append(lst[-1]+val)
		self.__lst=lst
	def __Get_Dire(self):
		'''
			返回self.__box的方向，取值为0、1、2、3。
			0：左到右；
			1：上到下；
			2：右到左；
			3：下到上；
		'''
		dire=self.__box.direction()
		if(dire==QBoxLayout.Direction.LeftToRight):
			dire=0b00
		elif(dire==QBoxLayout.Direction.TopToBottom):
			dire=0b01
		elif(dire==QBoxLayout.Direction.RightToLeft):
			dire=0b10
		elif(dire==QBoxLayout.Direction.BottomToTop):
			dire=0b11		
		return dire
	def __Opt_DrawArrow(self,pix:QPixmap,ptr:QPainter,LTWH:list,RBLU:int):
		'''
			提供上箭头图片pix，
			使用画笔ptr，
			在区域LTWH内，
			根据箭头方向RBLU旋转箭头并进行绘制
		'''
		P=[pix.width(),pix.height()]
		LT=LTWH[:2]
		WH=LTWH[2:]
		for i in range(2):
			if(WH[i]<0):
				LT[i]+=WH[i]
				WH[i]=-WH[i]
		for i in range(2):
			if(P[i]>WH[i]):
				P[(i+1)%2]=int(P[(i+1)%2]*WH[i]/P[i])
				P[i]=WH[i]
				pix=pix.scaled(*P)
		P=[P[i]>>1 for i in range(2)]
		C=[LT[i]+(WH[i]>>1) for i in range(2)]
		trans=[
			QTransform(0,1,0,-1,0,0,LT[0]+WH[0],C[1]-P[1],1),
			QTransform(1,0,0,0,-1,0,C[0]-P[0],LT[1]+WH[1],1),
			QTransform(0,1,0,1,0,0,LT[0],C[1]-P[1],1),
			QTransform(1,0,0,0,1,0,C[0]-P[0],LT[1],1),]
		ptr.save()
		ptr.setTransform(trans[RBLU])
		ptr.drawPixmap(0,0,pix)
		ptr.restore()
	def showEvent(self,event):
		self.__Update_Lst()
	def paintEvent(self,event):
		if(self.parent()):
			self.resize(self.parent().size())
		col_bg=QColor(0,0,0,64)#背景色
		col_hv=QColor(0,0,255,64)#悬浮色
		col_ln=QColor(0,0,0,128)#分界色
		ptr=QPainter(self)
		pen=QPen(col_ln)
		lst=self.__lst

		#细线绘制
		pen.setWidth(3)
		ptr.setPen(pen)
		ptr.fillRect(self.geometry(),col_bg)
		dire=self.__Get_Dire()
		w=self.width()
		h=self.height()
		if(dire&0b01):#竖向
			for pos in lst:
				ptr.drawLine(0,pos,w,pos)
		else:#横向
			for pos in lst:
				ptr.drawLine(pos,0,pos,h)

		#高亮绘制
		index=self.__index
		cnt=len(lst)
		if(index>=cnt):
			index=cnt-1
		pe=lst[index]
		ps=-1
		if(self.__arrowUp):
			if(index+1<cnt):
				ps=lst[index+1]
		else:
			if(index>0):
				ps=lst[index-1]
		pen.setWidth(10)
		ptr.setPen(pen)

		if(self.__valid):
			if(dire&0b01):#竖向
				if(ps<0):
					ps=h
				ps=(ps+pe)>>1
				LT=[0,ps]
				WH=[w,pe-ps+1]
				ptr.fillRect(*LT,*WH,col_hv)
				ptr.drawLine(0,pe,w,pe)
				print(">>",0b11 if self.__arrowUp else 0b01)
				self.__Opt_DrawArrow(self.__arrowPix,ptr,LT+WH,0b11 if self.__arrowUp else 0b01)
			else:#横向
				if(ps<0):
					ps=w
				ps=(ps+pe)>>1
				LT=[ps,0]
				WH=[pe-ps+1,h]
				ptr.fillRect(*LT,*WH,col_hv)
				ptr.drawLine(pe,0,pe,w)
				self.__Opt_DrawArrow(self.__arrowPix,ptr,LT+WH,0b10 if self.__arrowUp else 0b00)
	def Opt_PosChange(self,pos:QPoint):
		'''
			当鼠标移动时需要调用该函数
		'''
		valid=self.geometry().contains(pos)
		update=False
		if(valid!=self.__valid):
			self.__valid=valid
			update=True
		if(valid):
			dire=self.__Get_Dire()
			lst=self.__lst
			cnt=len(lst)
			arrowUp=True
			pos=pos.y() if(dire&0b01) else pos.x()
			index=XJ_BinarySearch(lst,pos)
			if(index==cnt):
				if(cnt>0):
					arrowUp=False
			else:
				if(index>0):
					p1=lst[index-1]
					p2=lst[index]
					ph=(p1+p2)>>1
					if(pos>ph):
						arrowUp=False
					else:
						index-=1
			update=(self.__arrowUp!=arrowUp) or (self.__index!=index)
			self.__arrowUp=arrowUp
			self.__index=index
		if(update):#避免频繁更新
			self.update()
	def Get_InsertIndex(self):
		'''
			获取插入点。
			如果插入点不存在则返回None
		'''
		return self.__index if self.__valid else None
	


	