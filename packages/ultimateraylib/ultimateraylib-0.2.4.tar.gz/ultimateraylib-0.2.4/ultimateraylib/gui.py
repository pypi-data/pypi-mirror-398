from ._classes import *
# gui

# int GuiButton(Rectangle bounds, const char *text)
lib.GuiButton.argtypes = [Rectangle, c_char_p]
lib.GuiButton.restype = ctypes.c_int
def gui_button(bounds: Rectangle, text:str):
    return bool(lib.GuiButton(bounds, text.encode()))

# int GuiMessageBox(Rectangle bounds, const char *title, const char *message, const char *buttons)
makeconnect("GuiMessageBox", [Rectangle, c_char_p, c_char_p, c_char_p], c_int)
def gui_message_box(bounds, title, message, buttons):
    return lib.GuiMessageBox(bounds, title, message, buttons)

'''
RAYGUIAPI int GuiDropdownBox(Rectangle bounds, const char *text, int *active, bool editMode);          // Dropdown Box control


RAYGUIAPI int GuiSpinner(Rectangle bounds, const char *text, int *value, int minValue, int maxValue, bool editMode); // Spinner control

RAYGUIAPI int GuiValueBox(Rectangle bounds, const char *text, int *value, int minValue, int maxValue, bool editMode); // Value Box control, updates input text with numbers

RAYGUIAPI int GuiValueBoxFloat(Rectangle bounds, const char *text, char *textValue, float *value, bool editMode); // Value box control for float values

RAYGUIAPI int GuiTextBox(Rectangle bounds, char *text, int textSize, bool editMode);                   // Text Box control, updates input text

RAYGUIAPI int GuiSlider(Rectangle bounds, const char *textLeft, const char *textRight, float *value, float minValue, float maxValue); // Slider control
RAYGUIAPI int GuiSliderBar(Rectangle bounds, const char *textLeft, const char *textRight, float *value, float minValue, float maxValue); // Slider Bar control
RAYGUIAPI int GuiProgressBar(Rectangle bounds, const char *textLeft, const char *textRight, float *value, float minValue, float maxValue); // Progress Bar control
RAYGUIAPI int GuiStatusBar(Rectangle bounds, const char *text);                                        // Status Bar control, shows info text

RAYGUIAPI int GuiDummyRec(Rectangle bounds, const char *text);                                         // Dummy control for placeholders
RAYGUIAPI int GuiGrid(Rectangle bounds, const char *text, float spacing, int subdivs, Vector2 *mouseCell); // Grid control
'''

makeconnect("GuiDropdownBox", [Rectangle, c_char_p, POINTER(c_int), c_bool], c_int)
def gui_dropdown_box(bounds: Rectangle, text: str, active: int, edit_mode: bool):
    dad = c_int(active)
    lib.GuiDropdownBox(bounds, text, byref(dad), edit_mode)
    return dad.value

makeconnect("GuiSpinner", [Rectangle, c_char_p, POINTER(c_int), c_int, c_int, c_bool], c_int)
def gui_spinner(bounds, text, value: int, min_value, max_value, edit_mode):
    dad = c_int(value)
    lib.GuiSpinner(bounds, text, byref(dad), min_value, max_value, edit_mode)
    return dad.value

makeconnect("GuiValueBox", [Rectangle, c_char_p, POINTER(c_int), c_int, c_int, c_bool], c_int)
def gui_value_box(bounds: Rectangle, text: str, value: int, min_value: int, max_value: int, edit_mode: bool):
    dad = c_int(value)
    lib.GuiValueBox(bounds, text, byref(dad), min_value, max_value, edit_mode)
    return dad.value

makeconnect("GuiValueBoxFloat", [Rectangle, c_char_p, c_char_p, POINTER(c_float), c_bool], c_int)
def gui_value_box_float(bounds: Rectangle, text: str, text_value: str, value: float, edit_mode: bool):
    dad = c_float(value)
    lib.GuiValueBoxFloat(bounds, text, text_value, byref(dad), edit_mode)
    return dad.value

makeconnect("GuiTextBox", [Rectangle, c_char_p, c_int, c_bool], c_int)
def gui_text_box(bounds: Rectangle, text: str, text_size: int, edit_mode: bool) -> tuple[bool, str]:
    # Create a buffer of the right size
    buf = create_string_buffer(text.encode(), text_size)
    caret = lib.GuiTextBox(bounds, buf, text_size, edit_mode)
    return bool(caret), buf.value.decode()  # Return caret and updated string

makeconnect("GuiSlider", [Rectangle, c_char_p, c_char_p, POINTER(c_float), c_float, c_float], c_int)
def gui_slider(bounds: Rectangle, text_left: str, text_right: str, value: float, min_value: float, max_value: float) -> tuple[float, int]:
    skibiidi = c_float(value)
    da = lib.GuiSlider(bounds, text_left.encode(), text_right.encode(), byref(skibiidi), min_value, max_value)
    return skibiidi.value, da

makeconnect("GuiSliderBar", [Rectangle, c_char_p, c_char_p, POINTER(c_float), c_float, c_float], c_int)
def gui_slider_bar(bounds: Rectangle, text_left: str, text_right: str, value: float, min_value: float, max_value: float) -> tuple[float, int]:
    skibiidi = c_float(value)
    da = lib.GuiSliderBar(bounds, text_left.encode(), text_right.encode(), byref(skibiidi), min_value, max_value)
    return skibiidi.value, da

makeconnect("GuiProgressBar", [Rectangle, c_char_p, c_char_p, POINTER(c_float), c_float, c_float], c_int)
def gui_progress_bar(bounds: Rectangle, text_left: str, text_right: str, value: float, min_value: float, max_value: float) -> tuple[float, int]:
    skibiidi = c_float(value)
    da = lib.GuiProgressBar(bounds, text_left.encode(), text_right.encode(), byref(skibiidi), min_value, max_value)
    return skibiidi.value, da

makeconnect("GuiStatusBar", [Rectangle, c_char_p], c_int)
def gui_status_bar(bounds: Rectangle, text: str) -> int:
    return lib.GuiStatusBar(bounds, text.encode())

makeconnect("GuiDummyRec", [Rectangle, c_char_p], c_int)
def gui_dummy_rec(bounds: Rectangle, text: str) -> int:
    return lib.GuiDummyRec(bounds, text.encode())

'''
// Global gui state control functions
RAYGUIAPI void GuiEnable(void);                                 // Enable gui controls (global state)
RAYGUIAPI void GuiDisable(void);                                // Disable gui controls (global state)
RAYGUIAPI void GuiLock(void);                                   // Lock gui controls (global state)
RAYGUIAPI void GuiUnlock(void);                                 // Unlock gui controls (global state)

RAYGUIAPI bool GuiIsLocked(void);                               // Check if gui is locked (global state)
RAYGUIAPI void GuiSetAlpha(float alpha);                        // Set gui controls alpha (global state), alpha goes from 0.0f to 1.0f
RAYGUIAPI void GuiSetState(int state);                          // Set gui state (global state)
RAYGUIAPI int GuiGetState(void);                                // Get gui state (global state)

// Font set/get functions
RAYGUIAPI void GuiSetFont(Font font);                           // Set gui custom font (global state)
RAYGUIAPI Font GuiGetFont(void);                                // Get gui custom font (global state)

// Style set/get functions
RAYGUIAPI void GuiSetStyle(int control, int property, int value); // Set one style property
RAYGUIAPI int GuiGetStyle(int control, int property);           // Get one style property

// Styles loading functions
RAYGUIAPI void GuiLoadStyle(const char *fileName);              // Load style file over global style variable (.rgs)
RAYGUIAPI void GuiLoadStyleDefault(void);                       // Load style default over global style
'''

gui_enable = lib.GuiEnable
gui_disable = lib.GuiDisable
gui_lock = lib.GuiLock
gui_unlock = lib.GuiUnlock

makeconnect("GuiIsLocked", [], c_bool)
def gui_is_locked() -> bool:
    return lib.GuiIsLocked()

makeconnect("GuiSetAlpha", [c_float])
def gui_set_alpha(alpha: float):
    lib.GuiSetAlpha(alpha)

makeconnect("GuiSetState", [c_int])
def gui_set_state(state: int):
    lib.GuiSetState(state)

makeconnect("GuiGetState", [], c_int)
def gui_get_state() -> int:
    return lib.GuiGetState()

makeconnect("GuiSetFont", [Font])
def gui_set_font(font: Font):
    lib.GuiSetFont(font)

makeconnect("GuiGetFont", [], Font)
def gui_get_font() -> Font:
    return lib.GuiGetFont()

makeconnect("GuiSetStyle", [c_int, c_int, c_int])
def gui_set_style(control: int, property: int, value: int):
    lib.GuiSetStyle(control, property, value)

makeconnect("GuiGetStyle", [c_int, c_int], c_int)
def gui_get_style(control: int, property: int) -> int:
    return lib.GuiGetStyle(control, property)

makeconnect("GuiLoadStyle", [c_char_p])
def gui_load_style(file_name: str):
    lib.GuiLoadStyle(file_name.encode())

gui_load_style_default = lib.GuiLoadStyleDefault

'''
// Tooltips management functions
RAYGUIAPI void GuiEnableTooltip(void);                          // Enable gui tooltips (global state)
RAYGUIAPI void GuiDisableTooltip(void);                         // Disable gui tooltips (global state)

RAYGUIAPI void GuiSetTooltip(const char *tooltip);              // Set tooltip string

// Icons functionality
RAYGUIAPI const char *GuiIconText(int iconId, const char *text); // Get text with icon id prepended (if supported)

#if !defined(RAYGUI_NO_ICONS)
RAYGUIAPI void GuiSetIconScale(int scale);                      // Set default icon drawing size
RAYGUIAPI unsigned int *GuiGetIcons(void);                      // Get raygui icons data pointer
RAYGUIAPI char **GuiLoadIcons(const char *fileName, bool loadIconsName); // Load raygui icons file (.rgi) into internal icons data
RAYGUIAPI void GuiDrawIcon(int iconId, int posX, int posY, int pixelSize, Color color); // Draw icon using pixel size at specified position
#endif

// Utility functions
RAYGUIAPI int GuiGetTextWidth(const char *text);                // Get text width considering gui style and icon size (if required)
'''

gui_enable_tooltip = lib.GuiEnableTooltip
gui_disable_tooltip = lib.GuiDisableTooltip

makeconnect("GuiSetTooltip", [c_char_p])


makeconnect("GuiIconText", [c_int, c_char_p], c_char_p)


