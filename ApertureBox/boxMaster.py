#coding=utf-8
#由于串口字符串通讯比较方便，所有函数返回值均为字符串格式，需要int及其他格式请自己转换
import time
import json
import requests
import serial
import RPi.GPIO
import sys
import os
import threading
from status import status

global core #核心
global ser #串口
global serIsOpen #串口开启标志
global lastDown #上次下载时间
global downRun #下载进程结束标志
global gatherRun #搜集信息进程结束标志
global lastGather #上次搜集信息时间

#以下是控制台格式输出样式
STYLE = {
        'fore':
        {   # 前景色
            'black'    : 30,   #  黑色
            'red'      : 31,   #  红色
            'green'    : 32,   #  绿色
            'yellow'   : 33,   #  黄色
            'blue'     : 34,   #  蓝色
            'purple'   : 35,   #  紫红色
            'cyan'     : 36,   #  青蓝色
            'white'    : 37,   #  白色
        },

        'back' :
        {   # 背景
            'black'     : 40,  #  黑色
            'red'       : 41,  #  红色
            'green'     : 42,  #  绿色
            'yellow'    : 43,  #  黄色
            'blue'      : 44,  #  蓝色
            'purple'    : 45,  #  紫红色
            'cyan'      : 46,  #  青蓝色
            'white'     : 47,  #  白色
        },

        'mode' :
        {   # 显示模式
            'mormal'    : 0,   #  终端默认设置
            'bold'      : 1,   #  高亮显示
            'underline' : 4,   #  使用下划线
            'blink'     : 5,   #  闪烁
            'invert'    : 7,   #  反白显示
            'hide'      : 8,   #  不可见
        },

        'default' :
        {
            'end' : 0,
        },
}

def UseStyle(string, mode = '', fore = '', back = ''):
    mode  = '%s' % STYLE['mode'][mode] if STYLE['mode'].has_key(mode) else ''
    fore  = '%s' % STYLE['fore'][fore] if STYLE['fore'].has_key(fore) else ''
    back  = '%s' % STYLE['back'][back] if STYLE['back'].has_key(back) else ''
    style = ';'.join([s for s in [mode, fore, back] if s])
    style = '\033[%sm' % style if style else ''
    end   = '\033[%sm' % STYLE['default']['end'] if style else ''
    return '%s%s%s' % (style, string, end)

#以下是内存信息
def getRAMinfo(target):
    mem = {}
    f = open("/proc/meminfo")
    lines = f.readlines()
    f.close()
    mem['total']=long(lines[0].split(':')[1].split()[0])
    mem['free']=(long(lines[1].split(':')[1].split()[0])+long(lines[3].split(':')[1].split()[0])+long(lines[4].split(':')[1].split()[0]))
    mem['used']=long(mem['total']-mem['free'])
    return str(int(mem[target]/1024))

#以下是CPU温度
def get_cpu_temp():
    cpu_temp_file = open( "/sys/class/thermal/thermal_zone0/temp" )
    cpu_temp = cpu_temp_file.read()
    cpu_temp_file.close()
    cpu_out = int(cpu_temp)/1000
    return str(cpu_out)

#以下是时间戳
def getTime(tFormat):
    if tFormat == 'long':
        return time.strftime("[%Y年%m月%d日 %H:%M:%S]")
    elif tFormat == 'short':
        return time.strftime("%H:%M")
    elif tFormat == 'last':
        return str(time.time())

#打印信息到控制台
def printInfo(info,status):
    print getTime('long'),
    print info,
    print '[状态：',
    if int(status) == 200:
        print UseStyle('200',fore='green'),
    else:
        print UseStyle(status,fore='red'),
    print ']'

#核心信息收集
def gatherCoreInfo():
    global core
    global gatherRun
    global lastGather
    while gatherRun == 1:
        if time.time()-lastGather>5:
            core.temp = get_cpu_temp()
            core.RAM_Used = getRAMinfo('used')
            core.RAM_Free = getRAMinfo('free')
            core.RAM_Total = getRAMinfo('total')

#下载信息
def download():
    global serIsOpen
    global ser
    global downRun
    while True:
        try:
            if serIsOpen == 0:
                ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            try:
                download_data_to_arduino('ttyACM0')
            except:
                serIsOpen = 0
        except:
            if serIsOpen == 0:
                ser = serial.Serial('/dev/ttyACM1', 9600, timeout=1)
            try:
                download_data_to_arduino('ttyACM1')
            except:
                serIsOpen = 0
        if downRun == 0:
            break

#下载信息到Arduino（受限于Arduino，下载为1秒一次）
def download_data_to_arduino(serNum='未知'):
    global lastDown
    global core
    global serIsOpen
    global ser
    serIsOpen = 1
    if time.time()-lastDown>1:
        dataSheet = core.temp
        dataSheet += ','
        dataSheet += core.RAM_Free
        dataSheet += ','
        dataSheet += str(int(float(core.RAM_Used)/float(core.RAM_Total)*100))
        dataSheet += ','
        dataSheet += getTime('short')
        ser.write(dataSheet)
        content = '已在串口'+serNum+'上向Arduino下载数据'
        printInfo(content,'200')
        lastDown = time.time()

#以下是主进程
def main():
    global downRun
    global gatherRun
    downloadThread = threading.Thread(target = download,args=())
    gatherThread = threading.Thread(target = gatherCoreInfo,args=())
    while True:#重启各个线程
        try:
            if downloadThread.isAlive() == False:
                downloadThread.start()
            if gatherThread.isAlive() == False:
                gatherThread.start()
        except:
            downRun = 0
            gatherRun = 0
            break


#开始程序
if __name__ == '__main__':
    #初始化
    core = status('Raspberry Pi',get_cpu_temp(),0,getRAMinfo('used'),getRAMinfo('free'),getRAMinfo('total'))
    serIsOpen = 0
    lastDown = time.time()-1
    lastGather = time.time()-1
    downRun = 1
    gatherRun = 1
    #主循环
    main()
