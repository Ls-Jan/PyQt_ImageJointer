__author__='Ls_Jan'
__version__='1.0.0'
__all__='XJQ_PictJointer'

from PyQt5.QtWidgets import QWidget,QUndoStack
from PyQt5.QtGui import QMovie,QPixmap,QColor,QPainter,QTransform,QMouseEvent,QDrag
from PyQt5.QtCore import QRect,QPoint,QBuffer,QByteArray,Qt,QUrl,QMimeData
from .Command import ListElementMove
from XJ.Structs.XJ_MouseStatus import XJ_MouseStatus
from XJ.Functions.XJ_BinarySearch import XJ_BinarySearch
from XJ.Structs.XJQ_UrlPictManager import XJQ_UrlPictManager

from typing import Union

class XJQ_PictJointer(QWidget):
	'''
		图片拼接器。

		耦合的怪物(又不是不能用)。
		不解耦的最大原因是，没有功能复用性，
		只不过这也导致了改起来很特么烦，堆屎山了属于是。
	'''
	def __init__(self,loadingMovie:QMovie,failPict:QPixmap,insertArrowPict:QPixmap):
		super().__init__()
		self.__horizontal=False#排列方式
		self.__align=1#对齐方式左中右012
		self.__indexes=[0]#图片位置轴
		self.__urls=[]#图片url链接
		self.__selected=set()#被选中的图片索引
		self.__lastSelected=[0,0]#最近一次点击选中的图片索引，Ctrl点击时会根据该值判断是否取消选中，后一个数值的含义是：无行为(0)、单选(1)、反选目标(2)
		self.__pix=QPixmap()
		self.__mskSelect=QPixmap()
		self.__mskInsert=QPixmap()
		self.__cursorPos=[-1,0]#记录鼠标当前位置下的图片索引(-1为无效值)、插入方位(-1,0,1)
		self.__insertBorderDetect=50
		self.__ms=XJ_MouseStatus()
		self.__arrowPict=insertArrowPict
		self.__pm=XJQ_UrlPictManager(loadingMovie,failPict)
		self.__stk=QUndoStack()
		self.__color=[QColor(0,0,255,128),QColor(255,255,0,128),QColor(255,0,0,128)]#依次是选中、插入、插入边界
		self.__dragPreviewSize=[400,160]

		self.__pm.pixChanged.connect(self.__Opt_UpdatePix)
		self.__Opt_UpdatePix()
		self.setAcceptDrops(True)
	def Set_Direction(self,horizontal:bool):
		'''
			设置图片排列方向
		'''
		self.__horizontal=horizontal
		self.__Opt_UpdatePix()
	def Set_Align(self,align:int):
		'''
			设置对齐，
			align有三种取值0、1、2，
			分别对应左/上对齐、居中对齐、右/下对齐
		'''
		self.__align=align
		self.__Opt_UpdatePix()
	def Set_AntiJitter(self,val:int):
		'''
			设置防抖，鼠标拖拽超出指定距离时才发送拖拽事件
		'''
		self.__ms.Set_AntiJitter(val)
	def Set_DragPreviewSize(self,W:int=None,H:int=None):
		'''
			设置图片拖拽时的预览图最大宽高
		'''
		if(W!=None):
			self.__dragPreviewSize[0]=W
		if(H!=None):
			self.__dragPreviewSize[1]=H
	def Get_JointPix(self):
		'''
			获取拼接图片(QPixmap)，将会忽略那些加载失败的内容
		'''
		pix,indexes=self.__Get_JointPix(None,True)
		return pix
	def Get_Direction(self,isHorizontal:bool=True):
		'''
			获取排列方向，指定isHorizontal为真时(此为默认)如果是水平排列则返回真
		'''
		return self.__horizontal^(not isHorizontal)
	def Opt_InsertPict(self,index:int,url:str,data:Union[bytes,QPixmap]=None):
		'''
			插入图片，如果已有图片文件数据data(bytes/QPixmap)则可以进行传递。
			index为负数则末尾插入。
			如果url为None并且data不为None，则url会使用'hash:HHH'的格式，其中HHH的值为hash(data)
		'''
		index=len(self.__urls) if index<0 else min(len(self.__urls),index)
		if(isinstance(data,QPixmap)):
			arr=QByteArray()
			data.save(QBuffer(arr),'png')
			data=arr.data()
		if(url==None and data):
			url=f'hash:{hash(data)}'
		if(url):
			url=self.__pm.Opt_RequestUrl(url,data)
			moveSource=[url]
			moveDestination=ListElementMove.Index(self.__urls,[index])
			self.__stk.push(ListElementMove(moveSource,moveDestination))
			self.__Opt_UpdatePix()
	def Opt_SetSelected(self,selected:set):
		'''
			设置被选中的图片索引
		'''
		self.__selected=selected.copy()
		self.__Opt_UpdateMskSelect()
	def Opt_RemovePict(self,indices:list,removeSelected:bool=False):
		'''
			移除图片，如果指定removeSelected为真则只移除被选中的图片
		'''
		if(removeSelected):
			indices=list(self.__selected)
		self.__selected.clear()
		moveSource=ListElementMove.Index(self.__urls,indices)
		moveDestination=None
		self.__stk.push(ListElementMove(moveSource,moveDestination))
		self.__Opt_UpdatePix()
		self.__mskInsert=QPixmap()
		# self.__Opt_UpdateMskInsert()
	def Get_PictCount(self):
		'''
			获取当前图片数
		'''
		return len(self.__urls)
	def __Get_PosIsInside(self,pos:QPoint):
		'''
			判断点是否在图片范围内
		'''
		if(len(self.__urls)==0):
			return True
		pos=(pos.x(),pos.y())
		sSize=(self.width(),self.height())
		pSize=(self.__pix.width(),self.__pix.height())
		index=1 if self.__horizontal else 0
		delta=(sSize[index]-pSize[index])>>1
		return delta<=pos[index]<=delta+pSize[index]
	def __Get_Index(self,pos:QPoint):
		'''
			获取当前位置，返回图片索引值以及插入方位(-1,0,1)
		'''
		pos=pos.x() if self.__horizontal else pos.y()
		target=XJ_BinarySearch(self.__indexes,pos)
		insertFlag=0
		if(target==0):
			insertFlag=-1
		else:
			target-=1
			if(target==len(self.__indexes)-1):
				insertFlag=-1
			else:
				L=self.__indexes[target]
				R=self.__indexes[target+1]
				dL=pos-L
				dR=R-pos
				if(dL<self.__insertBorderDetect or dR<self.__insertBorderDetect):
					insertFlag=-1 if dL<dR else 1
		return target,insertFlag
	def __Get_JointPix(self,limitSize:tuple=None,ignoreInvalid:bool=False):
		'''
			获取拼接图，返回QPixmap以及indexes:list。
			如果给定limitSize，图片大小会限制在范围之内，同时也会影响返回的indexes。
			如果ignoreInvalid为真则会忽略那些失效的内容。
		'''
		if(not self.__urls):
			return QPixmap(),[0]
		index=0 if self.__horizontal else 1
		mW=0
		indexes=[0]
		pixInfo=[]#[(pix:QPixmap,size:tuple)]
		fail=set()#失败图片对应的pixInfo索引
		for url in self.__urls:
			if(ignoreInvalid and not self.__pm.Get_IsValid(url)):
				fail.add(len(pixInfo))
			pix=self.__pm.Get_UrlPict(url)
			size=(pix.width(),pix.height())
			indexes.append(indexes[-1]+size[index])
			pixInfo.append((pix,size))
			mW=max(size[(index+1)%2],mW)
		size=(indexes[-1],mW) if self.__horizontal else (mW,indexes[-1])
		size=(max(size[0],1),max(size[1],1))
		rate=min(limitSize[0]/size[0],limitSize[1]/size[1],1) if limitSize else 1
		mSize=[int(s*rate) for s in size]
		rst=QPixmap(*mSize)
		rst.fill(Qt.GlobalColor.transparent)
		ptr=QPainter(rst)
		ptr.setWindow(0,0,*size)#使用这步操作就可以省下ptr.drawPixmap绘制图片时的大小调整
		for i in range(len(pixInfo)):
			if(i in fail):#失败数据不绘制
				continue
			pix,size=pixInfo[i]
			offset=size[(index+1)%2]
			offset=(mW-offset)*self.__align/2 if self.__align>0 else 0
			delta=indexes[i]
			pos=(delta,offset) if self.__horizontal else (offset,delta)
			ptr.drawPixmap(*pos,pix)
		ptr.end()
		for i in range(len(indexes)):
			indexes[i]=int(indexes[i]*rate)
		return rst,indexes
	def __Opt_UpdatePix(self,urls:set=None):
		'''
			图片发生变化，进行更新
		'''
		sW,sH=self.width(),self.height()
		pix,indexes=self.__Get_JointPix((sW,sH))#懒得优化，索性重新生成
		pW,pH=pix.width(),pix.height()
		rst=QPixmap(sW,sH)
		rst.fill(Qt.GlobalColor.transparent)
		ptr=QPainter(rst)
		pos=(0,max(0,(sH-pH)/2)) if self.__horizontal else (max(0,(sW-pW)/2),0)
		if(pix):
			ptr.drawPixmap(*pos,pix)
		ptr.end()
		self.__pix=rst
		self.__indexes=indexes
		self.__Opt_UpdateMskSelect()
		self.update()
	def __Opt_UpdateMskSelect(self):
		'''
			更新maskSelect
		'''
		pix=QPixmap(self.__pix.size())
		pix.fill(Qt.transparent)
		if(self.__selected):
			ptr=QPainter(pix)
			rect=QRect(0,0,pix.width(),pix.height())
			for index in self.__selected:
				L=self.__indexes[index]
				R=self.__indexes[index+1] if index+1<len(self.__indexes) else None
				if(self.__horizontal):
					rect.setLeft(L)
					if(R):
						rect.setRight(R)
				else:
					rect.setTop(L)
					if(R):
						rect.setBottom(R)
				ptr.fillRect(rect,self.__color[0])
			ptr.end()
		self.__mskSelect=pix
		self.update()
	def __Opt_UpdateMskInsert(self):
		'''
			更新mskInsert
		'''
		index,insertFlag=self.__cursorPos
		pixSize=self.__pix.size().expandedTo(self.size())
		targetArea=QRect(QPoint(0,0),pixSize)
		insertArea=None
		TLRB=-1
		if(self.__horizontal):
			targetArea.setLeft(self.__indexes[index])
			targetArea.setRight(self.__indexes[index+1] if(index+1<len(self.__indexes)) else self.width())
			pixSize.setWidth(self.width())
			TLRB=1 if insertFlag<0 else 2 if insertFlag>0 else -1
		else:
			targetArea.setTop(self.__indexes[index])
			targetArea.setBottom(self.__indexes[index+1] if(index+1<len(self.__indexes)) else self.height())
			pixSize.setHeight(self.height())
			TLRB=0 if insertFlag<0 else 3 if insertFlag>0 else -1
		if(insertFlag!=0):
			insertArea=QRect(targetArea)
			if(TLRB==0):#上
				insertArea.setBottom(min(insertArea.bottom(),insertArea.top()+self.__insertBorderDetect))
			elif(TLRB==1):#左
				insertArea.setRight(min(insertArea.right(),insertArea.left()+self.__insertBorderDetect))
			elif(TLRB==2):#右
				insertArea.setLeft(max(insertArea.left(),insertArea.right()-self.__insertBorderDetect))
			elif(TLRB==3):#下
				insertArea.setTop(max(insertArea.top(),insertArea.bottom()-self.__insertBorderDetect))
		pix=QPixmap(pixSize)
		pix.fill(Qt.transparent)
		ptr=QPainter(pix)

		ptr.fillRect(targetArea,self.__color[1])
		if(insertArea):
			ptr.fillRect(insertArea,self.__color[2])
			if(TLRB>=0):
				self.__Opt_DrawArrow(self.__arrowPict,ptr,insertArea,TLRB)
		ptr.end()
		self.__mskInsert=pix
		self.update()
	@staticmethod
	def __Opt_DrawArrow(pix:QPixmap,ptr:QPainter,rect:QRect,TLRB:int):
		'''
			提供上箭头图片pix，
			使用画笔ptr，
			在区域rect内，
			根据箭头方向TLRB旋转箭头并进行绘制，可取值为0123，对应'TLRB'的含义(即上左右下)
		'''
		if(pix):
			P=[pix.width(),pix.height()]
			LT=[rect.left(),rect.top()]
			WH=[rect.width(),rect.height()]
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
				QTransform(1,0,0,0,1,0,C[0]-P[0],LT[1],1),#上
				QTransform(0,1,0,1,0,0,LT[0],C[1]-P[1],1),#左
				QTransform(0,1,0,-1,0,0,LT[0]+WH[0],C[1]-P[1],1),#右
				QTransform(1,0,0,0,-1,0,C[0]-P[0],LT[1]+WH[1],1),#下
			]
			ptr.save()
			ptr.setTransform(trans[TLRB%4])
			ptr.drawPixmap(0,0,pix)
			ptr.restore()
	def paintEvent(self,event):
		ptr=QPainter(self)
		sW,sH=self.width(),self.height()
		pW,pH=self.__pix.width(),self.__pix.height()
		pos=(0,max(0,(sH-pH)/2)) if self.__horizontal else (max(0,(sW-pW)/2),0)
		ptr.drawPixmap(0,0,self.__pix)
		if(self.__mskSelect):
			ptr.drawPixmap(*pos,self.__mskSelect)
		if(self.__mskInsert):
			ptr.drawPixmap(*pos,self.__mskInsert)
	def showEvent(self,event):
		self.__mskInsert=QPixmap()
		self.__Opt_UpdatePix()
	def resizeEvent(self,event):
		self.__mskInsert=QPixmap()
		self.__Opt_UpdatePix()
	def mousePressEvent(self,event):
		index,insertFlag=self.__Get_Index(event.pos())
		self.__ms.Opt_Update(event)
		if(event.button()==Qt.LeftButton):#鼠标左键
			ctrlFlag=bool(event.modifiers() & Qt.Modifier.CTRL)
			exist=index in self.__selected
			status=1 if not ctrlFlag else 2 if exist else 0
			self.__lastSelected=[index,status]
			if(self.__Get_PosIsInside(event.pos()) and index<len(self.__urls)):#没有点击到外部
				if(not ctrlFlag and not exist):
					self.__selected.clear()
				if(index<len(self.__urls)):
					self.__selected.add(index)
			else:
				self.__lastSelected[1]=0
				if(not ctrlFlag):
					self.__selected.clear()
			self.__Opt_UpdateMskSelect()
		else:
			event.ignore()
	def mouseMoveEvent(self,event):
		self.__ms.Opt_Update(event)
		if(self.__ms.Get_HasMoved(True) and self.__ms.Get_PressButtonStatus()[0]==Qt.MouseButton.LeftButton):#左键发生拖拽，发送QDrag。
			#事实上一旦调用了QDrag.exec，控件将不会再收到鼠标事件，对应的会收到拖拽事件
			urls=[]
			self.__lastSelected[1]=0
			for index in self.__selected:
				urls.append(QUrl(self.__urls[index]))
			if(urls):
				dg=QDrag(self)
				mData=QMimeData()
				mData.setUrls(urls)
				url=self.__urls[self.__lastSelected[0]]
				if(self.__pm.Get_IsValid(url)):
					pix=self.__pm.Get_UrlPict(url)
					pS=(pix.width(),pix.height())
					dS=self.__dragPreviewSize
					rate=min(1,*(dS[i]/pS[i] for i in range(2) if dS[i]>0))
					dg.setPixmap(pix.scaled(*(int(rate*pS[i]) for i in range(2))))
				dg.setMimeData(mData)
				dg.exec(Qt.CopyAction)
			self.__ms.Opt_Release()
	def mouseReleaseEvent(self,event):
		self.__ms.Opt_Update(event)
		index,flag=self.__lastSelected
		if(flag>0):
			if(flag==1):
				self.__selected.clear()
				self.__selected.add(index)
			else:
				self.__selected.remove(index)
			self.__Opt_UpdateMskSelect()
	def dragEnterEvent(self,event):
		mData=event.mimeData()
		# for key in mData.formats():#debug，查看QMimeData中的数据，虽然没啥意义
			# print(key,mData.data(key))
		if(mData.hasImage() or mData.hasUrls()):
			event.acceptProposedAction()
		self.__cursorPos=[-1,0]
		self.update()
	def dragMoveEvent(self,event):
		rst=self.__Get_Index(event.pos())
		if(self.__cursorPos[0]!=rst[0] or self.__cursorPos[1] !=rst[1]):
			self.__cursorPos=rst
			self.__Opt_UpdateMskInsert()
		self.update()
	def dropEvent(self,event):
		self.__mskInsert=QPixmap()
		self.update()
		insertIndex,insertFlag=self.__cursorPos
		if(insertIndex>=0):
			if(insertFlag!=0):#插入数据
				if(insertFlag>0):
					insertIndex+=1
				mData=event.mimeData()
				moveSource=None
				moveDestination=ListElementMove.Index(self.__urls,[insertIndex])
				if(self.__ms.Get_PressButtonStatus()[1]==QMouseEvent.Type.MouseButtonPress):#内部拖拽，移动数据
					moveSource=ListElementMove.Index(self.__urls,sorted(self.__selected))
					delta=0
					for i in sorted(self.__selected):
						if(i>=insertIndex):
							break
						delta+=1
					index=insertIndex-delta
					self.__selected={index+i for i in range(len(self.__selected))}
				else:#外部拖拽，插入数据
					if(mData.hasUrls()):
						urls=[]
						for url in mData.urls():
							url=self.__pm.Opt_RequestUrl(url.url())
							urls.append(url)
						moveSource=urls
					elif(mData.hasImage()):
						img=mData.imageData()
						data=QByteArray()
						pix=QPixmap()
						pix.fromImage(img)
						pix.save(QBuffer(data),'png')
						url=f'hash:{hash(data)}'
						self.__pm.Opt_RequestUrl(url,data)
						moveSource=[url]
				if(moveSource):
					self.__stk.push(ListElementMove(moveSource,moveDestination))
				self.__Opt_UpdatePix()
	def dragLeaveEvent(self,event):
		self.__mskInsert=QPixmap()
		self.update()





