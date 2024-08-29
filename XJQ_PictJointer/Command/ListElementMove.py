
__version__='1.0.0'
__author__='Ls_Jan'
__all__=['ListElementMove']

from PyQt5.QtWidgets import QUndoCommand
from typing import Union

class ListElementMove(QUndoCommand):
	'''
		列表元素移动命令，将元素移动到指定位置
	'''
	class Index:
		def __init__(self,lst:list,indices:list):
			'''
				结构体，记录列表以及索引。
			'''
			self.lst=lst
			self.indices=indices.copy()
	def __init__(self,source:Union[Index,list],destination:Union[Index,None]):
		'''
			将一份数据进行移动，包含数据的插入、移动、删除功能。
			如果source不是Index，那么会将数据插入到指定位置；
			如果destination为None，那么会将数据进行删除；
			如果source和destination均是Index，那么会将数据进行跨表移动；

			当在同个列表中移动位置时，会自动调整插入位置，也就是调用方只需关心插入点即可。
			例如[<A>,B,<C>,D,<E>,F]，将ACE移动到2位置，会变为[B,<A>,<C>,<E>,D,F]
		'''
		super().__init__()
		self.__source=source
		self.__destination=destination
		self.__init()
	def redo(self):
		self.__Move(self.__source,self.__destination)
	def undo(self):
		self.__Move(self.__destination,self.__source)
	def __init(self):
		source=self.__source
		destination=self.__destination
		if(isinstance(source,self.Index)):
			count=len(source.lst)
			source.indices=list(filter(lambda index:0<=index<count,source.indices))
			if(isinstance(destination,self.Index)):
				count=len(destination.lst)
				insertIndex=destination.indices[0]
				insertIndex=min(max(0,insertIndex),count)
				if(source.lst==destination.lst):
					delta=0
					for index in source.indices:
						if(index<insertIndex):
							delta+=1
					insertIndex-=delta
				destination.indices=[insertIndex+i for i in range(len(source.indices))]
	@classmethod
	def __Move(self,source:Union[Index,list],destination:Union[Index,None]):
		'''
			将数据进行移动。
			会返回实际插入数据
		'''
		data=[]
		if(not isinstance(source,self.Index)):
			data=source
		else:
			indicesSrc=[]
			for index in source.indices:
				if(0<=index<len(source.lst)):
					data.append(source.lst[index])
					indicesSrc.append(index)
			indicesSrc.sort()
			for index in reversed(indicesSrc):
				source.lst.pop(index)
		if(isinstance(destination,self.Index)):
			indicesDst=sorted(zip(destination.indices,data),key=lambda item:item[0])
			for item in indicesDst:
				index,val=item
				destination.lst.insert(index,val)




#简单的测试代码
if __name__=='__main__':
	from PyQt5.QtWidgets import QUndoStack

	lst=[1,2,3,4,5,6,7,8,9]
	selected=[1,3,5,7]
	# insertIndex=0
	# insertIndex=1
	insertIndex=5
	# insertIndex=len(lst)+1

	print([lst[index] for index in selected])
	for index in range(len(lst)):
		if(index==insertIndex):
			print(f'<{lst[index]}>',end=' ')
		else:
			if(index not in selected):
				print(lst[index],end=' ')
	print('\n\n')

	stk=QUndoStack()
	stk.push(ListElementMove(ListElementMove.Index(lst,selected),ListElementMove.Index(lst,[insertIndex])))
	print("——"*20)
	stk.undo()
	print("——"*20)
	stk.redo()
	exit()





