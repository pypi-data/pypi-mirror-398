import os
import ctypes,pathlib

from ctypes import (
    c_char_p,
    c_int,
    c_bool,
    c_float,
    c_uint,
    c_void_p,
    Structure,
    POINTER,
    c_ubyte,
    c_ushort,
    c_char,
    byref,
    c_double,
    c_long,
    create_string_buffer
)
import platform

class Rectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]
    
    x: float
    y: float
    width: float
    height: float

class Color(ctypes.Structure):
    _fields_ = [
        ("r", ctypes.c_ubyte),
        ("g", ctypes.c_ubyte),
        ("b", ctypes.c_ubyte),
        ("a", ctypes.c_ubyte),
    ]

    r: int
    g: int
    b: int
    a: int

class Texture2D(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("mipmaps", ctypes.c_int),
        ("format", ctypes.c_int),
    ]

    id: int
    width: int
    height: int
    mipmaps: int
    format: int

Texture = Texture2D
TextureCubemap = Texture2D

class Vector2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float)
    ]

    x: float
    y: float

    def __add__(self, other):
        if isinstance(other, Vector2):
            return lib.Vector2Add(self, other)
    def __sub__(self, other):
        if isinstance(other, Vector2):
            return lib.Vector2Subtract(self, other)

class Vector3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float)
    ]

    x: float
    y: float
    z: float

class Vector4(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float)
    ]

    x: float
    y: float
    z: float
    w: float

class Quaternion(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float)
    ]

    x: float
    y: float
    z: float
    w: float

class Matrix(ctypes.Structure):
    "Matrix, 4x4 components, column major, OpenGL style, right-handed"
    _fields_ = [
        ("m0", ctypes.c_float),("m4", ctypes.c_float),("m8", ctypes.c_float),("m12", ctypes.c_float),
        ("m1", ctypes.c_float),("m5", ctypes.c_float),("m9", ctypes.c_float),("m13", ctypes.c_float),
        ("m2", ctypes.c_float),("m6", ctypes.c_float),("m10", ctypes.c_float),("m14", ctypes.c_float),
        ("m3", ctypes.c_float),("m7", ctypes.c_float),("m11", ctypes.c_float),("m15", ctypes.c_float),
    ]

    m0: float
    m1: float
    m2: float
    m3: float

    m4: float
    m5: float
    m6: float
    m7: float

    m8: float
    m9: float
    m10: float
    m11: float

    m12: float
    m13: float
    m14: float
    m15: float

# NOTE: Helper types to be used instead of array return types for *ToFloat functions

class Float16(Structure):
    _fields_ = [("v", c_float * 16)]

class Float3(Structure):
    _fields_ = [("v", c_float * 3)]


class Image(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("mipmaps", ctypes.c_int),
        ("format", ctypes.c_int),
    ]

    data: c_void_p
    width: int
    height: int
    mipmaps: int
    format: int

class Camera2D(ctypes.Structure):
    "Camera2D, defines position/orientation in 2d space"
    _fields_ = [
        ("offset", Vector2),
        ("target", Vector2),
        ("rotation", c_float),
        ("zoom", c_float),
    ]

    offset: Vector2
    target: Vector2
    rotation: float
    zoom: float
    
class Camera3D(Structure):
    "Camera, defines position/orientation in 3d space"
    _fields_ = [
        ("position", Vector3),
        ("target", Vector3),
        ("up", Vector3),
        ("fovy", c_float),
        ("projection", c_int)
    ]

    position: Vector3
    target: Vector3
    up: Vector3
    fovy: float
    projection: int

def make_camera(position: Vector3, target: Vector3, up: Vector3, fovy: float, projection: int):
    return Camera3D(position, target, up, fovy, projection)

Camera = Camera3D

class Ray(Structure):
    "Ray, ray for raycasting"
    _fields_ = [
        ("position", Vector3),
        ("direction", Vector3),
    ]

    position: Vector3
    direction: Vector3

class RayCollision(Structure):
    "RayCollision, ray hit information"
    _fields_ = [
        ("hit", c_bool),
        ("distance", c_float),
        ("point", Vector3),
        ("normal", Vector3)
    ]

    hit: bool
    distance: float
    point: Vector3
    normal: Vector3

class RenderTexture(Structure):
    "RenderTexture, fbo for texture rendering"
    _fields_ = [
        ("id", c_uint),
        ("texture", Texture2D),
        ("depth",  Texture2D)
    ]

    id: int
    texture: Texture2D
    depth: Texture2D

RenderTexture2D = RenderTexture

class NPatchInfo(Structure):
    "NPatchInfo, n-patch layout info"
    _fields_ = [
        ("source", Rectangle),
        ("left", c_int),
        ("top", c_int),
        ("right", c_int),
        ("bottom", c_int),
        ("layout", c_int),
    ]

    source: Rectangle
    left: int
    top: int
    right: int
    bottom: int
    layout: int

class GlyphInfo(Structure):
    "GlyphInfo, font characters glyphs info"
    _fields_ = [
        ("value", c_int),
        ("offsetX", c_int),
        ("offsetY", c_int),
        ("advanceX", c_int),
        ("image", Image),
    ]

    value: int
    offsetX: int
    offsetY: int
    advanceX: int
    image: Image

class Font(Structure):
    "Font, font texture and GlyphInfo array data"
    _fields_ = [
        ("baseSize", c_int),
        ("glyphCount", c_int),
        ("glyphPadding", c_int),
        ("texture", Texture2D),
        ("recs", ctypes.POINTER(Rectangle)),
        ("glyphs", POINTER(GlyphInfo))
    ]

    baseSize: int
    glyphCount: int
    glyphPadding: int

    texture: Texture2D
    recs: list[Rectangle]
    glyphs: GlyphInfo

class VrStereoConfig(Structure):
    _fields_ = [
        ("projection", Matrix * 2),
        ("viewOffset", Matrix * 2),

        ("leftLensCenter", c_float * 2),
        ("rightLensCenter", c_float * 2),
        ("leftScreenCenter", c_float * 2),
        ("rightScreenCenter", c_float * 2),
        ("scale", c_float * 2),
        ("scaleIn", c_float * 2)
    ]



'''

// Shader
typedef struct Shader {
    unsigned int id;        // Shader program id
    int *locs;              // Shader locations array (RL_MAX_SHADER_LOCATIONS)
} Shader;

// Mesh, vertex data and vao/vbo
typedef struct Mesh {
    int vertexCount;        // Number of vertices stored in arrays
    int triangleCount;      // Number of triangles stored (indexed or not)

    // Vertex attributes data
    float *vertices;        // Vertex position (XYZ - 3 components per vertex) (shader-location = 0)
    float *texcoords;       // Vertex texture coordinates (UV - 2 components per vertex) (shader-location = 1)
    float *texcoords2;      // Vertex texture second coordinates (UV - 2 components per vertex) (shader-location = 5)
    float *normals;         // Vertex normals (XYZ - 3 components per vertex) (shader-location = 2)
    float *tangents;        // Vertex tangents (XYZW - 4 components per vertex) (shader-location = 4)
    unsigned char *colors;      // Vertex colors (RGBA - 4 components per vertex) (shader-location = 3)
    unsigned short *indices;    // Vertex indices (in case vertex data comes indexed)

    // Animation vertex data
    float *animVertices;    // Animated vertex positions (after bones transformations)
    float *animNormals;     // Animated normals (after bones transformations)
    unsigned char *boneIds; // Vertex bone ids, max 255 bone ids, up to 4 bones influence by vertex (skinning) (shader-location = 6)
    float *boneWeights;     // Vertex bone weight, up to 4 bones influence by vertex (skinning) (shader-location = 7)
    Matrix *boneMatrices;   // Bones animated transformation matrices
    int boneCount;          // Number of bones

    // OpenGL identifiers
    unsigned int vaoId;     // OpenGL Vertex Array Object id
    unsigned int *vboId;    // OpenGL Vertex Buffer Objects id (default vertex data)
} Mesh;

'''
class Shader(Structure):
    "Shader"
    _fields_ = [
        ("id", c_uint),
        ("locs", POINTER(c_int))
    ]

    id: int
    locs: int

"""
typedef struct MaterialMap {
    Texture2D texture;      // Material map texture
    Color color;            // Material map color
    float value;            // Material map value
} MaterialMap;
"""
class MaterialMap(Structure):
    _fields_ = [
        ("texture", Texture2D),
        ("color", Color),
        ("value", c_float)
    ]

    texture: Texture2D
    color: Color
    value: float

"""
typedef struct Material {
    Shader shader;          // Material shader
    MaterialMap *maps;      // Material maps array (MAX_MATERIAL_MAPS)
    float params[4];        // Material generic parameters (if required)
} Material;
"""
class Material(Structure):
    _fields_ = [
        ("shader", Shader),
        ("maps", POINTER(MaterialMap)),
        ("params", c_float * 4)
    ]

    shader: Shader
    maps: MaterialMap
    params: list[float]

class Mesh(Structure):
    "Mesh, vertex data and vao/vbo"
    _fields_ = [
        ("vertexCount", c_int),
        ("triangleCount", c_int),
        
        ("vertices", POINTER(c_float)),
        ("texcoords", POINTER(c_float)),
        ("texcoords2", POINTER(c_float)),
        ("normals", POINTER(c_float)),
        ("tangents", POINTER(c_float)),

        ("colors", POINTER(c_ubyte)),
        ("indices", POINTER(c_ushort)),

        ("animVertices", POINTER(c_float)),
        ("animNormals", POINTER(c_float)),

        ("boneIds", POINTER(c_ubyte)),

        ("boneWeights", POINTER(c_float)),

        ("boneMatrices", POINTER(Matrix)),

        ("boneCount", c_int),

        ("vaoId", c_uint),
        ("vboId", POINTER(c_uint))
    ]

"""
typedef struct BoneInfo {
    char name[32];          // Bone name
    int parent;             // Bone parent
} BoneInfo;
"""
class BoneInfo(Structure):
    _fields_ = [
        ("name", c_char * 32),
        ("parent", c_int)
    ]

    name: bytes
    parent: int

"""
typedef struct Transform {
    Vector3 translation;    // Translation
    Quaternion rotation;    // Rotation
    Vector3 scale;          // Scale
} Transform;
"""
class Transform(Structure):
    _fields_ = [
        ("translation", Vector3),
        ("rotation", Quaternion),
        ("scale", Vector3)
    ]

    translation: Vector3
    rotation: Quaternion
    scale: Vector3

'''
typedef struct ModelAnimation {
    int boneCount;          // Number of bones
    int frameCount;         // Number of animation frames
    BoneInfo *bones;        // Bones information (skeleton)
    Transform **framePoses; // Poses array by frame
    char name[32];          // Animation name
} ModelAnimation;
'''
class ModelAnimation(Structure):
    _fields_ = [
        ("boneCount", c_int),
        ("frameCount", c_int),
        ("bones", POINTER(BoneInfo)),
        ("framePoses", POINTER(POINTER(Transform))),
        ("name", c_char * 32)
    ]

    boneCount: int
    frameCount: int
    bones: list[BoneInfo]
    framePoses: list[Transform]
    name: bytes

"""
// AudioStream, custom audio stream
typedef struct AudioStream {
    rAudioBuffer *buffer;       // Pointer to internal data used by the audio system
    rAudioProcessor *processor; // Pointer to internal data processor, useful for audio effects

    unsigned int sampleRate;    // Frequency (samples per second)
    unsigned int sampleSize;    // Bit depth (bits per sample): 8, 16, 32 (24 not supported)
    unsigned int channels;      // Number of channels (1-mono, 2-stereo, ...)
} AudioStream;

// Sound
typedef struct Sound {
    AudioStream stream;         // Audio stream
    unsigned int frameCount;    // Total number of frames (considering channels)
} Sound;

// Music, audio stream, anything longer than ~10 seconds should be streamed
typedef struct Music {
    AudioStream stream;         // Audio stream
    unsigned int frameCount;    // Total number of frames (considering channels)
    bool looping;               // Music looping enable

    int ctxType;                // Type of music context (audio filetype)
    void *ctxData;              // Audio context data, depends on type
} Music;
"""

class AudioStream(Structure):
    _fields_ = [
        ("buffer", c_void_p),       # rAudioBuffer*
        ("processor", c_void_p),    # rAudioProcessor*
        
        ("sampleRate", c_uint),
        ("sampleSize", c_uint),
        ("channels", c_uint),
    ]

    buffer: c_void_p
    processor: c_void_p

    sampleRate: int
    sampleSize: int
    channels: int

class Sound(Structure):
    _fields_ = [
        ("stream", AudioStream),
        ("frameCount", c_uint)
    ]

    stream: AudioStream
    frameCount: int

class Music(Structure):
    _fields_ = [
        ("stream", AudioStream),
        ("frameCount", c_uint),
        ("looping", c_bool),

        ("ctxType", c_int),
        ("ctxData", c_void_p)
    ]

    stream: AudioStream
    frameCount: int
    looping: bool

    ctxType: int
    ctxData: c_void_p

"""
typedef struct Model {
    Matrix transform;       // Local transform matrix

    int meshCount;          // Number of meshes
    int materialCount;      // Number of materials
    Mesh *meshes;           // Meshes array
    Material *materials;    // Materials array
    int *meshMaterial;      // Mesh material number

    // Animation data
    int boneCount;          // Number of bones
    BoneInfo *bones;        // Bones information (skeleton)
    Transform *bindPose;    // Bones base transformation (pose)
} Model;
"""
class Model(Structure):
    _fields_ = [
        ("transform", Matrix),
        ("meshCount", c_int),
        ("materialCount", c_int),
        ("meshes", POINTER(Mesh)),
        ("materials", POINTER(Material)),
        ("meshMaterial", POINTER(c_int)),  # <- fixed

        ("boneCount", c_int),
        ("bones", POINTER(BoneInfo)),
        ("bindPose", POINTER(Transform))
    ]

    transform: Matrix
    meshCount: int
    materialCount: int
    meshes: list[Mesh]
    materials: list[Material]
    meshMaterial: int

    boneCount: int
    bones: list[BoneInfo]
    bindPose: list[Transform]

"""
typedef struct BoundingBox {
    Vector3 min;            // Minimum vertex box-corner
    Vector3 max;            // Maximum vertex box-corner
} BoundingBox;
"""
class BoundingBox(Structure):
    _fields_ = [
        ("min", Vector3),
        ("max", Vector3),
    ]

    min: Vector3
    max: Vector3

"""
typedef struct Wave {
    unsigned int frameCount;    // Total number of frames (considering channels)
    unsigned int sampleRate;    // Frequency (samples per second)
    unsigned int sampleSize;    // Bit depth (bits per sample): 8, 16, 32 (24 not supported)
    unsigned int channels;      // Number of channels (1-mono, 2-stereo, ...)
    void *data;                 // Buffer data pointer
} Wave;
"""
class Wave(Structure):
    _fields_ = [
        ("frameCount", c_uint),
        ("sampleRate", c_uint),
        ("sampleSize", c_uint),
        ("channels", c_uint),
        ("data", c_void_p)
    ]

"""
typedef struct FilePathList {
    unsigned int capacity;          // Filepaths max entries
    unsigned int count;             // Filepaths entries count
    char **paths;                   // Filepaths entries
} FilePathList;
"""
class FilePathList(Structure):
    _fields_ = [
        ("capacity", c_uint),
        ("count", c_uint),
        ("paths", POINTER(c_char_p))
    ]

    capacity: int
    count: int
    paths: list[str]

# const
rl_imgp = ctypes.POINTER(Image) # it's pointing to that chocolate cake over there
ubyte_p = POINTER(c_ubyte)
c_ubyte_p = ubyte_p
c_int_p = POINTER(c_int)

libex: str
lib: ctypes.CDLL
def init():
    global lib, libex
    if platform.system() == "Darwin":
        #os.environ["DYLD_LIBRARY_PATH"] = os.path.dirname(__file__)
        libex = "libAppleSillicon.dylib"
    elif platform.system() == "Windows":
        libex = "libwin86_64.dll"
    elif platform.system() == "Linux":
        libex = "liblinux86_64.so"
    else:
        raise RuntimeError("Platform not supported")
    library_path = pathlib.Path(__file__).parent / libex
    print(f"Dylib Path: {library_path}")
    print(f"System: {platform.platform()}")
    lib = ctypes.CDLL(str(library_path))

# make
def make_rect(x: float,y: float,width: float,height: float):
    return Rectangle(x,y,width,height)

#   colors
def make_color(red: int, green: int, blue: int, alpha:int=255):
    return Color(red, green, blue, alpha)

def makeconnect(cfunc: str, args: list = [], res = None):
    poop: ctypes._NamedFuncPointer = getattr(lib, cfunc)
    poop.argtypes = args
    poop.restype = res
