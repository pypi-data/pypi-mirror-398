from ._classes import *

'''

RLAPI void rlMatrixMode(int mode);                      // Choose the current matrix to be transformed
RLAPI void rlPushMatrix(void);                          // Push the current matrix to stack
RLAPI void rlPopMatrix(void);                           // Pop latest inserted matrix from stack
RLAPI void rlLoadIdentity(void);                        // Reset current matrix to identity matrix

RLAPI void rlTranslatef(float x, float y, float z);     // Multiply the current matrix by a translation matrix
RLAPI void rlRotatef(float angle, float x, float y, float z); // Multiply the current matrix by a rotation matrix
RLAPI void rlScalef(float x, float y, float z);         // Multiply the current matrix by a scaling matrix

RLAPI void rlMultMatrixf(const float *matf);            // Multiply the current matrix by another matrix
RLAPI void rlFrustum(double left, double right, double bottom, double top, double znear, double zfar);
RLAPI void rlOrtho(double left, double right, double bottom, double top, double znear, double zfar);
RLAPI void rlViewport(int x, int y, int width, int height); // Set the viewport area
RLAPI void rlSetClipPlanes(double nearPlane, double farPlane);    // Set clip planes distances
RLAPI double rlGetCullDistanceNear(void);               // Get cull plane distance near
RLAPI double rlGetCullDistanceFar(void);                // Get cull plane distance far
'''

makeconnect("rlMatrixMode" , [c_int])
def rl_matrix_mode(mode: int):
    lib.rlMatrixMode(mode)

rl_push_matrix = lib.rlPushMatrix
rl_pop_matrix = lib.rlPopMatrix
rl_load_identity = lib.rlLoadIdentity

makeconnect("rlTranslatef", [c_float, c_float, c_float])
def rl_translatef(x: float, y: float, z: float):
    lib.rlTranslatef(x, y, z)

makeconnect("rlRotatef", [c_float, c_float, c_float, c_float])
def rl_rotatef(angle: float, x: float, y: float, z: float):
    lib.rlRotatef(angle, x, y, z)

makeconnect("rlScalef", [c_float, c_float, c_float])
def rl_scalef(x: float, y: float, z: float):
    lib.rlScalef(x, y, z)

makeconnect("rlMultMatrixf", [POINTER(c_float)])
def rl_mult_matrixf(matf: float):
    lib.rlMultMatrixf(byref(c_float(matf)))

makeconnect("rlFrustum", [c_double, c_double, c_double, c_double, c_double, c_double]) 
def rl_frustum(left: float, right: float, bottom: float, top: float, znear: float, zfar: float):
    lib.rlFrustum(left, right, bottom, top, znear, zfar)

makeconnect("rlOrtho", [c_double, c_double, c_double, c_double, c_double, c_double]) 
def rl_ortho(left: float, right: float, bottom: float, top: float, znear: float, zfar: float):
    lib.rlOrtho(left, right, bottom, top, znear, zfar)



'''
//------------------------------------------------------------------------------------
// Functions Declaration - Vertex level operations
//------------------------------------------------------------------------------------
RLAPI void rlBegin(int mode);                           // Initialize drawing mode (how to organize vertex)
RLAPI void rlEnd(void);                                 // Finish vertex providing

RLAPI void rlVertex2i(int x, int y);                    // Define one vertex (position) - 2 int
RLAPI void rlVertex2f(float x, float y);                // Define one vertex (position) - 2 float
RLAPI void rlVertex3f(float x, float y, float z);       // Define one vertex (position) - 3 float

RLAPI void rlTexCoord2f(float x, float y);              // Define one vertex (texture coordinate) - 2 float
RLAPI void rlNormal3f(float x, float y, float z);       // Define one vertex (normal) - 3 float
RLAPI void rlColor4ub(unsigned char r, unsigned char g, unsigned char b, unsigned char a); // Define one vertex (color) - 4 byte
RLAPI void rlColor3f(float x, float y, float z);        // Define one vertex (color) - 3 float
RLAPI void rlColor4f(float x, float y, float z, float w); // Define one vertex (color) - 4 float
'''

makeconnect("rlBegin", [c_int])
def rl_begin(mode: int):
    lib.rlBegin(mode)
rl_end = lib.rlEnd

makeconnect("rlVertex2i", [c_int, c_int])
def rl_vertex_2i(x: int, y:int):
    lib.rlVertex2i(x, y)

makeconnect("rlVertex2f", [c_float, c_float])
def rl_vertex_2f(x: float, y:float):
    lib.rlVertex2f(x, y)

makeconnect("rlVertex3f", [c_float, c_float, c_float])
def rl_vertex_3f(x: float, y:float, z: float):
    lib.rlVertex3f(x, y, z)

makeconnect("rlTexCoord2f", [c_float, c_float])
def rl_tex_coord_2f(x: float, y:float):
    lib.rlTexCoord2f(x, y)

makeconnect("rlNormal3f", [c_float, c_float, c_float])
def rl_normal_3f(x: float, y:float, z: float):
    lib.rlNormal3f(x, y, z)

makeconnect("rlColor4ub", [c_ubyte, c_ubyte, c_ubyte, c_ubyte])
def rl_color_4ub(r: int, g: int, b: int, a: int ):
    lib.rlColor4ub(r, g, b, a)

makeconnect("rlColor3f", [c_float, c_float, c_float])
def rl_color_3f(x: float, y:float, z: float):
    lib.rlColor3f(x, y, z)

makeconnect("rlColor4f", [c_float, c_float, c_float, c_float])
def rl_color_4f(x: float, y:float, z: float, w: float):
    lib.rlColor4f(x, y, z, w)

'''
//------------------------------------------------------------------------------------
// Functions Declaration - OpenGL style functions (common to 1.1, 3.3+, ES2)
// NOTE: This functions are used to completely abstract raylib code from OpenGL layer,
// some of them are direct wrappers over OpenGL calls, some others are custom
//------------------------------------------------------------------------------------

// Vertex buffers state
RLAPI bool rlEnableVertexArray(unsigned int vaoId);     // Enable vertex array (VAO, if supported)
RLAPI void rlDisableVertexArray(void);                  // Disable vertex array (VAO, if supported)
RLAPI void rlEnableVertexBuffer(unsigned int id);       // Enable vertex buffer (VBO)
RLAPI void rlDisableVertexBuffer(void);                 // Disable vertex buffer (VBO)
RLAPI void rlEnableVertexBufferElement(unsigned int id); // Enable vertex buffer element (VBO element)
RLAPI void rlDisableVertexBufferElement(void);          // Disable vertex buffer element (VBO element)
RLAPI void rlEnableVertexAttribute(unsigned int index); // Enable vertex attribute index
RLAPI void rlDisableVertexAttribute(unsigned int index); // Disable vertex attribute index
RLAPI void rlEnableStatePointer(int vertexAttribType, void *buffer); // Enable attribute state pointer
RLAPI void rlDisableStatePointer(int vertexAttribType); // Disable attribute state pointer

// Textures state
RLAPI void rlActiveTextureSlot(int slot);               // Select and active a texture slot
RLAPI void rlEnableTexture(unsigned int id);            // Enable texture
RLAPI void rlDisableTexture(void);                      // Disable texture
RLAPI void rlEnableTextureCubemap(unsigned int id);     // Enable texture cubemap
RLAPI void rlDisableTextureCubemap(void);               // Disable texture cubemap
RLAPI void rlTextureParameters(unsigned int id, int param, int value); // Set texture parameters (filter, wrap)
RLAPI void rlCubemapParameters(unsigned int id, int param, int value); // Set cubemap parameters (filter, wrap)

// Shader state
RLAPI void rlEnableShader(unsigned int id);             // Enable shader program
RLAPI void rlDisableShader(void);                       // Disable shader program
'''

'''
// Framebuffer state
RLAPI void rlEnableFramebuffer(unsigned int id);        // Enable render texture (fbo)
RLAPI void rlDisableFramebuffer(void);                  // Disable render texture (fbo), return to default framebuffer
RLAPI unsigned int rlGetActiveFramebuffer(void);        // Get the currently active render texture (fbo), 0 for default framebuffer
RLAPI void rlActiveDrawBuffers(int count);              // Activate multiple draw color buffers
RLAPI void rlBlitFramebuffer(int srcX, int srcY, int srcWidth, int srcHeight, int dstX, int dstY, int dstWidth, int dstHeight, int bufferMask); // Blit active framebuffer to main framebuffer
RLAPI void rlBindFramebuffer(unsigned int target, unsigned int framebuffer); // Bind framebuffer (FBO)

// General render state
RLAPI void rlEnableColorBlend(void);                    // Enable color blending
RLAPI void rlDisableColorBlend(void);                   // Disable color blending
RLAPI void rlEnableDepthTest(void);                     // Enable depth test
RLAPI void rlDisableDepthTest(void);                    // Disable depth test
RLAPI void rlEnableDepthMask(void);                     // Enable depth write
RLAPI void rlDisableDepthMask(void);                    // Disable depth write
RLAPI void rlEnableBackfaceCulling(void);               // Enable backface culling
RLAPI void rlDisableBackfaceCulling(void);              // Disable backface culling
RLAPI void rlColorMask(bool r, bool g, bool b, bool a); // Color mask control
RLAPI void rlSetCullFace(int mode);                     // Set face culling mode
RLAPI void rlEnableScissorTest(void);                   // Enable scissor test
RLAPI void rlDisableScissorTest(void);                  // Disable scissor test
RLAPI void rlScissor(int x, int y, int width, int height); // Scissor test
RLAPI void rlEnablePointMode(void);                     // Enable point mode
RLAPI void rlDisablePointMode(void);                    // Disable point mode
RLAPI void rlSetPointSize(float size);                  // Set the point drawing size
RLAPI float rlGetPointSize(void);                       // Get the point drawing size
RLAPI void rlEnableWireMode(void);                      // Enable wire mode
RLAPI void rlDisableWireMode(void);                     // Disable wire mode
RLAPI void rlSetLineWidth(float width);                 // Set the line drawing width
RLAPI float rlGetLineWidth(void);                       // Get the line drawing width
RLAPI void rlEnableSmoothLines(void);                   // Enable line aliasing
RLAPI void rlDisableSmoothLines(void);                  // Disable line aliasing
RLAPI void rlEnableStereoRender(void);                  // Enable stereo rendering
RLAPI void rlDisableStereoRender(void);                 // Disable stereo rendering
RLAPI bool rlIsStereoRenderEnabled(void);               // Check if stereo render is enabled

RLAPI void rlClearColor(unsigned char r, unsigned char g, unsigned char b, unsigned char a); // Clear color buffer with color
RLAPI void rlClearScreenBuffers(void);                  // Clear used screen buffers (color and depth)
RLAPI void rlCheckErrors(void);                         // Check and log OpenGL error codes
RLAPI void rlSetBlendMode(int mode);                    // Set blending mode
RLAPI void rlSetBlendFactors(int glSrcFactor, int glDstFactor, int glEquation); // Set blending mode factor and equation (using OpenGL factors)
RLAPI void rlSetBlendFactorsSeparate(int glSrcRGB, int glDstRGB, int glSrcAlpha, int glDstAlpha, int glEqRGB, int glEqAlpha); // Set blending mode factors and equations separately (using OpenGL factors)

'''

'''
#define RL_TEXTURE_WRAP_REPEAT                  0x2901      // GL_REPEAT
#define RL_TEXTURE_WRAP_CLAMP                   0x812F      // GL_CLAMP_TO_EDGE
#define RL_TEXTURE_WRAP_MIRROR_REPEAT           0x8370      // GL_MIRRORED_REPEAT
#define RL_TEXTURE_WRAP_MIRROR_CLAMP            0x8742      // GL_MIRROR_CLAMP_EXT

// Matrix modes (equivalent to OpenGL)
#define RL_MODELVIEW                            0x1700      // GL_MODELVIEW
#define RL_PROJECTION                           0x1701      // GL_PROJECTION
#define RL_TEXTURE                              0x1702      // GL_TEXTURE

// Primitive assembly draw modes
#define RL_LINES                                0x0001      // GL_LINES
#define RL_TRIANGLES                            0x0004      // GL_TRIANGLES
#define RL_QUADS                                0x0007      // GL_QUADS

// GL equivalent data types
#define RL_UNSIGNED_BYTE                        0x1401      // GL_UNSIGNED_BYTE
#define RL_FLOAT                                0x1406      // GL_FLOAT
'''

RL_TEXTURE_WRAP_REPEAT = 0x2901
RL_TEXTURE_WRAP_CLAMP = 0x812F
RL_TEXTURE_WRAP_MIRROR_REPEAT = 0x8370
RL_TEXTURE_WRAP_MIRROR_CLAMP = 0x8742

RL_MODELVIEW = 0x1700
RL_PROJECTION = 0x1701
RL_TEXTURE = 0x1702

RL_LINES = 0x0001
RL_TRIANGLES = 0x0004
RL_QUADS = 0x0007

RL_UNSIGNED_BYTE = 0x1401
RL_FLOAT = 0x1406

'''
// rlgl initialization functions
RLAPI void rlglInit(int width, int height);             // Initialize rlgl (buffers, shaders, textures, states)
RLAPI void rlglClose(void);                             // De-initialize rlgl (buffers, shaders, textures)
RLAPI void rlLoadExtensions(void *loader);              // Load OpenGL extensions (loader function required)

RLAPI void *rlGetProcAddress(const char *procName);     // Get OpenGL procedure address
RLAPI int rlGetVersion(void);                           // Get current OpenGL version

RLAPI void rlSetFramebufferWidth(int width);            // Set current framebuffer width
RLAPI int rlGetFramebufferWidth(void);                  // Get default framebuffer width

RLAPI void rlSetFramebufferHeight(int height);          // Set current framebuffer height
RLAPI int rlGetFramebufferHeight(void);                 // Get default framebuffer height

RLAPI unsigned int rlGetTextureIdDefault(void);         // Get default texture id
RLAPI unsigned int rlGetShaderIdDefault(void);          // Get default shader id
RLAPI int *rlGetShaderLocsDefault(void);                // Get default shader locations
'''

makeconnect("rlglInit", [c_int, c_int])
def rlgl_init(width: int, height: int):
    lib.rlglInit(width, height)

rlgl_close = lib.rlglClose

makeconnect("rlLoadExtensions", [c_void_p])
def rl_load_extensions(loader: c_void_p):
    lib.rlLoadExtensions(loader)
'''
makeconnect("rlGetProcAddress", [c_char_p], c_void_p)
def rl_get_proc_address(proc_name: str) -> c_void_p:
    return lib.rlGetProcAddress(proc_name.encode())
'''
makeconnect("rlGetVersion", [], c_int)
def rl_get_version() -> int:
    return lib.rlGetVersion()

makeconnect("rlSetFramebufferWidth", [c_int])
def rl_set_framebuffer_width(width: int):
    lib.rlSetFramebufferWidth(width)

makeconnect("rlGetFramebufferWidth", [], c_int)
def rl_get_frame_buffer_width() -> int:
    return lib.rlGetFramebufferWidth()

makeconnect("rlSetFramebufferHeight", [c_int])
def rl_set_framebuffer_height(height: int):
    lib.rlSetFramebufferHeight(height)

makeconnect("rlGetFramebufferHeight", [], c_int)
def rl_get_frame_buffer_height() -> int:
    return lib.rlGetFramebufferHeight()

