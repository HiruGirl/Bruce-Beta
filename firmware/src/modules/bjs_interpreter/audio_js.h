#if !defined(DISABLE_INTERPRETER) && (!defined(LITE_VERSION) || defined(KEEP_JS))
#ifndef __AUDIO_JS_H__
#define __AUDIO_JS_H__

#include "helpers_js.h"

extern "C" {
JSValue native_playAudioFile(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
JSValue native_tone(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv);
}

#endif
#endif
