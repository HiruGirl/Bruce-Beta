#if !defined(DISABLE_INTERPRETER) && (!defined(LITE_VERSION) || defined(KEEP_JS))
#ifndef __NOTIFICATION_JS_H__
#define __NOTIFICATION_JS_H__

#include "helpers_js.h"

extern "C" {
JSValue native_notifyBlink(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
}

#endif
#endif
