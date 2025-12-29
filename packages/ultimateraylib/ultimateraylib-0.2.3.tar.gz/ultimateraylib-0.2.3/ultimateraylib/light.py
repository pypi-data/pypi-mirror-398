from ._classes import *

'''
typedef struct {   
    int type;
    bool enabled;

    Vector3 position;
    Vector3 target;

    Color color;

    float attenuation;
    
    // Shader locations
    int enabledLoc;
    int typeLoc;
    int positionLoc;
    int targetLoc;
    int colorLoc;
    int attenuationLoc;
} Light;

// Light type
typedef enum {
    LIGHT_DIRECTIONAL = 0,
    LIGHT_POINT
} LightType;
'''

class Light(Structure):
    _fields_ = [
        ("type", c_int),
        ("enabled", c_bool),

        ("position", Vector3),
        ("target", Vector3),

        ("color", Color),

        ("attenuation", c_float),

        ("enabledLoc", c_int),
        ("typeLoc", c_int),
        ("positionLoc", c_int),
        ("targetLoc", c_int),
        ("colorLoc", c_int),
        ("attenuationLoc", c_int)
    ]

    type: int
    enabled: bool
    
    position: Vector3
    target: Vector3

    color: Color

    attenuation: float

    enabledLoc: int
    typeLoc: int
    positionLoc: int

    targetLoc: int
    colorLoc: int
    attenuationLoc: int


LIGHT_DIRECTIONAL = 0
LIGHT_POINT = 1

'''
Light CreateLight(int type, Vector3 position, Vector3 target, Color color, Shader shader);   // Create a light and get shader locations
void UpdateLightValues(Shader shader, Light light);         // Send light properties to shader
'''

makeconnect("CreateLight", [c_int, Vector3, Vector3, Color, Shader], Light)
def create_light(type: int, position: Vector3, target: Vector3, color: Color, shader: Shader) -> Light:
    "Create a light and get shader locations"
    return lib.CreateLight(type, position, target, color, shader)

makeconnect("UpdateLightValues", [Shader, Light])
def update_light_values(shader: Shader, light: Light):
    'Send light properties to shader'
    lib.UpdateLightValues(shader, light)