from ._classes import *

# KEY

lib.IsKeyPressed.argtypes = [ctypes.c_int]
lib.IsKeyPressed.restype = ctypes.c_bool
def is_key_pressed(key):
    return lib.IsKeyPressed(key)

lib.IsKeyPressedRepeat.argtypes = [ctypes.c_int]
lib.IsKeyPressedRepeat.restype = ctypes.c_bool
def is_key_pressed_repeat(key):
    return lib.IsKeyPressedRepeat(key)

lib.IsKeyDown.argtypes = [ctypes.c_int]
lib.IsKeyDown.restype = ctypes.c_bool
def is_key_down(key):
    return lib.IsKeyDown(key)

lib.IsKeyReleased.argtypes = [ctypes.c_int]
lib.IsKeyReleased.restype = ctypes.c_bool
def is_key_released(key):
    return lib.IsKeyReleased(key)

lib.IsKeyUp.argtypes = [ctypes.c_int]
lib.IsKeyUp.restype = ctypes.c_bool
def is_key_up(key):
    return lib.IsKeyUp(key)

lib.GetKeyPressed.restype = ctypes.c_int
def get_key_pressed():
    return lib.GetKeyPressed()

lib.GetCharPressed.restype = ctypes.c_int
def get_char_pressed():
    "Get char pressed (unicode), call it multiple times"
    return lib.GetCharPressed()

lib.GetKeyName.argtypes = [ctypes.c_int]
lib.GetKeyName.restype = ctypes.c_char_p
def get_key_name(key):
    "Get name of a QWERTY key on the current keyboard layout (eg returns string 'q' for KEY_A on an AZERTY keyboard)"
    return lib.GetKeyName(key)

lib.SetExitKey.argtypes = [ctypes.c_int]
def set_exit_key(key):
    lib.SetExitKey(key)


# MOUSE

lib.IsMouseButtonPressed.argtypes = [ctypes.c_int]
lib.IsMouseButtonPressed.restype = ctypes.c_bool
def is_mouse_button_pressed(button):
    "Check if a mouse button has been pressed once"
    return lib.IsMouseButtonPressed(button)

lib.IsMouseButtonDown.argtypes = [ctypes.c_int]
lib.IsMouseButtonDown.restype = ctypes.c_bool
def is_mouse_button_down(button):
    "Check if a mouse button is being pressed"
    return lib.IsMouseButtonDown(button)

lib.IsMouseButtonReleased.argtypes = [ctypes.c_int]
lib.IsMouseButtonReleased.restype = ctypes.c_bool
def is_mouse_button_released(button):
    "Check if a mouse button has been released once"
    return lib.IsMouseButtonReleased(button)

lib.IsMouseButtonUp.argtypes = [ctypes.c_int]
lib.IsMouseButtonUp.restype = ctypes.c_bool
def is_mouse_button_up(button):
    "Check if a mouse button is NOT being pressed"
    return lib.IsMouseButtonUp(button)

lib.GetMouseX.restype = ctypes.c_int
def get_mouse_x():
    "Get mouse position X"
    return lib.GetMouseX()

lib.GetMouseY.restype = ctypes.c_int
def get_mouse_y():
    "Get mouse position Y"
    return lib.GetMouseY()

lib.GetMousePosition.restype = Vector2
def get_mouse_position():
    return lib.GetMousePosition()

lib.GetMouseDelta.restype = Vector2
def get_mouse_delta():
    "Get mouse delta between frames"
    return lib.GetMouseDelta()

lib.SetMousePosition.argtypes = [ctypes.c_int, ctypes.c_int]
def set_mouse_position(x, y):
    "Set mouse position XY"
    lib.SetMousePosition(x,y)

lib.SetMouseOffset.argtypes = [ctypes.c_int, ctypes.c_int]
def set_mouse_offset(offset_x, offset_y):
    "Set mouse offset"
    lib.SetMouseOffset(offset_x, offset_y)

lib.SetMouseScale.argtypes = [ctypes.c_float, ctypes.c_float]
def set_mouse_scale(scale_x, scale_y):
    "Set mouse scaling"
    lib.SetMouseScale(scale_x, scale_y)

lib.GetMouseWheelMove.restype = ctypes.c_float
def get_mouse_wheel_move():
    "Get mouse wheel movement for X or Y, whichever is larger"
    return lib.GetMouseWheelMove()

lib.GetMouseWheelMoveV.restype = Vector2
def get_mouse_wheel_move_v():
    "Get mouse wheel movement for both X and Y"
    return lib.GetMouseWheelMoveV()

lib.SetMouseCursor.argtypes = [ctypes.c_int]
def set_mouse_cursor(cursor):
    return lib.SetMouseCursor(cursor)

# touching dihhhh 🥀

lib.GetTouchX.restype = ctypes.c_int
def get_touch_x():
    "Get touch position X for touch point 0 (relative to screen size)"
    return lib.GetTouchX()

lib.GetTouchY.restype = ctypes.c_int
def get_touch_y():
    "Get touch position Y for touch point 0 (relative to screen size)"
    return lib.GetTouchY()

lib.GetTouchPosition.restype = Vector2
lib.GetTouchPosition.argtypes = [ctypes.c_int]
def get_touch_position(index):
    "Get touch position XY for a touch point index (relative to screen size)"
    return lib.GetTouchPosition(index)

lib.GetTouchPointId.restype = ctypes.c_int
lib.GetTouchPointId.argtypes = [ctypes.c_int]
def get_touch_point_id(index):
    "Get touch point identifier for given index"
    return lib.GetTouchPointId(index)

lib.GetTouchPointCount.restype = ctypes.c_int
def get_touch_point_count():
    "Get number of touch points"
    return lib.GetTouchPointCount()

# gesture

lib.SetGesturesEnabled.argtypes = [ctypes.c_uint]
def set_gestures_enabled(flags: int):
    "Enable a set of gestures using flags"
    lib.SetGesturesEnabled(flags)

lib.IsGestureDetected.argtypes = [ctypes.c_uint]
lib.IsGestureDetected.restype = ctypes.c_bool
def is_gesture_detected(gesture: int):
    "Check if a gesture have been detected"
    return lib.IsGestureDetected(gesture)

lib.GetGestureDetected.restype = ctypes.c_int
def get_gesture_detected():
    "Get latest detected gesture"
    return lib.GetGestureDetected()

lib.GetGestureHoldDuration.restype = ctypes.c_float
def get_gesture_hold_duration():
    "Get gesture hold time in seconds"
    return lib.GetGestureHoldDuration()

lib.GetGestureDragVector.restype = Vector2
def get_gesture_drag_vector():
    "Get gesture drag vector"
    return lib.GetGestureDragVector()

lib.GetGestureDragAngle.restype = ctypes.c_float
def get_gesture_drag_angle():
    "Get gesture drag angle"
    return lib.GetGestureDragAngle()

lib.GetGesturePinchVector.restype = Vector2
def get_gesture_pinch_vector():
    "Get gesture pinch delta"
    return lib.GetGesturePinchVector()

lib.GetGesturePinchAngle.restype = ctypes.c_float
def get_gesture_pinch_angle():
    "Get gesture pinch angle"
    return lib.GetGesturePinchAngle()


"""
RLAPI int GetGamepadButtonPressed(void);                      // Get the last gamepad button pressed
RLAPI int GetGamepadAxisCount(int gamepad);                   // Get axis count for a gamepad
RLAPI float GetGamepadAxisMovement(int gamepad, int axis);    // Get movement value for a gamepad axis
-- RLAPI int SetGamepadMappings(const char *mappings);           // Set internal gamepad mappings (SDL_GameControllerDB)
RLAPI void SetGamepadVibration(int gamepad, float leftMotor, float rightMotor, float duration); // Set gamepad vibration for both motors (duration in seconds)
"""
# gamepad

makeconnect("IsGamepadAvailable", [ctypes.c_int], ctypes.c_bool)
def is_gamepad_available(gamepad: int):
    "Check if a gamepad is available"
    return lib.IsGamepadAvailable(gamepad)

makeconnect("GetGamepadName", [ctypes.c_int], ctypes.c_char_p)
def get_gamepad_name(gamepad: int):
    "Get gamepad internal name id"
    return lib.GetGamepadName(gamepad)

makeconnect("IsGamepadButtonPressed", [c_int, c_int], c_bool) # Check if a gamepad button has been pressed once (gamepad button)
def is_gamepad_button_pressed(gamepad: int, button: int):
    "Check if a gamepad button has been pressed once"
    return lib.IsGamepadButtonPressed(gamepad, button)

makeconnect("IsGamepadButtonDown", [c_int, c_int], c_bool) # Check if a gamepad button is being pressed (gamepad button)
def is_gamepad_button_down(gamepad: int, button: int):
    "Check if a gamepad button is being pressed"
    return lib.IsGamepadButtonDown(gamepad, button)

makeconnect("IsGamepadButtonReleased", [c_int, c_int], c_bool) # Check if a gamepad button has been released once
def is_gamepad_button_released(gamepad: int, button: int):
    "Check if a gamepad button has been released once"
    return lib.IsGamepadButtonReleased(gamepad, button)

makeconnect("IsGamepadButtonUp", [c_int, c_int], c_bool) # Check if a gamepad button is NOT being pressed
def is_gamepad_button_up(gamepad: int, button: int):
    "Check if a gamepad button is NOT being pressed"
    return lib.IsGamepadButtonUp(gamepad, button)

makeconnect("GetGamepadButtonPressed", [], c_int)
def get_gamepad_button_pressed():
    "Get the last gamepad button pressed"
    return lib.GetGamepadButtonPressed()

makeconnect("GetGamepadAxisCount", [c_int], c_int)
def get_gamepad_axis_count(gamepad: int):
    return lib.GetGamepadAxisCount(gamepad)

makeconnect("GetGamepadAxisMovement", [c_int, c_int], c_float)
def get_gamepad_axis_movement(gamepad: int, axis: int):
    return lib.GetGamepadAxisMovement(gamepad, axis)

makeconnect("SetGamepadMappings", [c_char_p], c_int)
def set_gamepad_mappings(mappings: str):
    return lib.SetGamepadMappings(mappings.encode())

makeconnect("SetGamepadVibration", [c_int, c_float, c_float, c_float])
def set_gamepad_vibration(gamepad: int, left_motor: float, right_motor: float, duration: float):
    lib.SetGamepadVibration(gamepad, left_motor, right_motor, duration)

'''
RLAPI void ShowCursor(void);                                      // Shows cursor
RLAPI void HideCursor(void);                                      // Hides cursor
RLAPI bool IsCursorHidden(void);                                  // Check if cursor is not visible
RLAPI void EnableCursor(void);                                    // Enables cursor (unlock cursor)
RLAPI void DisableCursor(void);                                   // Disables cursor (lock cursor)
RLAPI bool IsCursorOnScreen(void);                                // Check if cursor is on the screen
'''

show_cursor = lib.ShowCursor
"Shows cursor"
hide_cursor = lib.HideCursor
"Hides cursor"

makeconnect("IsCursorHidden", [], c_bool)
def is_cursor_hidden()-> bool:
    "Check if cursor is not visible"
    return lib.IsCursorHidden()

enable_cursor = lib.EnableCursor 
"Enables cursor (unlock cursor)"

disable_cursor = lib.DisableCursor
"Disables cursor (lock cursor)"

makeconnect("IsCursorOnScreen", [], c_bool)
def is_cursor_on_screen()-> bool:
    "Check if cursor is on the screen"
    return lib.IsCursorOnScreen()

