#if !defined(DISABLE_INTERPRETER) && (!defined(LITE_VERSION) || defined(KEEP_JS))
#ifndef __RUNTIME_JS_H__
#define __RUNTIME_JS_H__

#include "helpers_js.h"

extern "C" {
JSValue native_runtimeToBackground(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_runtimeToForeground(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_runtimeIsForeground(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_runtimeMain(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
}

#endif
#endif
