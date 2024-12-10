#ifndef XIAO_ROUND_DISPLAY

#define XIAO_ROUND_DISPLAY
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

class Touch_XiaoRound : public lgfx::v1::ITouch {
  public:
  Touch_XiaoRound();
  bool init() override;
  void wakeup() override;
  void sleep() override;
  uint_fast8_t getTouchRaw(lgfx::v1::touch_point_t *tp, uint_fast8_t count) override;
};

class XiaoRoundDisplay : public lgfx::LGFX_Device {
  lgfx::Panel_GC9A01 _panel;
  lgfx::Bus_SPI _bus;
  lgfx::Light_PWM _light;
  Touch_XiaoRound _touch;

 public:
  XiaoRoundDisplay();
};

#endif //#ifndef XIAO_ROUND_DISPLAY
