#coding=utf-8
class status:
    '''这是一个用来定义部件状态的类'''
    def __init__(self,name,temp,humi,RAM_Used,RAM_Free,RAM_Total):
        self.name = name
        self.temp = temp
        self.humi = humi
        self.RAM_Used = RAM_Used
        self.RAM_Free = RAM_Free
        self.RAM_Total = RAM_Total
