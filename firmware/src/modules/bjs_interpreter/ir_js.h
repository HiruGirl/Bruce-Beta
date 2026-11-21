#if !defined(DISABLE_INTERPRETER) && (!defined(LITE_VERSION) || defined(KEEP_JS))
#ifndef __IR_JS_H__
#define __IR_JS_H__

#include "helpers_js.h"

extern "C" {
JSValue native_irTransmitFile(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_irTransmit(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_irRead(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_irReadRaw(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
}

#endif
#endif
