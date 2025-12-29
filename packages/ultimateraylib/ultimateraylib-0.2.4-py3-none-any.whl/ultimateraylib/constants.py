from ._classes import *
'''
#define LIGHTGRAY  CLITERAL(Color){ 200  200  200  255 }   # Light Gray
#define GRAY       CLITERAL(Color){ 130  130  130  255 }   # Gray
#define DARKGRAY   CLITERAL(Color){ 80  80  80  255 }      # Dark Gray
#define YELLOW     CLITERAL(Color){ 253  249  0  255 }     # Yellow
#define GOLD       CLITERAL(Color){ 255  203  0  255 }     # Gold
#define ORANGE     CLITERAL(Color){ 255  161  0  255 }     # Orange
#define PINK       CLITERAL(Color){ 255  109  194  255 }   # Pink
#define RED        CLITERAL(Color){ 230  41, 55, 255 }     # Red
#define MAROON     CLITERAL(Color){ 190, 33, 55, 255 }     # Maroon

#define GREEN      CLITERAL(Color){ 0, 228, 48, 255 }      # Green

#define LIME       CLITERAL(Color){ 0, 158, 47, 255 }      # Lime
#define DARKGREEN  CLITERAL(Color){ 0, 117, 44, 255 }      # Dark Green

#define SKYBLUE    CLITERAL(Color){ 102, 191, 255, 255 }   # Sky Blue
#define BLUE       CLITERAL(Color){ 0, 121, 241, 255 }     # Blue
#define DARKBLUE   CLITERAL(Color){ 0, 82, 172, 255 }      # Dark Blue

#define PURPLE     CLITERAL(Color){ 200, 122, 255, 255 }   # Purple
#define VIOLET     CLITERAL(Color){ 135, 60, 190, 255 }    # Violet
#define DARKPURPLE CLITERAL(Color){ 112, 31, 126, 255 }    # Dark Purple

#define BEIGE      CLITERAL(Color){ 211, 176, 131, 255 }   # Beige
#define BROWN      CLITERAL(Color){ 127, 106, 79, 255 }    # Brown
#define DARKBROWN  CLITERAL(Color){ 76, 63, 47, 255 }      # Dark Brown

#define WHITE      CLITERAL(Color){ 255, 255, 255, 255 }   # White
#define BLACK      CLITERAL(Color){ 0, 0, 0, 255 }         # Black
#define BLANK      CLITERAL(Color){ 0, 0, 0, 0 }           # Blank (Transparent)
#define MAGENTA    CLITERAL(Color){ 255, 0, 255, 255 }     # Magenta
#define RAYWHITE   CLITERAL(Color){ 245, 245, 245, 255 }   # My own White (raylib logo)
'''


# colors

LIGHTGRAY = make_color(200, 200, 200, 255)
GRAY = make_color(130, 130, 130, 255)
DARKGRAY = make_color(80, 80, 80, 255)
YELLOW = make_color(253, 249, 0, 255)
GOLD = make_color(255, 203, 0, 255)
ORANGE = make_color(255, 161, 0, 255)
RED = make_color(230, 41, 55, 255)
MAROON = make_color(190, 33, 55, 255)

GREEN = make_color(0, 228, 48, 255)
LIME = make_color(0, 158, 47, 255)
DARKGREEN = make_color(0, 117, 44, 255)

SKYBLUE = make_color(102, 191, 255, 255)
BLUE = make_color(0, 121, 241, 255)
DARKBLUE = make_color(0, 82, 172, 255)

PURPLE = make_color(200, 122, 255, 255)
VIOLET = make_color(135, 60, 190, 255)
DARKPURPLE = make_color(112, 31, 126, 255)

BEIGE = make_color(211, 176, 131, 255)
BROWN = make_color(127, 106, 79, 255)
DARKBROWN = make_color(76, 63, 47, 255)

WHITE = make_color(255, 255, 255, 255)
BLACK = make_color(0, 0, 0, 255)
BLANK = make_color(0, 0, 0, 0)
MAGENTA = make_color(255, 0, 255, 255)
RAYWHITE = make_color(245, 245, 245, 255)



# keys

KEY_NULL= 0 # Key: NULL, used for no key pressed
# Alphanumeric keys
KEY_APOSTROPHE  = 39    # Key: '
KEY_COMMA   = 44    # Key: ,
KEY_MINUS   = 45    # Key: -
KEY_PERIOD  = 46    # Key: .
KEY_SLASH   = 47    # Key: /
KEY_ZERO= 48    # Key: 0
KEY_ONE = 49    # Key: 1
KEY_TWO = 50    # Key: 2
KEY_THREE   = 51    # Key: 3
KEY_FOUR= 52    # Key: 4
KEY_FIVE= 53    # Key: 5
KEY_SIX = 54    # Key: 6
KEY_SEVEN   = 55    # Key: 7
KEY_EIGHT   = 56    # Key: 8
KEY_NINE= 57    # Key: 9
KEY_SEMICOLON   = 59    # Key: ;
KEY_EQUAL   = 61    # Key: =
KEY_A   = 65    # Key: A | a
KEY_B   = 66    # Key: B | b
KEY_C   = 67    # Key: C | c
KEY_D   = 68    # Key: D | d
KEY_E   = 69    # Key: E | e
KEY_F   = 70    # Key: F | f
KEY_G   = 71    # Key: G | g
KEY_H   = 72    # Key: H | h
KEY_I   = 73    # Key: I | i
KEY_J   = 74    # Key: J | j
KEY_K   = 75    # Key: K | k
KEY_L   = 76    # Key: L | l
KEY_M   = 77    # Key: M | m
KEY_N   = 78    # Key: N | n
KEY_O   = 79    # Key: O | o
KEY_P   = 80    # Key: P | p
KEY_Q   = 81    # Key: Q | q
KEY_R   = 82    # Key: R | r
KEY_S   = 83    # Key: S | s
KEY_T   = 84    # Key: T | t
KEY_U   = 85    # Key: U | u
KEY_V   = 86    # Key: V | v
KEY_W   = 87    # Key: W | w
KEY_X   = 88    # Key: X | x
KEY_Y   = 89    # Key: Y | y
KEY_Z   = 90    # Key: Z | z
KEY_LEFT_BRACKET= 91    # Key: [
KEY_BACKSLASH   = 92    # Key: '\'
KEY_RIGHT_BRACKET   = 93    # Key: ]
KEY_GRAVE   = 96   # Key: `
# Function keys
KEY_SPACE   = 32   # Key: Space
KEY_ESCAPE  = 256  # Key: Esc
KEY_ENTER   = 257  # Key: Enter
KEY_TAB = 258   # Key: Tab
KEY_BACKSPACE   = 259   # Key: Backspace
KEY_INSERT  = 260   # Key: Ins
KEY_DELETE  = 261   # Key: Del
KEY_RIGHT   = 262   # Key: Cursor right
KEY_LEFT= 263   # Key: Cursor left
KEY_DOWN= 264   # Key: Cursor down
KEY_UP  = 265   # Key: Cursor up
KEY_PAGE_UP = 266   # Key: Page up
KEY_PAGE_DOWN   = 267   # Key: Page down
KEY_HOME= 268   # Key: Home
KEY_END = 269   # Key: End
KEY_CAPS_LOCK   = 280   # Key: Caps lock
KEY_SCROLL_LOCK = 281   # Key: Scroll down
KEY_NUM_LOCK= 282   # Key: Num lock
KEY_PRINT_SCREEN= 283   # Key: Print screen
KEY_PAUSE   = 284   # Key: Pause
KEY_F1  = 290   # Key: F1
KEY_F2  = 291   # Key: F2
KEY_F3  = 292   # Key: F3
KEY_F4  = 293   # Key: F4
KEY_F5  = 294   # Key: F5
KEY_F6  = 295   # Key: F6
KEY_F7  = 296   # Key: F7
KEY_F8  = 297   # Key: F8
KEY_F9  = 298   # Key: F9
KEY_F10 = 299   # Key: F10
KEY_F11 = 300   # Key: F11
KEY_F12 = 301   # Key: F12
KEY_LEFT_SHIFT  = 340   # Key: Shift left
KEY_LEFT_CONTROL= 341   # Key: Control left
KEY_LEFT_ALT= 342   # Key: Alt left
KEY_LEFT_SUPER  = 343   # Key: Super left
KEY_RIGHT_SHIFT = 344   # Key: Shift right
KEY_RIGHT_CONTROL   = 345   # Key: Control right
KEY_RIGHT_ALT   = 346   # Key: Alt right
KEY_RIGHT_SUPER = 347   # Key: Super right
KEY_KB_MENU = 348   # Key: KB menu
# Keypad keys
KEY_KP_0= 320   # Key: Keypad 0
KEY_KP_1= 321   # Key: Keypad 1
KEY_KP_2= 322   # Key: Keypad 2
KEY_KP_3= 323   # Key: Keypad 3
KEY_KP_4= 324   # Key: Keypad 4
KEY_KP_5= 325   # Key: Keypad 5
KEY_KP_6= 326   # Key: Keypad 6
KEY_KP_7= 327   # Key: Keypad 7
KEY_KP_8= 328   # Key: Keypad 8
KEY_KP_9= 329   # Key: Keypad 9
KEY_KP_DECIMAL  = 330   # Key: Keypad .
KEY_KP_DIVIDE   = 331   # Key: Keypad /
KEY_KP_MULTIPLY = 332   # Key: Keypad *
KEY_KP_SUBTRACT = 333   # Key: Keypad -
KEY_KP_ADD  = 334   # Key: Keypad +
KEY_KP_ENTER= 335   # Key: Keypad Enter
KEY_KP_EQUAL= 336   # Key: Keypad =
# Android key buttons
KEY_BACK= 4 # Key: Android back button
KEY_MENU= 5 # Key: Android menu button
KEY_VOLUME_UP   = 24   # Key: Android volume up button
KEY_VOLUME_DOWN = 25





# Mouse buttons

MOUSE_BUTTON_LEFT    = 0        # Mouse button left
MOUSE_BUTTON_RIGHT   = 1        # Mouse button right
MOUSE_BUTTON_MIDDLE  = 2        # Mouse button middle (pressed wheel)
MOUSE_BUTTON_SIDE    = 3        # Mouse button side (advanced mouse device)
MOUSE_BUTTON_EXTRA   = 4        # Mouse button extra (advanced mouse device)
MOUSE_BUTTON_FORWARD = 5        # Mouse button forward (advanced mouse device)
MOUSE_BUTTON_BACK    = 6        # Mouse button back (advanced mouse device)

FLAG_VSYNC_HINT         = 0x00000040   # Set to try enabling V-Sync on GPU
FLAG_FULLSCREEN_MODE    = 0x00000002   # Set to run program in fullscreen
FLAG_WINDOW_RESIZABLE   = 0x00000004   # Set to allow resizable window
FLAG_WINDOW_UNDECORATED = 0x00000008   # Set to disable window decoration (frame and buttons)
FLAG_WINDOW_HIDDEN      = 0x00000080    # Set to hide window
FLAG_WINDOW_MINIMIZED   = 0x00000200    # Set to minimize window (iconify)
FLAG_WINDOW_MAXIMIZED   = 0x00000400    # Set to maximize window (expanded to monitor)
FLAG_WINDOW_UNFOCUSED   = 0x00000800    # Set to window non focused
FLAG_WINDOW_TOPMOST     = 0x00001000    # Set to window always on top
FLAG_WINDOW_ALWAYS_RUN  = 0x00000100    # Set to allow windows running while minimized
FLAG_WINDOW_TRANSPARENT = 0x00000010    # Set to allow transparent framebuffer
FLAG_WINDOW_HIGHDPI     = 0x00002000    # Set to support HighDPI
FLAG_WINDOW_MOUSE_PASSTHROUGH = 0x00004000  # Set to support mouse passthrough  only supported when FLAG_WINDOW_UNDECORATED
FLAG_BORDERLESS_WINDOWED_MODE = 0x00008000  # Set to run program in borderless windowed mode
FLAG_MSAA_4X_HINT       = 0x00000020    # Set to try enabling MSAA 4X
FLAG_INTERLACED_HINT    = 0x00010000    # Set to try enabling interlaced video format (for V3D)

# cursors

MOUSE_CURSOR_DEFAULT       = 0      
" Default pointer shape"
MOUSE_CURSOR_ARROW         = 1      
" Arrow shape"
MOUSE_CURSOR_IBEAM         = 2      
" Text writing cursor shape"
MOUSE_CURSOR_CROSSHAIR     = 3      
" Cross shape"
MOUSE_CURSOR_POINTING_HAND = 4      
" Pointing hand cursor"
MOUSE_CURSOR_RESIZE_EW     = 5      
" Horizontal resize/move arrow shape"
MOUSE_CURSOR_RESIZE_NS     = 6      
" Vertical resize/move arrow shape"
MOUSE_CURSOR_RESIZE_NWSE   = 7      
" Top-left to bottom-right diagonal resize/move arrow shape"
MOUSE_CURSOR_RESIZE_NESW   = 8      
" The top-right to bottom-left diagonal resize/move arrow shape"
MOUSE_CURSOR_RESIZE_ALL    = 9      
" The omnidirectional resize/move cursor shape"
MOUSE_CURSOR_NOT_ALLOWED   = 10     
" The operation-not-allowed shape"

'''
typedef enum {
    LOG_ALL = 0,        # Display all logs
    LOG_TRACE,          # Trace logging, intended for internal use only
    LOG_DEBUG,          # Debug logging, used for internal debugging, it should be disabled on release builds
    LOG_INFO,           # Info logging, used for program execution info
    LOG_WARNING,        # Warning logging, used on recoverable failures
    LOG_ERROR,          # Error logging, used on unrecoverable failures
    LOG_FATAL,          # Fatal logging, used to abort program: exit(EXIT_FAILURE)
    LOG_NONE            # Disable logging
} TraceLogLevel;
'''

LOG_ALL = 0
LOG_TRACE = 1
LOG_DEBUG = 2
LOG_INFO = 3
LOG_WARNING = 4
LOG_ERROR = 5
LOG_FATAL = 6
LOG_NONE = 7
'''
    SHADER_LOC_VERTEX_POSITION = 0,   Shader location: vertex attribute: position
    SHADER_LOC_VERTEX_TEXCOORD01,   # Shader location: vertex attribute: texcoord01
    SHADER_LOC_VERTEX_TEXCOORD02,   # Shader location: vertex attribute: texcoord02
    SHADER_LOC_VERTEX_NORMAL,       # Shader location: vertex attribute: normal
    SHADER_LOC_VERTEX_TANGENT,      # Shader location: vertex attribute: tangent
    SHADER_LOC_VERTEX_COLOR,        # Shader location: vertex attribute: color
    SHADER_LOC_MATRIX_MVP,          # Shader location: matrix uniform: model-view-projection
    SHADER_LOC_MATRIX_VIEW,         # Shader location: matrix uniform: view (camera transform)
    SHADER_LOC_MATRIX_PROJECTION,   # Shader location: matrix uniform: projection
    SHADER_LOC_MATRIX_MODEL,        # Shader location: matrix uniform: model (transform)
    SHADER_LOC_MATRIX_NORMAL,       # Shader location: matrix uniform: normal
    SHADER_LOC_VECTOR_VIEW,         # Shader location: vector uniform: view
    SHADER_LOC_COLOR_DIFFUSE,       # Shader location: vector uniform: diffuse color
    SHADER_LOC_COLOR_SPECULAR,      # Shader location: vector uniform: specular color
    SHADER_LOC_COLOR_AMBIENT,       # Shader location: vector uniform: ambient color
    SHADER_LOC_MAP_ALBEDO,          # Shader location: sampler2d texture: albedo (same as: SHADER_LOC_MAP_DIFFUSE)
    SHADER_LOC_MAP_METALNESS,       # Shader location: sampler2d texture: metalness (same as: SHADER_LOC_MAP_SPECULAR)
    SHADER_LOC_MAP_NORMAL,          # Shader location: sampler2d texture: normal
    SHADER_LOC_MAP_ROUGHNESS,       # Shader location: sampler2d texture: roughness
    SHADER_LOC_MAP_OCCLUSION,       # Shader location: sampler2d texture: occlusion
    SHADER_LOC_MAP_EMISSION,        # Shader location: sampler2d texture: emission
    SHADER_LOC_MAP_HEIGHT,          # Shader location: sampler2d texture: height
    SHADER_LOC_MAP_CUBEMAP,         # Shader location: samplerCube texture: cubemap
    SHADER_LOC_MAP_IRRADIANCE,      # Shader location: samplerCube texture: irradiance
    SHADER_LOC_MAP_PREFILTER,       # Shader location: samplerCube texture: prefilter
    SHADER_LOC_MAP_BRDF,            # Shader location: sampler2d texture: brdf
    SHADER_LOC_VERTEX_BONEIDS,      # Shader location: vertex attribute: boneIds
    SHADER_LOC_VERTEX_BONEWEIGHTS,  # Shader location: vertex attribute: boneWeights
    SHADER_LOC_BONE_MATRICES,       # Shader location: array of matrices uniform: boneMatrices
    SHADER_LOC_VERTEX_INSTANCE_TX   # Shader location: vertex attribute: instanceTransform
'''
SHADER_LOC_VERTEX_POSITION = 0
SHADER_LOC_VERTEX_TEXCOORD01= 1  # Shader location: vertex attribute: texcoord01
SHADER_LOC_VERTEX_TEXCOORD02= 2  # Shader location: vertex attribute: texcoord02
SHADER_LOC_VERTEX_NORMAL=   3    # Shader location: vertex attribute: normal
SHADER_LOC_VERTEX_TANGENT= 4     # Shader location: vertex attribute: tangent
SHADER_LOC_VERTEX_COLOR=   5     # Shader location: vertex attribute: color
SHADER_LOC_MATRIX_MVP=   6       # Shader location: matrix uniform: model-view-projection
SHADER_LOC_MATRIX_VIEW=      7   # Shader location: matrix uniform: view (camera transform)
SHADER_LOC_MATRIX_PROJECTION= 8  # Shader location: matrix uniform: projection
SHADER_LOC_MATRIX_MODEL=   9     # Shader location: matrix uniform: model (transform)
SHADER_LOC_MATRIX_NORMAL=   10    # Shader location: matrix uniform: normal
SHADER_LOC_VECTOR_VIEW=    11     # Shader location: vector uniform: view
SHADER_LOC_COLOR_DIFFUSE=  12     # Shader location: vector uniform: diffuse color
SHADER_LOC_COLOR_SPECULAR=  13    # Shader location: vector uniform: specular color
SHADER_LOC_COLOR_AMBIENT=  14     # Shader location: vector uniform: ambient color
SHADER_LOC_MAP_ALBEDO=     15     # Shader location: sampler2d texture: albedo (same as: SHADER_LOC_MAP_DIFFUSE)
SHADER_LOC_MAP_METALNESS=   16    # Shader location: sampler2d texture: metalness (same as: SHADER_LOC_MAP_SPECULAR)
SHADER_LOC_MAP_NORMAL=      17    # Shader location: sampler2d texture: normal
SHADER_LOC_MAP_ROUGHNESS=   18    # Shader location: sampler2d texture: roughness
SHADER_LOC_MAP_OCCLUSION=    19   # Shader location: sampler2d texture: occlusion
SHADER_LOC_MAP_EMISSION=    20    # Shader location: sampler2d texture: emission
SHADER_LOC_MAP_HEIGHT=     21     # Shader location: sampler2d texture: height
SHADER_LOC_MAP_CUBEMAP=    22     # Shader location: samplerCube texture: cubemap
SHADER_LOC_MAP_IRRADIANCE=  23    # Shader location: samplerCube texture: irradiance
SHADER_LOC_MAP_PREFILTER=   24    # Shader location: samplerCube texture: prefilter
SHADER_LOC_MAP_BRDF=    25        # Shader location: sampler2d texture: brdf
SHADER_LOC_VERTEX_BONEIDS=    26  # Shader location: vertex attribute: boneIds
SHADER_LOC_VERTEX_BONEWEIGHTS= 27 # Shader location: vertex attribute: boneWeights
SHADER_LOC_BONE_MATRICES=    28   # Shader location: array of matrices uniform: boneMatrices
SHADER_LOC_VERTEX_INSTANCE_TX= 29  # Shader location: vertex attribute: instanceTransform

SHADER_UNIFORM_FLOAT = 0        # Shader uniform type: float
SHADER_UNIFORM_VEC2 =   1          # Shader uniform type: vec2 (2 float)
SHADER_UNIFORM_VEC3 =   2          # Shader uniform type: vec3 (3 float)
SHADER_UNIFORM_VEC4 =   3          # Shader uniform type: vec4 (4 float)
SHADER_UNIFORM_INT =    4          # Shader uniform type: int
SHADER_UNIFORM_IVEC2 = 5           # Shader uniform type: ivec2 (2 int)
SHADER_UNIFORM_IVEC3 =   6         # Shader uniform type: ivec3 (3 int)
SHADER_UNIFORM_IVEC4 =   7         # Shader uniform type: ivec4 (4 int)
SHADER_UNIFORM_UINT = 8            # Shader uniform type: unsigned int
SHADER_UNIFORM_UIVEC2 = 9          # Shader uniform type: uivec2 (2 unsigned int)
SHADER_UNIFORM_UIVEC3 =  10         # Shader uniform type: uivec3 (3 unsigned int)
SHADER_UNIFORM_UIVEC4 =  11         # Shader uniform type: uivec4 (4 unsigned int)
SHADER_UNIFORM_SAMPLER2D =    12    # Shader uniform type: sampler2d

SHADER_ATTRIB_FLOAT = 0        # Shader attribute type: float
SHADER_ATTRIB_VEC2 = 1            # Shader attribute type: vec2 (2 float)
SHADER_ATTRIB_VEC3   = 2           # Shader attribute type: vec3 (3 float)
SHADER_ATTRIB_VEC4  =3            # Shader attribute type: vec4 (4 float)
