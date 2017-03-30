#coding=utf-8
import time
import json
import requests
import serial
import RPi.GPIO
import sys
import os
import threading

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

#yeelink api配置
api_key='3297ae1f5852fba76237d5cff223e278'
api_headers={'U-ApiKey':api_key,'content-type': 'application/json'}

black = " ---------------------------"

#内存信息
def getRAMinfo(tar):
    mem = {}  
    f = open("/proc/meminfo")  
    lines = f.readlines()  
    f.close()  
    for line in lines:  
        if len(line) < 2: continue  
        name = line.split(':')[0]  
        var = line.split(':')[1].split()[0]  
        mem[name] = long(var) * 1024.0  
    mem['MemUsed'] = mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached']  
    return mem[tar]/1024/1024
    
#得到CPU温度
def get_cpu_temp():
    global last_cpu_time
    global cpu_out
    if time.time()-last_cpu_time>10:
        cpu_temp_file = open( "/sys/class/thermal/thermal_zone0/temp" )
        cpu_temp = cpu_temp_file.read()
        cpu_temp_file.close()
        cpu_out = float(cpu_temp)/1000
    last_cpu_time = time.time()#防止频繁读取系统
    return cpu_out

#上传CPU温度到yeelink
def upload_cpu_temp_to_yeelink():
    while True:
        #学习变量字符串 url=r'%s/device/%s/sensor/%s/datapoints' % (api_url,raspi_device_id,cpu_sensor_id)
        url='http://api.yeelink.net/v1.0/device/355998/sensor/403110/datapoints'
        strftime=time.strftime("%Y-%m-%dT%H:%M:%S")
        cpu_temp=get_cpu_temp()
        data={"timestamp":strftime , "value": cpu_temp}
        res=requests.post(url,headers=api_headers,data=json.dumps(data))
        strftime=time.strftime("%Y年%m月%d日 %H:%M:%S")
        print "[",strftime,"]",
        content = "上传数据到Yeelink服务器"
        n = 40 - len(content)
        content += black[0:n]
        print content,
        if res.status_code == 200:
            print "[状态:",UseStyle(res.status_code,fore = "green"),"]"
        else:
            print "[状态:",UseStyle(res.status_code,fore = "red"),"]"
        time.sleep(30)

#下载数据到arduino
def download_data_to_arduino():
    while True:
        #CPU信息
        cpu_temp = int(get_cpu_temp())
        dataSend = str(cpu_temp)
        dataSend += ","
        #RAM信息
        RAM_total =862
        RAM_used =getRAMinfo("MemUsed")
        RAM_free =862 - RAM_used
        RAM_per = int(RAM_used/RAM_total*100)
        dataSend += str(int(RAM_free))
        dataSend += ","
        dataSend += str(RAM_per)
        #时间信息
        time0 = time.strftime("%H:%M")
        dataSend += ","
        dataSend += str(time0)
        #输出信息
        ser.write(dataSend)
        state = ""
        a=time.time()
        while state =="":
            state = ser.readline()
            if time.time()-a>3:
                state = "Error"
                break
        strftime=time.strftime("%Y年%m月%d日 %H:%M:%S")
        print "[",strftime,"]",
        content = "下载数据到Arduino"
        n = 40 - len(content)
        content += black[0:n]
        print content,
        if state == "ok":
            print "[状态:",UseStyle(state,fore = "green"),"]"
        else:
            print "[状态:",UseStyle(state,fore = "red"),"]"
        time.sleep(10)

def main():
    while True:#重启被意外关闭的线程
        global serFlag
        global yeeFlag
        serFlag = 1
        yeeFlag = 1
        #下载线程
        download = threading.Thread(target = download_data_to_arduino,args=())
        if download.isAlive() != True:
            try:
                download.start()
            except:
                strftime=time.strftime("%Y年%m月%d日 %H:%M:%S")
                print "[",strftime,"]",
                print UseStyle("串口无响应，10秒后重试",fore = "red")
                serFlag=0;
                time.sleep(10)
        #上传线程
        uploadYeelink = threading.Thread(target = upload_cpu_temp_to_yeelink,args=())
        if uploadYeelink.isAlive() != True:
            try:
                last_run_upload1 = upload_cpu_temp_to_yeelink()
            except:
                strftime=time.strftime("%Y年%m月%d日 %H:%M:%S")
                print "[",strftime,"]",
                print UseStyle("服务异常，10秒后重试",fore = "red")
                yeeFlag=0
                time.sleep(10)
        #重启串口
        if serFlag==0:
            break
            
                    

if __name__ == '__main__':
    last_cpu_time = time.time()-11
    cpu_out = 0
    while True:
        try:
            ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        except:
            ser = serial.Serial('/dev/ttyACM1', 9600, timeout=1)
        main()
    if serFlag==0:
        try:
             download.exit()
        except:
            time.sleep(1)
    if yeeFlag==0:
        try:
             uploadYeelink.exit()
        except:
            time.sleep(1)
