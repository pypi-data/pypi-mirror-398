from ._classes import *




"""
RLAPI bool CheckCollisionSpheres(Vector3 center1, float radius1, Vector3 center2, float radius2); // Check collision between two spheres
RLAPI bool CheckCollisionBoxes(BoundingBox box1, BoundingBox box2);                         // Check collision between two bounding boxes
RLAPI bool CheckCollisionBoxSphere(BoundingBox box, Vector3 center, float radius);          // Check collision between box and sphere
RLAPI RayCollision GetRayCollisionSphere(Ray ray, Vector3 center, float radius);            // Get collision info between ray and sphere
RLAPI RayCollision GetRayCollisionBox(Ray ray, BoundingBox box);                            // Get collision info between ray and box
RLAPI RayCollision GetRayCollisionMesh(Ray ray, Mesh mesh, Matrix transform);               // Get collision info between ray and mesh
RLAPI RayCollision GetRayCollisionTriangle(Ray ray, Vector3 p1, Vector3 p2, Vector3 p3);    // Get collision info between ray and triangle
RLAPI RayCollision GetRayCollisionQuad(Ray ray, Vector3 p1, Vector3 p2, Vector3 p3, Vector3 p4); // Get collision info between ray and quad
"""
makeconnect("CheckCollisionSpheres", [Vector3, c_float, Vector3, c_float], c_bool)
def check_collision_spheres(center1:Vector3, radius1:float, center2:Vector3, radius2:float) -> bool:
    return lib.CheckCollisionSpheres(center1, radius1, center2, radius2)

makeconnect("CheckCollisionBoxes", [BoundingBox, BoundingBox], c_bool)
def check_collision_boxes(box1: BoundingBox, box2: BoundingBox) -> bool:
    return lib.CheckCollisionBoxes(box1, box2)

makeconnect("CheckCollisionBoxSphere", [BoundingBox, Vector3, c_float], c_bool)
def check_collision_box_sphere(box: BoundingBox, center: Vector3, radius: float) -> bool:
    return lib.CheckCollisionBoxSphere(box, center, radius)

makeconnect("GetRayCollisionSphere", [Ray, Vector3, c_float], RayCollision)
def get_ray_collision_sphere(ray: Ray, center: Vector3, radius: float) -> RayCollision:
    return lib.GetRayCollisionSphere(ray, center, radius)

makeconnect("GetRayCollisionBox", [Ray, BoundingBox], RayCollision)
def get_ray_collision_box(ray: Ray, box: BoundingBox) -> RayCollision:
    return lib.GetRayCollisionBox(ray, box)

makeconnect("GetRayCollisionMesh", [Ray, Mesh, Matrix], RayCollision)
def get_ray_collision_mesh(ray: Ray, mesh: Mesh, transform: Matrix) -> RayCollision:
    return lib.GetRayCollisionMesh(ray, mesh, transform)

makeconnect("GetRayCollisionTriangle", [Ray, Vector3, Vector3, Vector3], RayCollision)
def get_ray_collision_triangle(ray: Ray, p1: Vector3, p2: Vector3, p3: Vector3) -> RayCollision:
    return lib.GetRayCollisionTriangle(ray, p1, p2, p3)

makeconnect("GetRayCollisionQuad", [Ray, Vector3, Vector3, Vector3, Vector3], RayCollision)
def get_ray_collision_quad(ray: Ray, p1: Vector3, p2: Vector3, p3: Vector3, p4: Vector3) -> RayCollision:
    return lib.GetRayCollisionQuad(ray, p1, p2, p3, p4)
"""
RLAPI bool CheckCollisionRecs(Rectangle rec1, Rectangle rec2);                                           // Check collision between two rectangles
RLAPI bool CheckCollisionCircles(Vector2 center1, float radius1, Vector2 center2, float radius2);        // Check collision between two circles
RLAPI bool CheckCollisionCircleRec(Vector2 center, float radius, Rectangle rec);                         // Check collision between circle and rectangle

RLAPI bool CheckCollisionCircleLine(Vector2 center, float radius, Vector2 p1, Vector2 p2);               // Check if circle collides with a line created betweeen two points [p1] and [p2]

RLAPI bool CheckCollisionPointRec(Vector2 point, Rectangle rec);                                         // Check if point is inside rectangle
RLAPI bool CheckCollisionPointCircle(Vector2 point, Vector2 center, float radius);                       // Check if point is inside circle

RLAPI bool CheckCollisionPointTriangle(Vector2 point, Vector2 p1, Vector2 p2, Vector2 p3);               // Check if point is inside a triangle
RLAPI bool CheckCollisionPointLine(Vector2 point, Vector2 p1, Vector2 p2, int threshold);                // Check if point belongs to line created between two points [p1] and [p2] with defined margin in pixels [threshold]

RLAPI bool CheckCollisionPointPoly(Vector2 point, const Vector2 *points, int pointCount);                // Check if point is within a polygon described by array of vertices

RLAPI bool CheckCollisionLines(Vector2 startPos1, Vector2 endPos1, Vector2 startPos2, Vector2 endPos2, Vector2 *collisionPoint); // Check the collision between two lines defined by two points each, returns collision point by reference
RLAPI Rectangle GetCollisionRec(Rectangle rec1, Rectangle rec2);                                         // Get collision rectangle for two rectangles collision
"""

makeconnect("CheckCollisionRecs", [Rectangle, Rectangle], c_bool)
def check_collision_recs(rec1: Rectangle, rec2: Rectangle) -> bool:
    return lib.CheckCollisionRecs(rec1, rec2)

makeconnect("CheckCollisionCircles", [Vector2, c_float, Vector2, c_float], c_bool)
def check_collision_circles(center1: Vector2, radius1: float, center2: Vector2, radius2: float) -> bool:
    return lib.CheckCollisionCircles(center1, radius1, center2, radius2)

makeconnect("CheckCollisionCircleRec", [Vector2, c_float, Rectangle], c_bool)
def check_collision_circle_rec(center: Vector2, radius: float, rec: Rectangle) -> bool:
    return lib.CheckCollisionCircleRec(center, radius, rec)

makeconnect("CheckCollisionCircleLine", [Vector2, c_float, Vector2, Vector2], c_bool)
def check_collision_circle_line(center: Vector2, radius: float, p1: Vector2, p2: Vector2) -> bool:
    return lib.CheckCollisionCircleLine(center, radius, p1, p2)

makeconnect("CheckCollisionPointRec", [Vector2, Rectangle], c_bool)
def check_collision_point_rec(center: Vector2, rec: Rectangle) -> bool:
    return lib.CheckCollisionPointRec(center, rec)

makeconnect("CheckCollisionPointCircle", [Vector2, Vector2, c_float], c_bool)
def check_collision_point_circle(point: Vector2, center: Vector2, radius: float) -> bool:
    return lib.CheckCollisionPointCircle(point, center, radius)

makeconnect("CheckCollisionPointTriangle", [Vector2, Vector2, Vector2, Vector2], c_bool)
def check_collision_point_triangle(point: Vector2, p1: Vector2, p2: Vector2, p3: Vector2):
    return lib.CheckCollisionPointTriangle(point, p1, p2, p3)

makeconnect("CheckCollisionPointLine", [Vector2, Vector2, Vector2, c_int], c_bool)
def check_collision_point_line(point: Vector2, p1: Vector2, p2: Vector2, threshold: int) -> bool:
    return lib.CheckCollisionPointLine(point, p1, p2, threshold)

makeconnect("CheckCollisionPointPoly", [Vector2, POINTER(Vector2), c_int], c_bool)
def check_collision_point_poly(point: Vector2, points: list[Vector2]) -> bool:
    arr = Vector2 * len(points)
    meow = arr(*points)
    return lib.CheckCollisionPointPoly(point, meow, len(points))

makeconnect("CheckCollisionLines", [Vector2, Vector2, Vector2, Vector2, POINTER(Vector2)], c_bool)
def check_collision_lines(start_pos1: Vector2, end_pos1: Vector2, start_pos2: Vector2, end_pos2: Vector2, collision_point: Vector2) -> bool:
    return lib.CheckCollisionLines(start_pos1, end_pos1, start_pos2, end_pos2, byref(collision_point))

makeconnect("GetCollisionRec", [Rectangle, Rectangle], Rectangle)
def get_collision_rec(rec1: Rectangle, rec2: Rectangle) -> Rectangle:
    return lib.GetCollisionRec(rec1, rec2)

