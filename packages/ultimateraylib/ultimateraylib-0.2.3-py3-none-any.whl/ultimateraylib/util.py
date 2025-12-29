from ._classes import *


'''
RLAPI void TakeScreenshot(const char *fileName);                  // Takes a screenshot of current screen (filename extension defines format)
RLAPI void SetConfigFlags(unsigned int flags);                    // Setup init configuration flags (view FLAGS)
RLAPI void OpenURL(const char *url);                              // Open URL with default system browser (if available)
'''

makeconnect("TakeScreenshot", [c_char_p])
def take_screenshot(file_name: str):
    lib.TakeScreenshot(file_name)

makeconnect("SetConfigFlags", [c_uint])
def set_config_flags(flags: int):
    lib.SetConfigFlags(flags)

makeconnect("OpenURL", [c_char_p])
def open_url(url: str):
    lib.OpenURL(url)

"""
RLAPI void TraceLog(int logLevel, const char *text, ...);         // Show trace log messages (LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR...)
RLAPI void SetTraceLogLevel(int logLevel);                        // Set the current threshold (minimum) log level
RLAPI void *MemAlloc(unsigned int size);                          // Internal memory allocator
RLAPI void *MemRealloc(void *ptr, unsigned int size);             // Internal memory reallocator
RLAPI void MemFree(void *ptr);                                    // Internal memory free
"""

makeconnect("TraceLog", [c_int, c_char_p])
def trace_log(log_level: int, text: str):
    lib.TraceLog(log_level, text.encode())

makeconnect("SetTraceLogLevel", [c_int])
def set_trace_log_level(log_level: int):
    lib.SetTraceLogLevel(log_level)

makeconnect("MemAlloc", [c_uint], c_void_p)
def mem_alloc(size: int):
    return lib.MemAlloc(size)

makeconnect("MemRealloc", [c_void_p, c_uint], c_void_p)
def mem_realloc(ptr, size: int):
    return lib.MemRealloc(ptr, size)

makeconnect("MemFree", [c_void_p])
def mem_free(ptr):
    lib.MemFree(ptr)

'''
RLAPI void SetTargetFPS(int fps);                                 // Set target FPS (maximum)
RLAPI float GetFrameTime(void);                                   // Get time in seconds for last frame drawn (delta time)
RLAPI double GetTime(void);                                       // Get elapsed time in seconds since InitWindow()
RLAPI int GetFPS(void);                                           // Get current FPS
'''

makeconnect("SetTargetFPS", [c_int])
def set_target_fps(fps: int):
    lib.SetTargetFPS(fps)

makeconnect("GetFrameTime", [], c_float)
def get_frame_time() -> float:
    return lib.GetFrameTime()

makeconnect("GetTime", [], c_double)
def get_time() -> float:
    return lib.GetTime()

makeconnect("GetFPS", [], c_int)
def get_fps() -> int:
    return lib.GetFPS()

