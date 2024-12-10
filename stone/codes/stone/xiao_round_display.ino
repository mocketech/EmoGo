#include "xiao_round_display.hpp"

Touch_XiaoRound::Touch_XiaoRound() {
  _cfg.x_min = _cfg.y_min = 0;
  _cfg.x_max = _cfg.y_max = 239;
  _cfg.i2c_addr = 0x2e;
}

bool Touch_XiaoRound::init() {
  if (isSPI()) {
    return false;
  }
  if (_cfg.pin_int >= 0) {
    lgfx::pinMode(_cfg.pin_int, lgfx::v1::pin_mode_t::input_pullup);
  }
  return lgfx::i2c::init(_cfg.i2c_port, _cfg.pin_sda, _cfg.pin_scl).has_value();
}

void Touch_XiaoRound::wakeup() {}
void Touch_XiaoRound::sleep() {}

uint_fast8_t Touch_XiaoRound::getTouchRaw(lgfx::v1::touch_point_t *tp, uint_fast8_t count) {
  tp[0].size = 0;
  tp[0].id = 0;
  if (_cfg.pin_int < 0) {
    return 0;
  }
  //FIXME:
  if ((bool)lgfx::gpio_in(_cfg.pin_int)) {
    ::delay(10);
    if ((bool)lgfx::gpio_in(_cfg.pin_int)) {
      return 0;
    }
  }
  uint8_t buf[5];
  if (!lgfx::i2c::transactionRead(_cfg.i2c_port, _cfg.i2c_addr, buf, 5, _cfg.freq).has_value()) {
    return 0;
  }
  if (buf[0] != 1) {
    return 0;
  }
  tp[0].x = buf[2];
  tp[0].y = buf[4];
  tp[0].size = 1;
  return 1;
}

XiaoRoundDisplay::XiaoRoundDisplay() {
  auto bus_cfg = _bus.config(); 
  bus_cfg.spi_host = 0; // for XIAO RP2040    
  bus_cfg.spi_mode = 0;
  bus_cfg.freq_write = 80000000;
  bus_cfg.freq_read  = 20000000;
  bus_cfg.pin_sclk = D8; // for XIAO RP2040
  bus_cfg.pin_mosi = D10; // for XIAO RP2040
  bus_cfg.pin_miso = D9; // for XIAO RP2040
  bus_cfg.pin_dc   = D3; // for XIAO RP2040
  _bus.config(bus_cfg);
  _panel.setBus(&_bus);

  auto panel_cfg = _panel.config();
  panel_cfg.pin_cs = D1; // for emo-go on XIAO RP2040
  panel_cfg.pin_rst = -1;
  panel_cfg.pin_busy = -1;
  panel_cfg.memory_width = 240;
  panel_cfg.memory_height = 240;
  panel_cfg.panel_width = 240;
  panel_cfg.panel_height = 240;
  panel_cfg.offset_x = 0;
  panel_cfg.offset_y = 0;
  panel_cfg.offset_rotation = 0;
  panel_cfg.dummy_read_pixel = 8;
  panel_cfg.dummy_read_bits  = 1;
  panel_cfg.readable = false;
  panel_cfg.invert = true;
  panel_cfg.rgb_order = false;
  panel_cfg.dlen_16bit = false;
  panel_cfg.bus_shared =  true;
  _panel.config(panel_cfg);

  auto light_cfg = _light.config();
  // light_cfg.pin_bl = D6; // for XIAO RP2040
  light_cfg.pin_bl = -1; // for emo-go on XIAO RP2040
  light_cfg.invert = false;
  light_cfg.freq = 44100;
  light_cfg.pwm_channel = 7;
  _light.config(light_cfg);
  _panel.setLight(&_light);

  /* Don't use the feature that tells where it touched
   * because emogo stone should be i2c slave but it foced to be i2c master.
  auto touch_cfg = _touch.config(); 
  touch_cfg.pin_int = D7; // for XIAO RP2040
  touch_cfg.i2c_port = 1; // for XIAO RP2040
  touch_cfg.pin_sda  = D4; // for XIAO RP2040
  touch_cfg.pin_scl  = D5; // for XIAO RP2040
  touch_cfg.freq = 400000;

  _touch.config(touch_cfg);
  _panel.setTouch(&_touch);
  */
  
  setPanel(&_panel);
}
