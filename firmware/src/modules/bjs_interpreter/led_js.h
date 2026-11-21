#if !defined(DISABLE_INTERPRETER) && (!defined(LITE_VERSION) || defined(KEEP_JS))
#ifndef __LED_JS_H__
#define __LED_JS_H__

#include "helpers_js.h"

extern "C" {
JSValue native_ledSetColor(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_ledSetBrightness(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_ledOff(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_ledBlink(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
}

#endif
#endif
