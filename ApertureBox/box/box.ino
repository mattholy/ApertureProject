#include <Arduino.h>
#include <U8g2lib.h>

#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

U8G2_ST7920_128X64_F_SW_SPI u8g2(U8G2_R0, /* clock=*/ 13, /* data=*/ 11, /* CS=*/ 10, /* reset=*/ 8);

const int boxTempPin = 5;//机箱温度计
const int lowCtrl = 7;//5V继电器
const int highCtrl = 6;//220V继电器
volatile int highState = LOW;//高压继电器状态
String comdata="";
String a="";
int CPUTemp=0;
int RAM_free=0;
int RAM_per=0;
String time0;

void setup(void) {
  Serial.begin(9600);//主机通讯
  Serial.print("hello!");
  u8g2.begin();
  u8g2.enableUTF8Print();
  pinMode(lowCtrl, OUTPUT);
  digitalWrite(lowCtrl, HIGH);
  pinMode(highCtrl, OUTPUT);
  //digitalWrite(highCtrl, HIGH);为了安全不开机接通
  attachInterrupt(0,highVol,FALLING);
}

void loop(void) {
    if (Serial.available()){
    while (Serial.available()) {
      comdata += char(Serial.read());
      delay(2);
    }
    int cuPos = 0;
    int laPos = 0;
    cuPos = comdata.indexOf(",");
    CPUTemp=(comdata.substring(0,cuPos)).toInt();
    laPos = cuPos+1;
    cuPos = comdata.indexOf(",",cuPos+1);
    RAM_free=(comdata.substring(laPos,cuPos)).toInt();
    laPos = cuPos+1;
    cuPos = comdata.indexOf(",",cuPos+1);
    RAM_per=(comdata.substring(laPos,cuPos)).toInt();
    laPos = cuPos+1;
    cuPos = comdata.indexOf(",",cuPos+1);
    time0=(comdata.substring(laPos,cuPos));
    comdata="";
    Serial.print("ok");
  }
  u8g2.setFontDirection(0);
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_6x12_t_symbols);//7p
  u8g2.setCursor(0,7);
  u8g2.print(time0);
  u8g2.drawLine(0,9,128,9);
  u8g2.setFont(u8g2_font_6x12_t_symbols);  //8p
  u8g2.setCursor(0,19);
  u8g2.print("Core status: ");
  u8g2.setCursor(6,30);
  u8g2.print("Temp: ");
  u8g2.print(CPUTemp);
  u8g2.print("°C");
  u8g2.setCursor(6,40);
  u8g2.print("RAM: ");
  u8g2.drawFrame(30,33,50,7);
  u8g2.drawBox(30,33,RAM_per/2,7);
  u8g2.setCursor(85,40);
  u8g2.print( RAM_free);
  u8g2.print( "MB");
  u8g2.setCursor(0,50);
  u8g2.print( "Box Status:");
  u8g2.setCursor(6,61);
  int boxTemp = (125*analogRead(boxTempPin))>>8;
  u8g2.print("Temp: ");
  u8g2.print(boxTemp);
  u8g2.print("°C");
  u8g2.sendBuffer();
  delay(1000);
}

void highVol() {
  highState = ! highState;
  digitalWrite(highCtrl, highState);
}
