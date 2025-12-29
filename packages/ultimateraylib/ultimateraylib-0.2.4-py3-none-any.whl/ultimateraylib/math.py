from ._classes import *
# raymath

lib.Clamp.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
lib.Clamp.restype = ctypes.c_float
def clamp(value,min,max):
    return lib.Clamp(value, min, max)


vector2_zero = Vector2(0, 0)
#def vector2_zero():
#    return Vector2(0,0)
vector2_one = Vector2(1, 1)


'''
// Add two vectors (v1 + v2)
RMAPI Vector2 Vector2Add(Vector2 v1, Vector2 v2)

// Add vector and float value
RMAPI Vector2 Vector2AddValue(Vector2 v, float add)

// Subtract two vectors (v1 - v2)
RMAPI Vector2 Vector2Subtract(Vector2 v1, Vector2 v2)

// Subtract vector by float value
RMAPI Vector2 Vector2SubtractValue(Vector2 v, float sub)

// Calculate vector length
RMAPI float Vector2Length(Vector2 v)

// Calculate vector square length
RMAPI float Vector2LengthSqr(Vector2 v)
'''

makeconnect("Vector2Add", [Vector2, Vector2], Vector2)
def vector2_add(v1: Vector2, v2: Vector2) -> Vector2:
    "Add two vectors (v1 + v2)"
    return lib.Vector2Add(v1, v2)

makeconnect("Vector2AddValue", [Vector2, c_float], Vector2)
def vector2_add_value(v: Vector2, add: float) -> Vector2:
    "Add vector and float value"
    return lib.Vector2AddValue(v, add)

makeconnect("Vector2Subtract", [Vector2, Vector2], Vector2)
def vector2_subtract(v1: Vector2, v2: Vector2) -> Vector2:
    "Subtract two vectors (v1 - v2)"
    return lib.Vector2Subtract(v1, v2)

makeconnect("Vector2SubtractValue", [Vector2, c_float], Vector2)
def vector2_subtract_value(v: Vector2, sub: float) -> Vector2:
    "Subtract vector by float value"
    return lib.Vector2SubtractValue(v, sub)

makeconnect("Vector2Length", [Vector2], c_float)
def vector2_length(v: Vector2) -> float:
    "Calculate vector length"
    return lib.Vector2Length(v)

makeconnect("Vector2LengthSqr", [Vector2], c_float)
def vector2_length_sqr(v: Vector2) -> float:
    "Calculate vector square length"
    return lib.Vector2LengthSqr(v)



'''
// Calculate two vectors dot product
RMAPI float Vector2DotProduct(Vector2 v1, Vector2 v2)

// Calculate two vectors cross product
RMAPI float Vector2CrossProduct(Vector2 v1, Vector2 v2)

// Calculate distance between two vectors
RMAPI float Vector2Distance(Vector2 v1, Vector2 v2)

// Calculate square distance between two vectors
RMAPI float Vector2DistanceSqr(Vector2 v1, Vector2 v2)

// Calculate the signed angle from v1 to v2, relative to the origin (0, 0)
// NOTE: Coordinate system convention: positive X right, positive Y down
// positive angles appear clockwise, and negative angles appear counterclockwise
RMAPI float Vector2Angle(Vector2 v1, Vector2 v2)

// Calculate angle defined by a two vectors line
// NOTE: Parameters need to be normalized
// Current implementation should be aligned with glm::angle
RMAPI float Vector2LineAngle(Vector2 start, Vector2 end)

// Scale vector (multiply by value)
RMAPI Vector2 Vector2Scale(Vector2 v, float scale)

// Multiply vector by vector
RMAPI Vector2 Vector2Multiply(Vector2 v1, Vector2 v2)

// Negate vector
RMAPI Vector2 Vector2Negate(Vector2 v)

'''

makeconnect("Vector2DotProduct", [Vector2, Vector2], c_float)
def vector2_dot_product(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2DotProduct(v1, v2)
'''
makeconnect("Vector2CrossProduct", [Vector2, Vector2], c_float)
def vector2_cross_product(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2CrossProduct(v1, v2)
'''
makeconnect("Vector2Distance", [Vector2, Vector2], c_float)
def vector2_distance(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2Distance(v1, v2)

makeconnect("Vector2DistanceSqr", [Vector2, Vector2], c_float)
def vector2_distance_sqr(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2DistanceSqr(v1, v2)

makeconnect("Vector2Angle", [Vector2, Vector2], c_float)
def vector2_angle(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2Angle(v1, v2)

makeconnect("Vector2LineAngle", [Vector2, Vector2], c_float)
def vector2_line_angle(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2LineAngle(v1, v2)

makeconnect("Vector2Scale", [Vector2, c_float], Vector2)
def vector2_scale(v: Vector2, scale: float) -> Vector2:
    return lib.Vector2Scale(v, scale)

makeconnect("Vector2Multiply", [Vector2, Vector2], Vector2)
def vector2_multiply(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2Multiply(v1, v2)

makeconnect("Vector2Negate", [Vector2], Vector2)
def vector2_negate(v: Vector2) -> Vector2:
    return lib.Vector2Negate(v)

'''
// Divide vector by vector
RMAPI Vector2 Vector2Divide(Vector2 v1, Vector2 v2)

// Normalize provided vector
RMAPI Vector2 Vector2Normalize(Vector2 v)

// Transforms a Vector2 by a given Matrix
RMAPI Vector2 Vector2Transform(Vector2 v, Matrix mat)

// Calculate linear interpolation between two vectors
RMAPI Vector2 Vector2Lerp(Vector2 v1, Vector2 v2, float amount)

// Calculate reflected vector to normal
RMAPI Vector2 Vector2Reflect(Vector2 v, Vector2 normal)

// Get min value for each pair of components
RMAPI Vector2 Vector2Min(Vector2 v1, Vector2 v2)

// Get max value for each pair of components
RMAPI Vector2 Vector2Max(Vector2 v1, Vector2 v2)

// Rotate vector by angle
RMAPI Vector2 Vector2Rotate(Vector2 v, float angle)
'''

makeconnect("Vector2Divide", [Vector2, Vector2], Vector2)
def vector2_divide(v1: Vector2, v2: Vector2) -> float:
    return lib.Vector2Divide(v1, v2)

makeconnect("Vector2Normalize", [Vector2], Vector2)
def vector2_normalize(v: Vector2) -> Vector2:
    return lib.Vector2Normalize(v)

makeconnect("Vector2Transform", [Vector2, Matrix], Vector2)
def vector2_transform(v: Vector2, mat: Matrix) -> Vector2:
    return lib.Vector2Transform(v, mat)

makeconnect("Vector2Lerp", [Vector2, Vector2, c_float], Vector2)
def vector2_lerp(v1: Vector2, v2: Vector2, amount: float) -> float:
    return lib.Vector2Lerp(v1, v2, amount)

makeconnect("Vector2Reflect", [Vector2, Vector2], Vector2)
def vector2_reflect(v: Vector2, normal: Vector2) -> Vector2:
    return lib.Vector2Reflect(v, normal)

makeconnect("Vector2Min", [Vector2, Vector2], Vector2)
def vector2_min(v1: Vector2, v2: Vector2) -> Vector2:
    return lib.Vector2Min(v1, v2)

makeconnect("Vector2Max", [Vector2, Vector2], Vector2)
def vector2_max(v1: Vector2, v2: Vector2) -> Vector2:
    return lib.Vector2Max(v1, v2)

makeconnect("Vector2Rotate", [Vector2, c_float], Vector2)
def vector2_rotate(v: Vector2, angle: float) -> Vector2:
    return lib.Vector2Rotate(v, angle)

'''
// Move Vector towards target
RMAPI Vector2 Vector2MoveTowards(Vector2 v, Vector2 target, float maxDistance)

// Invert the given vector
RMAPI Vector2 Vector2Invert(Vector2 v)

// Clamp the components of the vector between
// min and max values specified by the given vectors
RMAPI Vector2 Vector2Clamp(Vector2 v, Vector2 min, Vector2 max)

// Clamp the magnitude of the vector between two min and max values
RMAPI Vector2 Vector2ClampValue(Vector2 v, float min, float max)

// Check whether two given vectors are almost equal
RMAPI int Vector2Equals(Vector2 p, Vector2 q)

// Compute the direction of a refracted ray
// v: normalized direction of the incoming ray
// n: normalized normal vector of the interface of two optical media
// r: ratio of the refractive index of the medium from where the ray comes
//    to the refractive index of the medium on the other side of the surface
RMAPI Vector2 Vector2Refract(Vector2 v, Vector2 n, float r)
'''

makeconnect("Vector2MoveTowards", [Vector2, Vector2, c_float], Vector2)
def vector2_move_towards(v: Vector2, target: Vector2, max_distance: float) -> Vector2:
    return lib.Vector2MoveTowards(v, target, max_distance)

makeconnect("Vector2Invert", [Vector2], Vector2)
def vector2_invert(v: Vector2) -> Vector2: 
    return lib.Vector2Invert(v)

makeconnect("Vector2Clamp", [Vector2, Vector2, Vector2], Vector2)
def vector2_clamp(v: Vector2, min: Vector2, max: Vector2) -> Vector2:
    return lib.Vector2Clamp(v, min, max)

makeconnect("Vector2ClampValue", [Vector2, c_float, c_float], Vector2)
def vector2_clamp_value(v: Vector2, min: float, max: float) -> Vector2:
    return lib.Vector2ClampValue(v, min, max)

makeconnect("Vector2Equals", [Vector2, Vector2], c_int)
def vector2_equals(p: Vector2, q: Vector2) -> int:
    return lib.Vector2Equals(p, q)

makeconnect("Vector2Refract", [Vector2, Vector2, c_float], Vector2)
def vector2_refract(v: Vector2, n: Vector2, r: float) -> Vector2:
    return lib.Vector2Refract(v, n, r)

vector3_zero = Vector3(0,0,0)
'Vector with components value 0.0f'

vector3_one = Vector3(1,1,1)
'Vector with components value 1.0f'

'''

// Add two vectors
RMAPI Vector3 Vector3Add(Vector3 v1, Vector3 v2)

// Add vector and float value
RMAPI Vector3 Vector3AddValue(Vector3 v, float add)

// Subtract two vectors
RMAPI Vector3 Vector3Subtract(Vector3 v1, Vector3 v2)

// Subtract vector by float value
RMAPI Vector3 Vector3SubtractValue(Vector3 v, float sub)
'''

makeconnect("Vector3Add", [Vector3, Vector3], Vector3)
def vector3_add(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Add(v1, v2)

makeconnect("Vector3AddValue", [Vector3, c_float], Vector3)
def vector3_add_value(v: Vector3, add: float) -> Vector3:
    return lib.Vector3AddValue(v, add)

makeconnect("Vector3Subtract", [Vector3, Vector3], Vector3)
def vector3_subtract(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Subtract(v1, v2)

makeconnect("Vector3SubtractValue", [Vector3, c_float], Vector3)
def vector3_subtract_value(v: Vector3, sub: float) -> Vector3:
    return lib.Vector3SubtractValue(v, sub)

'''
// Multiply vector by scalar
RMAPI Vector3 Vector3Scale(Vector3 v, float scalar)

// Multiply vector by vector
RMAPI Vector3 Vector3Multiply(Vector3 v1, Vector3 v2)

// Calculate two vectors cross product
RMAPI Vector3 Vector3CrossProduct(Vector3 v1, Vector3 v2)

// Calculate one vector perpendicular vector
RMAPI Vector3 Vector3Perpendicular(Vector3 v)

// Calculate vector length
RMAPI float Vector3Length(const Vector3 v)

// Calculate vector square length
RMAPI float Vector3LengthSqr(const Vector3 v)
'''

makeconnect("Vector3Scale", [Vector3, c_float], Vector3)
def vector3_scale(v: Vector3, scalar: float) -> Vector3:
    return lib.Vector3Scale(v, scalar)

makeconnect("Vector3Multiply", [Vector3, Vector3], Vector3)
def vector3_multiply(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Multiply(v1, v2)

makeconnect("Vector3CrossProduct", [Vector3, Vector3], Vector3)
def vector3_cross_product(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3CrossProduct(v1, v2)

makeconnect("Vector3Perpendicular", [Vector3], Vector3)
def vector3_perpendicular(v: Vector3) -> Vector3:
    return lib.Vector3Perpendicular(v)

makeconnect("Vector3Length", [Vector3], c_float)
def vector3_length(v: Vector3) -> float:
    return lib.Vector3Length(v)

makeconnect("Vector3LengthSqr", [Vector3], c_float)
def vector3_length_sqr(v: Vector3) -> float:
    return lib.Vector3LengthSqr(v)

'''
// Calculate two vectors dot product
RMAPI float Vector3DotProduct(Vector3 v1, Vector3 v2)

// Calculate distance between two vectors
RMAPI float Vector3Distance(Vector3 v1, Vector3 v2)

// Calculate square distance between two vectors
RMAPI float Vector3DistanceSqr(Vector3 v1, Vector3 v2)

// Calculate angle between two vectors
RMAPI float Vector3Angle(Vector3 v1, Vector3 v2)

// Negate provided vector (invert direction)
RMAPI Vector3 Vector3Negate(Vector3 v)

// Divide vector by vector
RMAPI Vector3 Vector3Divide(Vector3 v1, Vector3 v2)

// Normalize provided vector
RMAPI Vector3 Vector3Normalize(Vector3 v)

//Calculate the projection of the vector v1 on to v2
RMAPI Vector3 Vector3Project(Vector3 v1, Vector3 v2)

//Calculate the rejection of the vector v1 on to v2
RMAPI Vector3 Vector3Reject(Vector3 v1, Vector3 v2)
'''

makeconnect("Vector3DotProduct", [Vector3, Vector3], c_float)
def vector3_dot_product(v1: Vector3, v2: Vector3) -> float:
    return lib.Vector3DotProduct(v1, v2)

makeconnect("Vector3Distance", [Vector3, Vector3], c_float)
def vector3_distance(v1: Vector3, v2: Vector3) -> float:
    return lib.Vector3Distance(v1, v2)

makeconnect("Vector3DistanceSqr", [Vector3, Vector3], c_float)
def vector3_distance_sqr(v1: Vector3, v2: Vector3) -> float:
    return lib.Vector3DistanceSqr(v1, v2)

makeconnect("Vector3Angle", [Vector3, Vector3], c_float)
def vector3_angle(v1: Vector3, v2: Vector3) -> float:
    return lib.Vector3Angle(v1, v2)

makeconnect("Vector3Negate", [Vector3], Vector3)
def vector3_negate(v: Vector3) -> Vector3:
    return lib.Vector3Negate(v)

makeconnect("Vector3Divide", [Vector3, Vector3], Vector3)
def vector3_divide(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Divide(v1, v2)

makeconnect("Vector3Normalize", [Vector3], Vector3)
def vector3_normalize(v: Vector3) -> Vector3:
    return lib.Vector3Normalize(v)

makeconnect("Vector3Project", [Vector3, Vector3], Vector3)
def vector3_project(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Project(v1, v2)

makeconnect("Vector3Reject", [Vector3, Vector3], Vector3)
def vector3_reject(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Reject(v1, v2)

'''
// Orthonormalize provided vectors
// Makes vectors normalized and orthogonal to each other
// Gram-Schmidt function implementation
RMAPI void Vector3OrthoNormalize(Vector3 *v1, Vector3 *v2)

// Transforms a Vector3 by a given Matrix
RMAPI Vector3 Vector3Transform(Vector3 v, Matrix mat)

// Transform a vector by quaternion rotation
RMAPI Vector3 Vector3RotateByQuaternion(Vector3 v, Quaternion q)

// Rotates a vector around an axis
RMAPI Vector3 Vector3RotateByAxisAngle(Vector3 v, Vector3 axis, float angle)

// Move Vector towards target
RMAPI Vector3 Vector3MoveTowards(Vector3 v, Vector3 target, float maxDistance)

// Calculate linear interpolation between two vectors
RMAPI Vector3 Vector3Lerp(Vector3 v1, Vector3 v2, float amount)

// Calculate cubic hermite interpolation between two vectors and their tangents
// as described in the GLTF 2.0 specification: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#interpolation-cubic
RMAPI Vector3 Vector3CubicHermite(Vector3 v1, Vector3 tangent1, Vector3 v2, Vector3 tangent2, float amount)

// Calculate reflected vector to normal
RMAPI Vector3 Vector3Reflect(Vector3 v, Vector3 normal)
'''

makeconnect("Vector3OrthoNormalize", [POINTER(Vector3), POINTER(Vector3)])
makeconnect("Vector3Transform", [Vector3, Matrix], Vector3)
makeconnect("Vector3RotateByQuaternion", [Vector3, Quaternion], Vector3)

makeconnect("Vector3RotateByAxisAngle", [Vector3, Vector3, c_float], Vector3)
makeconnect("Vector3MoveTowards", [Vector3, Vector3, c_float], Vector3)
makeconnect("Vector3Lerp", [Vector3, Vector3, c_float], Vector3)

makeconnect("Vector3CubicHermite", [Vector3, Vector3, Vector3, Vector3, c_float], Vector3)
makeconnect("Vector3Reflect", [Vector3, Vector3], Vector3)

'''
// Get min value for each pair of components
RMAPI Vector3 Vector3Min(Vector3 v1, Vector3 v2)

// Get max value for each pair of components
RMAPI Vector3 Vector3Max(Vector3 v1, Vector3 v2)

// Compute barycenter coordinates (u, v, w) for point p with respect to triangle (a, b, c)
// NOTE: Assumes P is on the plane of the triangle
RMAPI Vector3 Vector3Barycenter(Vector3 p, Vector3 a, Vector3 b, Vector3 c)

// Projects a Vector3 from screen space into object space
// NOTE: We are avoiding calling other raymath functions despite available
RMAPI Vector3 Vector3Unproject(Vector3 source, Matrix projection, Matrix view)

// Get Vector3 as float array
RMAPI float3 Vector3ToFloatV(Vector3 v)

// Invert the given vector
RMAPI Vector3 Vector3Invert(Vector3 v)

// Clamp the components of the vector between
// min and max values specified by the given vectors
RMAPI Vector3 Vector3Clamp(Vector3 v, Vector3 min, Vector3 max)

// Clamp the magnitude of the vector between two values
RMAPI Vector3 Vector3ClampValue(Vector3 v, float min, float max)
'''

makeconnect("Vector3Min", [Vector3, Vector3], Vector3)

makeconnect("Vector3Max", [Vector3, Vector3], Vector3)

makeconnect("Vector3Barycenter", [Vector3, Vector3, Vector3, Vector3], Vector3)
makeconnect("Vector3Unproject", [Vector3, Matrix, Matrix], Vector3)
makeconnect("Vector3ToFloatV", [Vector3], Float3)
makeconnect("Vector3Invert", [Vector3], Vector3)
makeconnect("Vector3Clamp", [Vector3, Vector3, Vector3], Vector3)
makeconnect("Vector3ClampValue", [Vector3, c_float, c_float], Vector3)

'''
// Check whether two given vectors are almost equal
RMAPI int Vector3Equals(Vector3 p, Vector3 q)

// Compute the direction of a refracted ray
// v: normalized direction of the incoming ray
// n: normalized normal vector of the interface of two optical media
// r: ratio of the refractive index of the medium from where the ray comes
//    to the refractive index of the medium on the other side of the surface
RMAPI Vector3 Vector3Refract(Vector3 v, Vector3 n, float r)
'''

makeconnect("Vector3Equals", [Vector3, Vector3], c_int)
makeconnect("Vector3Refract", [Vector3, Vector3, c_float], Vector3)

# --- Vector3 Orthonormalization & Transform Functions ------------------------

def vector3_ortho_normalize(v1: Vector3, v2: Vector3) -> None:
    lib.Vector3OrthoNormalize(byref(v1), byref(v2))

def vector3_transform(v: Vector3, m: Matrix) -> Vector3:
    return lib.Vector3Transform(v, m)

def vector3_rotate_by_quaternion(v: Vector3, q: Quaternion) -> Vector3:
    return lib.Vector3RotateByQuaternion(v, q)

def vector3_rotate_by_axis_angle(v: Vector3, axis: Vector3, angle: float) -> Vector3:
    return lib.Vector3RotateByAxisAngle(v, axis, angle)

def vector3_move_towards(v: Vector3, target: Vector3, max_dist: float) -> Vector3:
    return lib.Vector3MoveTowards(v, target, max_dist)

def vector3_lerp(v1: Vector3, v2: Vector3, amount: float) -> Vector3:
    return lib.Vector3Lerp(v1, v2, amount)

def vector3_cubic_hermite(a: Vector3, t1: Vector3, b: Vector3, t2: Vector3, amount: float) -> Vector3:
    return lib.Vector3CubicHermite(a, t1, b, t2, amount)

def vector3_reflect(v: Vector3, normal: Vector3) -> Vector3:
    return lib.Vector3Reflect(v, normal)

# --- Vector3 Min/Max & Utility Functions ------------------------------------

def vector3_min(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Min(v1, v2)

def vector3_max(v1: Vector3, v2: Vector3) -> Vector3:
    return lib.Vector3Max(v1, v2)

def vector3_barycenter(p: Vector3, a: Vector3, b: Vector3, c: Vector3) -> Vector3:
    return lib.Vector3Barycenter(p, a, b, c)

def vector3_unproject(source: Vector3, projection: Matrix, view: Matrix) -> Vector3:
    return lib.Vector3Unproject(source, projection, view)

def vector3_to_floatv(v: Vector3) -> list[float]:
    return list(lib.Vector3ToFloatV(v).v)

def vector3_invert(v: Vector3) -> Vector3:
    return lib.Vector3Invert(v)

def vector3_clamp(v: Vector3, minv: Vector3, maxv: Vector3) -> Vector3:
    return lib.Vector3Clamp(v, minv, maxv)

def vector3_clamp_value(v: Vector3, min_val: float, max_val: float) -> Vector3:
    return lib.Vector3ClampValue(v, min_val, max_val)

# --- Equals & Refract -------------------------------------------------------

def vector3_equals(a: Vector3, b: Vector3) -> bool:
    return bool(lib.Vector3Equals(a, b))

def vector3_refract(v: Vector3, n: Vector3, r: float) -> Vector3:
    return lib.Vector3Refract(v, n, r)

'''
    // Matrix math
    float MatrixDeterminant(Matrix mat);                                        // Compute matrix determinant
    float MatrixTrace(Matrix mat);                                              // Get the trace of the matrix (sum of the values along the diagonal)

    Matrix MatrixTranspose(Matrix mat);                                         // Transposes provided matrix
    Matrix MatrixInvert(Matrix mat);                                            // Invert provided matrix

    Matrix MatrixIdentity(void);                                                // Get identity matrix

    Matrix MatrixAdd(Matrix left, Matrix right);                                // Add two matrices
    Matrix MatrixSubtract(Matrix left, Matrix right);                           // Subtract two matrices (left - right)
    Matrix MatrixMultiply(Matrix left, Matrix right);                           // Get two matrix multiplication NOTE: When multiplying matrices... the order matters!

    Matrix MatrixTranslate(float x, float y, float z);                          // Get translation matrix
    Matrix MatrixRotate(Vector3 axis, float angle);                             // Create rotation matrix from axis and angle NOTE: Angle should be provided in radians

    Matrix MatrixRotateX(float angle);                                          // Get x-rotation matrix NOTE: Angle must be provided in radians
    Matrix MatrixRotateY(float angle);                                          // Get y-rotation matrix NOTE: Angle must be provided in radians
    Matrix MatrixRotateZ(float angle);                                          // Get z-rotation matrix NOTE: Angle must be provided in radians

    Matrix MatrixRotateXYZ(Vector3 angle);                                      // Get xyz-rotation matrix NOTE: Angle must be provided in radians
    Matrix MatrixRotateZYX(Vector3 angle);                                      // Get zyx-rotation matrix NOTE: Angle must be provided in radians

    Matrix MatrixScale(float x, float y, float z);                              // Get scaling matrix
    Matrix MatrixFrustum(double left, double right, double bottom, double top, double near, double far); // Get perspective projection matrix

    Matrix MatrixPerspective(double fovy, double aspect, double near, double far); // Get perspective projection matrix NOTE: Fovy angle must be provided in radians
    Matrix MatrixOrtho(double left, double right, double bottom, double top, double near, double far); // Get orthographic projection matrix
    Matrix MatrixLookAt(Vector3 eye, Vector3 target, Vector3 up);               // Get camera look-at matrix (view matrix)

    float16 MatrixToFloatV(Matrix mat);                                         // Get float array of matrix data

'''

makeconnect("MatrixDeterminant", [Matrix], c_float)
def matrix_determinant(mat: Matrix) -> float:
    return lib.MatrixDeterminant(mat)

makeconnect("MatrixTrace", [Matrix], c_float)
def matrix_trace(mat: Matrix) -> float:
    return lib.MatrixTrace(mat)

makeconnect("MatrixTranspose", [Matrix], Matrix)
def matrix_transpose(mat: Matrix) -> Matrix:
    return lib.MatrixTranspose(mat)

makeconnect("MatrixInvert", [Matrix], Matrix)
def matrix_invert(mat: Matrix) -> Matrix:
    return lib.MatrixInvert(mat)

makeconnect("MatrixIdentity", [], Matrix)
def matrix_identity() -> Matrix:
    return lib.MatrixIdentity()

makeconnect("MatrixAdd", [Matrix, Matrix], Matrix)
def matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return lib.MatrixAdd(left, right)

makeconnect("MatrixSubtract", [Matrix, Matrix], Matrix)
def matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return lib.MatrixSubtract(left, right)

makeconnect("MatrixMultiply", [Matrix, Matrix], Matrix)
def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return lib.MatrixMultiply(left, right)

makeconnect("MatrixTranslate", [c_float, c_float, c_float], Matrix)
makeconnect("MatrixRotate", [Vector3, c_float], Matrix)

makeconnect("MatrixRotateX", [c_float], Matrix)
makeconnect("MatrixRotateY", [c_float], Matrix)
makeconnect("MatrixRotateZ", [c_float], Matrix)

makeconnect("MatrixRotateXYZ", [Vector3], Matrix)
makeconnect("MatrixRotateZYX", [Vector3], Matrix)

makeconnect("MatrixScale", [c_float, c_float, c_float], Matrix)
makeconnect("MatrixFrustum", [c_double, c_double, c_double, c_double, c_double, c_double], Matrix)

makeconnect("MatrixPerspective", [c_double, c_double, c_double, c_double], Matrix)
makeconnect("MatrixOrtho", [c_double, c_double, c_double, c_double, c_double, c_double], Matrix)

makeconnect("MatrixLookAt", [Vector3, Vector3, Vector3], Matrix)

makeconnect("MatrixToFloatV", [Matrix], Float16)
def matrix_to_float_v(mat: Matrix) -> list[float]:
    dad = lib.MatrixToFloatV(mat)
    return list(dad.v)

'''
    // Quaternion math
    Quaternion QuaternionAdd(Quaternion q1, Quaternion q2);                     // Add two quaternions
    Quaternion QuaternionAddValue(Quaternion q, float add);                     // Add quaternion and float value

    Quaternion QuaternionSubtract(Quaternion q1, Quaternion q2);                // Subtract two quaternions
    Quaternion QuaternionSubtractValue(Quaternion q, float sub);                // Subtract quaternion and float value

    Quaternion QuaternionIdentity(void);                                        // Get identity quaternion
    float QuaternionLength(Quaternion q);                                       // Computes the length of a quaternion

    Quaternion QuaternionNormalize(Quaternion q);                               // Normalize provided quaternion
    Quaternion QuaternionInvert(Quaternion q);                                  // Invert provided quaternion
    Quaternion QuaternionMultiply(Quaternion q1, Quaternion q2);                // Calculate two quaternion multiplication
    Quaternion QuaternionScale(Quaternion q, float mul);                        // Scale quaternion by float value
    Quaternion QuaternionDivide(Quaternion q1, Quaternion q2);                  // Divide two quaternions
    Quaternion QuaternionLerp(Quaternion q1, Quaternion q2, float amount);      // Calculate linear interpolation between two quaternions
    Quaternion QuaternionNlerp(Quaternion q1, Quaternion q2, float amount);     // Calculate slerp-optimized interpolation between two quaternions
    Quaternion QuaternionSlerp(Quaternion q1, Quaternion q2, float amount);     // Calculates spherical linear interpolation between two quaternions
    Quaternion QuaternionFromVector3ToVector3(Vector3 from, Vector3 to);        // Calculate quaternion based on the rotation from one vector to another
    Quaternion QuaternionFromMatrix(Matrix mat);                                // Get a quaternion for a given rotation matrix
    Matrix QuaternionToMatrix(Quaternion q);                                    // Get a matrix for a given quaternion
    Quaternion QuaternionFromAxisAngle(Vector3 axis, float angle);              // Get rotation quaternion for an angle and axis NOTE: Angle must be provided in radians
    void QuaternionToAxisAngle(Quaternion q, Vector3 *outAxis, float *outAngle); // Get the rotation angle and axis for a given quaternion
    Quaternion QuaternionFromEuler(float pitch, float yaw, float roll);         // Get the quaternion equivalent to Euler angles NOTE: Rotation order is ZYX
    Vector3 QuaternionToEuler(Quaternion q);                                    // Get the Euler angles equivalent to quaternion (roll, pitch, yaw) NOTE: Angles are returned in a Vector3 struct in radians
    Quaternion QuaternionTransform(Quaternion q, Matrix mat);                   // Transform a quaternion given a transformation matrix
    int QuaternionEquals(Quaternion p, Quaternion q);                           // Check whether two given quaternions are almost equal
'''

