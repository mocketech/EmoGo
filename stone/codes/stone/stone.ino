#include <Wire.h>

#include "xiao_round_display.hpp"
#include "data/dead_blink.h"
#include "data/dead_black.h"
#include "data/dead_white.h"
#include "data/defensive_blink.h"
#include "data/defensive_black.h"
#include "data/defensive_white.h"
#include "data/normal_blink.h"
#include "data/normal_black.h"
#include "data/normal_white.h"
#include "data/offensive_blink.h"
#include "data/offensive_black.h"
#include "data/offensive_white.h"

const uint8_t *image[][4] = { 
  { 
    dead_blink_png, defensive_blink_png, normal_blink_png, offensive_blink_png,
  }, {
    dead_black_png, defensive_black_png, normal_black_png, offensive_black_png,
  }, {
    dead_white_png, defensive_white_png, normal_white_png, offensive_white_png,
  }
};

const uint32_t image_len[][4] = {
  {
    dead_blink_png_len, defensive_blink_png_len, normal_blink_png_len, offensive_blink_png_len, 
  }, {
    dead_black_png_len, defensive_black_png_len, normal_black_png_len, offensive_black_png_len,
  }, {
    dead_white_png_len, defensive_white_png_len, normal_white_png_len, offensive_white_png_len,    
  }
};

XiaoRoundDisplay display;
LGFX_Sprite sprite_main( &display), sprite_blink( &display);

// 碁石の色
#define STONE_BLINK 0
#define STONE_BLACK 1
#define STONE_WHITE 2


// 碁石の表情
#define STONE_DEAD      0
#define STONE_DEFENSIVE 1
#define STONE_NORMAL    2
#define STONE_OFFENSIVE 3

// 碁石の向き
#define STONE_NORTH 0
#define STONE_EAST  90
#define STONE_SOUTH 180
#define STONE_WEST  270

// 碁石の状態
uint32_t stone_color = STONE_BLACK;
uint32_t stone_emotion = STONE_NORMAL;
uint32_t stone_direction = STONE_NORTH;
bool    stone_blink_state = false;
bool    stone_blink_expression = false;

// 外部通信定義
#define STONE_PWR D0
#define STONE_INT D2
#define TOUCH_INT D7
#define I2C_ADDR 0x8
uint8_t i2c_rxbuf[ 5] = { 0x00, 0x00, 0x00, 0x00, 0x00};
uint8_t i2c_txbuf[ 2] = { 0x00, 0x00};
bool i2c_recv_interrupted = false;
bool i2c_send_interrupted = false;
bool touch_interrupted = false;
uint32_t touch_timer = 0;

#define SET_STATE     1
#define SET_BLINK     2
#define BLINK         3

HardwareSerial *uart;

void receiveEvent( int num) {
  i2c_recv_interrupted = true;
  uart->println( "enter receiveEvent function.");
  
  for ( uint32_t i = 0; Wire.available(); i++) {
    if ( i < 5) i2c_rxbuf[ i] = Wire.read();
    else Wire.read();
  }
}

void sendEvent() {
  i2c_send_interrupted = true;
  
  for ( uint32_t i = 0; i < 2; i++) {
    Wire.write( i2c_txbuf[ i]);
  }
}

void touchEvent() {
  if ( touch_timer < millis()) {
    digitalWrite( STONE_INT, LOW);
    uart->println( "Touch Event " + String(millis()));
    touch_timer = millis() + 100;
  } else {
    digitalWrite( STONE_INT, HIGH);
  }
}

void setup() {
  uart = &Serial;
  //uart = &Serial1;
  
  uart->begin( 9600);
  delay( 1000);
  uart->println( "start:");

  // I2C settings
  Wire.begin( I2C_ADDR);
  //pinMode( SDA, INPUT);
  //pinMode( SCL, INPUT);
  Wire.onReceive( receiveEvent);
  Wire.onRequest( sendEvent);
  uart->println( "I2C settings done.");

  // Notify power and touch
  pinMode( STONE_PWR, OUTPUT);
  digitalWrite( STONE_PWR, LOW);
  pinMode( STONE_INT, OUTPUT);
  digitalWrite( STONE_INT, HIGH);
  pinMode( TOUCH_INT, INPUT_PULLUP);
  attachInterrupt( TOUCH_INT, touchEvent, FALLING);
  
  // Display settings
  display.init();
  sprite_main.createSprite( 120, 120);
  sprite_blink.createSprite( 120, 120);
  
  //sprite_main.drawPng( image[ stone_color][ stone_emotion], image_len[ stone_color][ stone_emotion], 0, 0);
  //sprite_blink.drawPng( image[ STONE_BLINK][ stone_emotion], image_len[ STONE_BLINK][ stone_emotion], 0, 0);
  
  display.startWrite();
  display.clear();
  //sprite_main.pushRotateZoom( 0, 2, 2);
  display.endWrite();
}

void loop() {
  String dbgMsg;
  
  if ( i2c_recv_interrupted) {
    i2c_recv_interrupted = false;
    dbgMsg = "command, parameters = " + String( i2c_rxbuf[ 0], HEX);
    for ( uint32_t i = 1; i <= 4; i++) {
      dbgMsg += ", " + String( i2c_rxbuf[ i], HEX); 
    }
    uart->println( dbgMsg);
        
    switch ( i2c_rxbuf[ 0]) {
      case SET_STATE:
      stone_color = i2c_rxbuf[ 1];
      stone_emotion = i2c_rxbuf[ 2];
      stone_direction = (uint32_t)i2c_rxbuf[ 3] * 256 + i2c_rxbuf[ 4];
      uart->println( String(stone_color)+" "+String(stone_emotion)+" "+String(stone_direction));
      break;
      
      case SET_BLINK:
      stone_blink_state = ( i2c_rxbuf[ 1] != 0x00) ? true : false;
      stone_blink_expression = false;
      break;
      
      case BLINK:
      if ( stone_blink_state) stone_blink_expression = ( i2c_rxbuf[ 1] != 0x00) ? true : false;
      else stone_blink_expression = false;
      break;
    }

    if ( stone_blink_state) {
      display.startWrite();
      if ( stone_blink_expression) sprite_blink.pushRotateZoom( stone_direction, 2.0, 2.0);
      else sprite_main.pushRotateZoom( stone_direction, 2.0, 2.0);
      display.endWrite();
      
    } else {
      sprite_main.drawPng( image[ stone_color][ stone_emotion], image_len[ stone_color][ stone_emotion], 0, 0);
      sprite_blink.drawPng( image[ STONE_BLINK][ stone_emotion], image_len[ STONE_BLINK][ stone_emotion], 0, 0);
      display.startWrite();
      sprite_main.pushRotateZoom( stone_direction, 2.0, 2.0);
      display.endWrite();
    }
  }

  if ( touch_interrupted) {
    touch_interrupted = false;
  }
}
