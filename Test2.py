
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from XJ.Structs.XJ_CacheProxy.BaseCallback import BaseCallback
from XJ.Structs.XJ_CacheProxy.XJ_QUrlCacheProxy import XJ_QUrlCacheProxy
from XJ.Structs.XJ_CacheProxy.BaseCacheProxy import BaseCacheProxy
from XJ.Functions.XJ_BinarySearch import XJ_BinarySearch

class XJ_UrlPictManager(QObject):
	'''
		外链图片管理器，将图片加载过程更加的分化。
		会发出三种信号：
			- pixChanged(set)：图片信息发生变化的链接；
			- requestSuccess(str)：请求成功的链接；
			- requestFail(str)：请求失败的链接；
	'''
	pixChanged=pyqtSignal(set)
	requestSuccess=pyqtSignal(str)
	requestFail=pyqtSignal(str)
	class __Callback(BaseCallback):#正是因为无法顺利的多继承，才硬生生的扯出这一坨东西，虽然不雅但问题不大
		def __init__(self,mutex:QMutex,finishUrls:set,failUrls:set,urls:map,failPict:QPixmap):
			self.__finishUrls=finishUrls
			self.__failUrls=failUrls
			self.__urls=urls
			self.__failPict=failPict
			self.__mutex=mutex
		def __call__(self,url:str,data:bytes):
			self.__mutex.lock()
			self.__finishUrls.add(url)
			if(data):
				pix=QPixmap()
				pix.loadFromData(data)
				self.__urls[url]=pix
			else:
				self.__urls[url]=self.__failPict
				self.__failUrls.add(url)
			self.__mutex.unlock()
	__timeout:int=0
	__failPict:QPixmap=None
	__cacheProxy:BaseCacheProxy=None
	__loadingMovie:QMovie=None
	def __init__(self,loadingMovie:QMovie,failPict:QPixmap,cacheProxy:BaseCacheProxy=None,timeout:int=0):
		super().__init__()
		self.__mutex=QMutex()
		self.__loadingMovie=loadingMovie
		self.__failPict=failPict
		self.__cacheProxy=cacheProxy if cacheProxy else XJ_QUrlCacheProxy()
		self.__timeout=timeout
		self.__urlsRequesting=set()#请求中
		self.__urlsFinished=set()#请求完毕
		self.__urlsFail=set()#失败
		self.__urlsPix=dict()#成功。{url<str>:pix<QPixmap>}
		mv=loadingMovie
		mv.stop()
		mv.jumpToFrame(0)
		mv.frameChanged.connect(self.__Opt_UpdateFrame)
	def __Opt_UpdateFrame(self):
		'''
			发送famreChanged信号，如果当前无正在请求的数据则会暂停QMovie
		'''
		urlsRequesting=self.__urlsRequesting.copy()
		urlsFinished=self.__urlsFinished.copy()
		if(urlsRequesting):
			self.__mutex.lock()
			for url in urlsRequesting:
				if(url not in urlsFinished):
					self.__urlsPix[url]=self.__loadingMovie.currentPixmap()
			self.__urlsRequesting.difference_update(urlsFinished)
			self.__urlsFinished.clear()
			self.__mutex.unlock()
			for url in urlsRequesting:
				if(url in urlsFinished):
					if(url not in self.__urlsFail):
						self.requestSuccess.emit(url)
					else:
						self.requestFail.emit(url)
			self.pixChanged.emit(self.__urlsRequesting.copy())
		else:
			self.__loadingMovie.stop()
	def Opt_RequestUrl(self,url:str,data:bytes):
		'''
			请求图片数据。
			如果已有图片数据则可指定data进行设置
		'''
		self.__mutex.lock()
		self.__urlsPix[url]=self.__loadingMovie.currentPixmap()
		self.__urlsRequesting.add(url)
		self.__mutex.unlock()
		self.__loadingMovie.start()
		if(data):
			self.__cacheProxy.Set_UrlData(url,data)
		self.__cacheProxy.Opt_RequestUrl(url,self.__Callback(self.__mutex,self.__urlsFinished,self.__urlsFail,self.__urlsPix,self.__failPict),self.__timeout)
	def Get_Size(self,url:str)->QSize:
		'''
			获取图片大小(QSize)
		'''
		return self.__urlsPix[url].size()
	def Get_IsValid(self,url:str)->bool:
		'''
			判断图片是否有效
		'''
		return url not in self.__urlsRequesting and url not in self.__urlsFail
	def Get_RequestingUrl(self)->set:
		'''
			返回正在请求中的url
		'''
		return self.__urlsRequesting
	def Get_AllUrls(self):
		'''
			获取所有的url
		'''
		return set(self.__urlsPix)
	def Get_UrlPict(self,url:str)->QPixmap:
		'''
			获取url的当前图片
		'''
		return self.__urlsPix[url]






class XJQ_ImageJointer(QWidget):
	def __init__(self,loadingMovie:QMovie,failPict:QPixmap):
		super().__init__()
		self.__horizontal=False
		self.__align=1
		self.__indexes=[0]
		self.__urls=[]
		self.__pix=QPixmap()#预拼接图
		self.__selected=[]
		self.__insert=[]#控件位置和插入方位(-1,0,1)
		self.__insertBorderDetect=40
		self.__pm=XJ_UrlPictManager(loadingMovie,failPict)
		self.__pm.pixChanged.connect(self.__Opt_Update)
		self.__Opt_Update()
		self.setMouseTracking(True)
	def Set_Direction(self,horizontal:bool):
		'''
			设置图片排列方向
		'''
		self.__horizontal=horizontal
		self.__Opt_Update()
	def Set_Align(self,align:int):
		'''
			设置对齐，
			align有三种取值0、1、2，
			分别对应左/上对齐、居中对齐、右/下对齐
		'''
		self.__align=align
		self.__Opt_Update()
	def Get_JointPix(self):
		'''
			获取拼接图片(QPixmap)，将会忽略那些加载失败的内容
		'''
		pix,indexes=self.__Get_JointPix(True)
		return pix
	def Opt_InsertPix(self,index:int,url:str,data:bytes=None):
		'''
			插入图片，如果已有图片文件数据data则可以进行传递
		'''
		index=0 if index<0 else min(len(self.__urls),index)
		self.__pm.Opt_RequestUrl(url,data)
		self.__urls.insert(index,url)
		self.__Opt_Update()
	def __Opt_Update(self,urls:set=None):
		'''
			图片发生变化，进行更新
		'''
		pix,indexes=self.__Get_JointPix()
		self.__pix=pix
		self.__indexes=indexes
		self.update()
		return
		if(urls==None):
			self.__Get_JointPix()
		else:
			for url in urls:

				self.__pm.Get_UrlPict(url)
		self.update()
		
	def __Get_Index(self,rPos:QPoint):
		'''
			获取当前位置，返回图片索引值以及插入方位(-1,0,1)
		'''
		sW,sH=self.width(),self.height()
		pW,pH=self.__pix.width(),self.__pix.height()
		rate=max(pW/sW,pH/sH,1)
		pos=rPos.x() if self.__horizontal else rPos.y()
		pos=int(pos*rate)
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
	def __Get_JointPix(self,ignoreInvalid:bool=False):
		'''
			获取拼接图，返回QPixmap以及indexes:list。
			如果ignoreInvalid为真则会忽略那些失效的内容
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
		rst=QPixmap(indexes[-1],mW) if self.__horizontal else QPixmap(mW,indexes[-1])
		rst.fill(Qt.GlobalColor.transparent)
		ptr=QPainter(rst)
		for i in range(len(pixInfo)):
			if(i in fail):#失败数据不绘制
				continue
			pix,size=pixInfo[i]
			offset=size[(index+1)%2]
			offset=(mW-offset)*(2-self.__align) if self.__align>0 else 0
			delta=indexes[i]
			pos=(delta,offset) if self.__horizontal else (offset,delta)
			ptr.drawPixmap(*pos,pix)
		ptr.end()
		return rst,indexes
	def paintEvent(self,event):
		ptr=QPainter(self)
		sW,sH=self.width(),self.height()
		pW,pH=self.__pix.width(),self.__pix.height()
		rate=min(sW/pW,sH/pH,1)
		pW,pH=int(pW*rate),int(pH*rate)
		drawArea=QRect(0,max(0,(sH-pH)/2),pW,pH) if self.__horizontal else QRect(max(0,(sW-pW)/2),0,pW,pH)
		ptr.drawPixmap(drawArea,self.__pix)
		if(self.__insert):
			index,insertFlag=self.__insert
			targetArea=QRect(drawArea)
			insertArea=None
			if(self.__horizontal):
				targetArea.setLeft(self.__indexes[index])
				targetArea.setRight(self.__indexes[index+1] if(index+1<len(self.__indexes)) else self.width())
			else:
				targetArea.setTop(self.__indexes[index])
				targetArea.setBottom(self.__indexes[index+1] if(index+1<len(self.__indexes)) else self.height())
			if(insertFlag!=0):
				insertArea=QRect(targetArea)
				if(self.__horizontal):
					if(insertFlag<0):
						insertArea.setRight(insertArea.left()+self.__insertBorderDetect)
					else:
						insertArea.setLeft(insertArea.right()-self.__insertBorderDetect)
				else:
					if(insertFlag<0):
						insertArea.setBottom(insertArea.top()+self.__insertBorderDetect)
					else:
						insertArea.setTop(insertArea.bottom()-self.__insertBorderDetect)
			ptr.fillRect(targetArea,QColor(255,255,0,128))
			if(insertArea):
				ptr.fillRect(insertArea,QColor(255,0,0,128))
	def showEvent(self,event):
		self.__Opt_Update()
	def resizeEvent(self,event):
		self.__Opt_Update()
	def mouseMoveEvent(self,event):
	# def mousePressEvent(self,event):
		rst=self.__Get_Index(event.pos())
		self.__insert=rst
		self.update()
		# print(rst)
	# def dragEnterEvent(self,event):
	# 	mData=event.mimeData()
	# 	if(mData.hasImage() or mData.hasUrls()):
	# 		self.__mskIn.show()
	# 		self.__mskIn.update()
	# 		event.acceptProposedAction()
	# def dragLeaveEvent(self,event):
	# 	self.__mskIn.hide()
	# def dragMoveEvent(self,event):
	# 	self.__mskIn.update()
	# def dropEvent(self,event):
	# 	layout,target,dire=self.__mskIn.Get_InsertPos()
	# 	if(layout!=None and dire%5!=0):#不是0或5，确定插入数据。虽然dire有效时layout必然不为空，但还是小防一手
	# 		mData=event.mimeData()
	# 		insertIndex=layout.indexOf(target)+(0 if dire<5 else 1) if(target!=None) else 0
	# 		if(self.__mskSe.Get_IsPressed()):#内部拖拽，移动控件
	# 			lst=[]
	# 			cmds=[]
	# 			for wid in self.__mskSe.Get_SelectedWidgets():
	# 				index=layout.indexOf(wid)
	# 				if(index>=0):
	# 					lst.append((index,wid))
	# 			lst.sort(key=lambda item:item[0])
	# 			for item in reversed(lst):
	# 				index,wid=item
	# 				cmds.append(Move(wid,insertIndex,layout))
	# 				if(index<insertIndex):
	# 					insertIndex-=1#不可能会出现小于0的情况
	# 			self.__stk.push(MultiCmds(*cmds))
	# 			self.__mskSe.Opt_Clear()
	# 		else:#外部拖拽，创建控件
	# 			cmds=[]
	# 			if(mData.hasUrls()):
	# 				for url in reversed(mData.urls()):
	# 					pict=XJQ_UrlPict(self.__config,url)
	# 					cmds.append(Move(pict,insertIndex,self.__box,True))
	# 			elif(mData.hasImage()):

	# 				img=mData.imageData()
	# 				data=QByteArray()
	# 				pix=QPixmap()
	# 				print(img)
	# 				pix.fromImage(img)
	# 				pix.save(QBuffer(data),'png')

	# 				pict=XJQ_UrlPict(self.__config,None,data)
	# 				cmds.append(Move(pict,insertIndex,self.__box,True))
	# 			if(cmds):
	# 				self.__stk.push(MultiCmds(*cmds))
	# 	self.__mskIn.hide()
	# def mousePressEvent(self,event):
	# 	self.__ms.Opt_Update(event)
	# 	if(event.button()==Qt.LeftButton):
	# 		self.__mskSe.Opt_Press(bool(event.modifiers() & Qt.Modifier.CTRL))
	# def mouseMoveEvent(self,event):
	# 	self.__ms.Opt_Update(event)
	# 	self.__mskIn.update()
	# 	lastPressedWid:QLabel=self.__mskSe.Get_LastPressedWidget()
	# 	if(lastPressedWid!=None):
	# 		self.__ms.Opt_Update(event)
	# 		if(self.__ms.Get_HasMoved(True)):#发生拖拽，发送QDrag。事实上一旦调用了QDrag.exec，控件将不会再收到鼠标事件，对应的会收到拖拽事件
	# 			self.__mskSe.Opt_Drag()
	# 			urls=[]
	# 			for wid in self.__mskSe.Get_SelectedWidgets():
	# 				pict:XJQ_UrlPict=wid
	# 				urls.append(QUrl(pict.Get_Url()))
	# 			if(urls):
	# 				dg=QDrag(self)
	# 				mData=QMimeData()
	# 				mData.setUrls(urls)
	# 				dg.setPixmap(lastPressedWid.pixmap())
	# 				dg.setMimeData(mData)
	# 				dg.exec(Qt.MoveAction)
	# def mouseReleaseEvent(self,event):
	# 	self.__ms.Opt_Update(event)
	# 	self.__mskSe.Opt_Release()

if True:
	app=QApplication([])
	jtr=XJQ_ImageJointer(QMovie('./XJQ_PictJointer/加载动画-1.gif'),QPixmap('./XJQ_PictJointer/图标-文件丢失.png'))
	jtr.Opt_InsertPix(0,r'F:\Github_Repository\Python\PyQt_ImageJointer\XJQ_PictJointer\图标-截图.ico')
	jtr.Opt_InsertPix(0,r'F:\Github_Repository\Python\PyQt_ImageJointer\XJQ_PictJointer\图标-截图.ico')
	# jtr.Opt_InsertPix(0,r'F:\Github_Repository\Python\PyQt_ImageJointer\XJQ_PictJointer\图标-截图.ico')
	# jtr.Opt_InsertPix(0,r'F:\Github_Repository\Python\PyQt_ImageJointer\XJQ_PictJointer\图标-截图.ico')
	jtr.resize(600,800)
	jtr.show()

	app.exec()


