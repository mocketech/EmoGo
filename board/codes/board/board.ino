// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8<
// 情碁 - 碁盤 (Board2 ver.)
// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8<

// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8<
// 注意事項：
// * Stone2はD2が使える。Stone:D2-->Board:D2
// * Stone3はD0,D2が使える。Stone:D0-->Board:D2, Stone:D2-->Board:D3
// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8<

// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8< 
// 以下のことを行う。
// * CANからID:CAN_ORDERの2byteのメッセージを受け取り、1byte目がSET_EMOTIONだったら、2byte目をI2CでSTONEに通知する。
// * CANからID:CAN_ORDERの2byteのメッセージを受け取り、1byte目がSET_BLINKだったら、点滅の状態を以下のように変更
//   * 2byte目が0ならblink_state = false
//   * それ以外ならblink_state = true
// * CANからID:CAN_BLINKの1byteのメッセージを受け取り、かつ、blink_state==trueなら、STONEに点滅指示をする。
//   * メッセージが0ならノーマル表示を通知
//   * それ以外なら色付き表示を通知
// * D2ピンが100ms以上HIGHなら、CANに脱着(NOTIFY_DETACH)を示すメッセージをID:CAN_NOTIFYで送る。
// * D2ピンがLOWなら、CANに装着(NOTIFY_ATTACH)を示すメッセージをID:CAN_NOTIFYに送る。
// * D2ピンが100ms未満でHIGHだったなら、CANに点滅要求(NOTIFY_BLINK)を示すメッセージをID:CAN_NOTIFYで送る。
// ----- 8< ----- 8< ----- 8< ----- 8< ----- 8< 

#include <mcp_can.h>
#include <SPI.h>
#include <Wire.h>
//#include "unique-id.h"
//#include "emogo.h"

#define UNIQID           0x22
#define CAN_MASK         0x07FF0000
#define CAN_ORDER        (0x0400 + UNIQID)
#define CAN_BLINK        0x01FF
#define CAN_NOTIFY       (0x0600 + UNIQID)

#define NOTIFY_ATTACH    0x1
#define NOTIFY_DETACH    0x0
#define NOTIFY_TOUCH     0x2
#define CAN_CS           D1
#define CAN_INT          D0

#define STONE_I2C_ADDR   0x8
#define STONE_INT        D3
#define STONE_ATTACH     D2

MCP_CAN CAN0( CAN_CS);

bool can_interrupted = false;
bool stone_touch_interrupted = false;
bool stone_attach_interrupted = false;
uint32_t touch_timer = 0;
uint32_t attach_timer = 0;
bool stone_attached = false;

HardwareSerial *uart;

void can_interrupt( void) {
  can_interrupted = true;
}

void stone_touch_interrupt( void) {
  if ( ! stone_attached) return;
  
  if ( touch_timer < millis()) {
    stone_touch_interrupted = true;
    touch_timer = millis() + 500;
  }
}

void stone_attach_interrupt( void) {
    stone_attach_interrupted = true;
}

uint8_t i2cSend( uint8_t addr, uint8_t* buf, uint32_t len) {
  Wire.beginTransmission( addr);
  for ( uint32_t i = 0; i < len; i++) {
    Wire.write( buf[ i]);
  }
  return Wire.endTransmission();
}

void setup() {
  uart = &Serial;
  //uart = &Serial1;
  
  uart->begin( 9600);
  delay( 5000);
  uart->println( "Starting Emo Go Board module.");
  
  pinMode( CAN_INT, INPUT_PULLUP); // Setting pin xx for ^INT input from CAN
  pinMode( STONE_INT, INPUT_PULLUP); // Setting pin xx fo ^INT input from STONE
  pinMode( STONE_ATTACH, INPUT_PULLUP);
  

  attachInterrupt( CAN_INT, can_interrupt, FALLING);
  attachInterrupt( STONE_INT, stone_touch_interrupt, FALLING);
  attachInterrupt( STONE_ATTACH, stone_attach_interrupt, CHANGE);
  
  if ( CAN0.begin( MCP_STD, CAN_500KBPS, MCP_20MHZ) == CAN_OK) uart->println( "MCP2515 initialized.");
  else uart->println( "MCP2515 init failed.");
  
  CAN0.init_Mask( 0, 0, CAN_MASK);
  CAN0.init_Filt( 0, 0, CAN_ORDER * 0x10000);  // システムからの指示、感情変更、点滅状態
  CAN0.init_Filt( 1, 0, CAN_BLINK * 0x10000);  // 点滅指示

  CAN0.init_Mask( 1, 0, CAN_MASK);
  CAN0.init_Filt( 2, 0, 0x00000000);
  CAN0.init_Filt( 3, 0, 0x00000000);
  CAN0.init_Filt( 4, 0, 0x00000000);
  CAN0.init_Filt( 5, 0, 0x00000000);
  CAN0.init_Filt( 6, 0, 0x00000000);
  
  uart->println( "Done to set filters on MCP2515.");
  CAN0.setMode( MCP_NORMAL);

  Wire.begin();
  //pinMode( SDA, INPUT);
  //pinMode( SCL, INPUT);
  uart->println( "I2C initialized.");
}

void loop() {
  uint32_t canId;
  uint8_t len = 0;
  uint8_t canBuf[ 8];
  uint8_t i2cBuf[ 3];
  uint8_t res;
  
  if ( can_interrupted) {   // システムからのアクション・CANからメッセージが来たら
    can_interrupted = false;
    res = CAN0.readMsgBuf( &canId, &len, canBuf);
    uart->print( String( canId, HEX));
    for ( uint32_t i = 0; i < len; i++) {
      i2cBuf[ i] = canBuf[ i];
      uart->print( ", " + String( canBuf[ i], HEX));
    }
    uart->println();

    i2cSend( STONE_I2C_ADDR, i2cBuf, len);
  }

  // 碁石が装着・脱着されたら
  if ( stone_attach_interrupted) {
    stone_attach_interrupted = false;
    attach_timer = millis() + 500;
  }

  // 碁石の装着・脱着を検知してから500ms後に装着・脱着を判定
  if ( attach_timer != 0 && attach_timer < millis()) { 
    attach_timer = 0;
    if ( ! stone_attached && digitalRead( STONE_ATTACH) == LOW) {
      stone_attached = true;
      canBuf[ 0] = NOTIFY_ATTACH;
      res = CAN0.sendMsgBuf( CAN_NOTIFY, 0, 1, canBuf);
      uart->println( "Attach");
    } if ( stone_attached && digitalRead( STONE_ATTACH) == HIGH) {
      stone_attached = false;
      canBuf[ 0] = NOTIFY_DETACH;
      res = CAN0.sendMsgBuf( CAN_NOTIFY, 0, 1, canBuf);
      uart->println( "Detach");
    }
  }
 
  // 碁石がタッチされたら
  if ( stone_touch_interrupted) {
    stone_touch_interrupted = false;
    if ( stone_attached) {
      canBuf[ 0] = NOTIFY_TOUCH;
      res = CAN0.sendMsgBuf( CAN_NOTIFY, 0, 1, canBuf);
      uart->println( "Touch");
    }
  }  

  //delay( 10);
}
