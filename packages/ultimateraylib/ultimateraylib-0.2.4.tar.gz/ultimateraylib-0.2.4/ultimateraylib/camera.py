from ._classes import *





"""
RLAPI void UpdateCamera(Camera *camera, int mode);            // Update camera position for selected mode
RLAPI void UpdateCameraPro(Camera *camera, Vector3 movement, Vector3 rotation, float zoom); // Update camera movement/rotation
"""
makeconnect("UpdateCamera", [POINTER(Camera3D), c_int])
def update_camera(camera: Camera3D, mode: int):
    lib.UpdateCamera(byref(camera), mode)
    return camera

makeconnect("UpdateCameraPro", [POINTER(Camera3D), Vector3, Vector3, c_float])
def update_camera_pro(camera: Camera3D, movement: Vector3, rotation: Vector3, zoom: float):
    lib.UpdateCameraPro(byref(camera), movement, rotation, zoom)
    return camera

"""
typedef enum {
    CAMERA_CUSTOM = 0,              // Camera custom, controlled by user (UpdateCamera() does nothing)
    CAMERA_FREE,                    // Camera free mode
    CAMERA_ORBITAL,                 // Camera orbital, around target, zoom supported
    CAMERA_FIRST_PERSON,            // Camera first person
    CAMERA_THIRD_PERSON             // Camera third person
} CameraMode;

// Camera projection
typedef enum {
    CAMERA_PERSPECTIVE = 0,         // Perspective projection
    CAMERA_ORTHOGRAPHIC             // Orthographic projection
} CameraProjection;
"""

CAMERA_CUSTOM = 0
CAMERA_FREE = 1
CAMERA_ORBITAL = 2
CAMERA_FIRST_PERSON = 3
CAMERA_THIRD_PERSON = 4

CAMERA_PERSPECTIVE = 0
CAMERA_ORTHOGRAPHIC = 1
