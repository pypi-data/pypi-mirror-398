from ._classes import *










# void ClearBackground(Color color)
lib.ClearBackground.argtypes = [Color]
def clear_background(color: Color):
    "Set background color (framebuffer clear color)"
    lib.ClearBackground(color)

# BeginDrawing()
def begin_drawing():
    "Setup canvas (framebuffer) to start drawing"
    lib.BeginDrawing()

# EndDrawing()
def end_drawing():
    "End canvas drawing and swap buffers (double buffering)"
    lib.EndDrawing()

makeconnect("BeginMode2D", [Camera2D])
def begin_mode_2d(camera: Camera2D):
    "Begin 2D mode with custom camera (2D)"
    lib.BeginMode2D(camera)

def end_mode_2d():
    "Ends 2D mode with custom camera"
    lib.EndMode2D()

makeconnect("BeginMode3D", [Camera3D])
def begin_mode_3d(camera: Camera3D):
    lib.BeginMode3D(camera)

makeconnect("EndMode3D")
end_mode_3d = lib.EndMode3D
"Ends 3D mode and returns to default 2D orthographic mode"


makeconnect("BeginTextureMode", [RenderTexture]) # RenderTexture2D
def begin_texture_mode(target: RenderTexture):
    lib.BeginTextureMode(target)

end_texture_mode = lib.EndTextureMode
"Ends drawing to render texture"

'''
RLAPI void BeginMode2D(Camera2D camera);                          // Begin 2D mode with custom camera (2D)
RLAPI void EndMode2D(void);                                       // Ends 2D mode with custom camera
RLAPI void BeginMode3D(Camera3D camera);                          // Begin 3D mode with custom camera (3D)
RLAPI void EndMode3D(void);                                       // Ends 3D mode and returns to default 2D orthographic mode
RLAPI void BeginTextureMode(RenderTexture2D target);              // Begin drawing to render texture
RLAPI void EndTextureMode(void);                                  // Ends drawing to render texture

RLAPI void BeginShaderMode(Shader shader);                        // Begin custom shader drawing
RLAPI void EndShaderMode(void);                                   // End custom shader drawing (use default shader)


RLAPI void BeginBlendMode(int mode);                              // Begin blending mode (alpha, additive, multiplied, subtract, custom)
RLAPI void EndBlendMode(void);                                    // End blending mode (reset to default: alpha blending)
RLAPI void BeginScissorMode(int x, int y, int width, int height); // Begin scissor mode (define screen area for following drawing)
RLAPI void EndScissorMode(void);                                  // End scissor mode
RLAPI void BeginVrStereoMode(VrStereoConfig config);              // Begin stereo rendering (requires VR simulator)
RLAPI void EndVrStereoMode(void);  
'''

makeconnect("BeginShaderMode", [Shader])
def begin_shader_mode(shader: Shader):
    lib.BeginShaderMode(shader)

end_shader_mode = lib.EndShaderMode
"End custom shader drawing (use default shader)"




'''
// Basic shapes drawing functions
RLAPI void DrawPixel(int posX, int posY, Color color);                                                   // Draw a pixel using geometry [Can be slow, use with care]
RLAPI void DrawPixelV(Vector2 position, Color color);                                                    // Draw a pixel using geometry (Vector version) [Can be slow, use with care]
RLAPI void DrawLine(int startPosX, int startPosY, int endPosX, int endPosY, Color color);                // Draw a line
RLAPI void DrawLineV(Vector2 startPos, Vector2 endPos, Color color);                                     // Draw a line (using gl lines)
RLAPI void DrawLineEx(Vector2 startPos, Vector2 endPos, float thick, Color color);                       // Draw a line (using triangles/quads)
RLAPI void DrawLineStrip(const Vector2 *points, int pointCount, Color color);                            // Draw lines sequence (using gl lines)

RLAPI void DrawLineBezier(Vector2 startPos, Vector2 endPos, float thick, Color color);                   // Draw line segment cubic-bezier in-out interpolation






RLAPI void DrawCircle(int centerX, int centerY, float radius, Color color);                              // Draw a color-filled circle
RLAPI void DrawCircleSector(Vector2 center, float radius, float startAngle, float endAngle, int segments, Color color);      // Draw a piece of a circle
RLAPI void DrawCircleSectorLines(Vector2 center, float radius, float startAngle, float endAngle, int segments, Color color); // Draw circle sector outline

RLAPI void DrawCircleGradient(int centerX, int centerY, float radius, Color inner, Color outer);         // Draw a gradient-filled circle

RLAPI void DrawCircleV(Vector2 center, float radius, Color color);                                       // Draw a color-filled circle (Vector version)
RLAPI void DrawCircleLines(int centerX, int centerY, float radius, Color color);                         // Draw circle outline
RLAPI void DrawCircleLinesV(Vector2 center, float radius, Color color);                                  // Draw circle outline (Vector version)


RLAPI void DrawEllipse(int centerX, int centerY, float radiusH, float radiusV, Color color);             // Draw ellipse
RLAPI void DrawEllipseV(Vector2 center, float radiusH, float radiusV, Color color);                      // Draw ellipse (Vector version)
RLAPI void DrawEllipseLines(int centerX, int centerY, float radiusH, float radiusV, Color color);        // Draw ellipse outline
RLAPI void DrawEllipseLinesV(Vector2 center, float radiusH, float radiusV, Color color);                 // Draw ellipse outline (Vector version)

RLAPI void DrawRing(Vector2 center, float innerRadius, float outerRadius, float startAngle, float endAngle, int segments, Color color); // Draw ring
RLAPI void DrawRingLines(Vector2 center, float innerRadius, float outerRadius, float startAngle, float endAngle, int segments, Color color);    // Draw ring outline

RLAPI void DrawRectangle(int posX, int posY, int width, int height, Color color);                        // Draw a color-filled rectangle
RLAPI void DrawRectangleV(Vector2 position, Vector2 size, Color color);                                  // Draw a color-filled rectangle (Vector version)
RLAPI void DrawRectangleRec(Rectangle rec, Color color);                                                 // Draw a color-filled rectangle
RLAPI void DrawRectanglePro(Rectangle rec, Vector2 origin, float rotation, Color color);                 // Draw a color-filled rectangle with pro parameters
RLAPI void DrawRectangleGradientV(int posX, int posY, int width, int height, Color top, Color bottom);   // Draw a vertical-gradient-filled rectangle
RLAPI void DrawRectangleGradientH(int posX, int posY, int width, int height, Color left, Color right);   // Draw a horizontal-gradient-filled rectangle
RLAPI void DrawRectangleGradientEx(Rectangle rec, Color topLeft, Color bottomLeft, Color bottomRight, Color topRight); // Draw a gradient-filled rectangle with custom vertex colors
RLAPI void DrawRectangleLines(int posX, int posY, int width, int height, Color color);                   // Draw rectangle outline
RLAPI void DrawRectangleLinesEx(Rectangle rec, float lineThick, Color color);                            // Draw rectangle outline with extended parameters
RLAPI void DrawRectangleRounded(Rectangle rec, float roundness, int segments, Color color);              // Draw rectangle with rounded edges
RLAPI void DrawRectangleRoundedLines(Rectangle rec, float roundness, int segments, Color color);         // Draw rectangle lines with rounded edges
RLAPI void DrawRectangleRoundedLinesEx(Rectangle rec, float roundness, int segments, float lineThick, Color color); // Draw rectangle with rounded edges outline

RLAPI void DrawTriangle(Vector2 v1, Vector2 v2, Vector2 v3, Color color);                                // Draw a color-filled triangle (vertex in counter-clockwise order!)
RLAPI void DrawTriangleLines(Vector2 v1, Vector2 v2, Vector2 v3, Color color);                           // Draw triangle outline (vertex in counter-clockwise order!)
RLAPI void DrawTriangleFan(const Vector2 *points, int pointCount, Color color);                          // Draw a triangle fan defined by points (first vertex is the center)
RLAPI void DrawTriangleStrip(const Vector2 *points, int pointCount, Color color);                        // Draw a triangle strip defined by points

RLAPI void DrawPoly(Vector2 center, int sides, float radius, float rotation, Color color);               // Draw a regular polygon (Vector version)
RLAPI void DrawPolyLines(Vector2 center, int sides, float radius, float rotation, Color color);          // Draw a polygon outline of n sides
RLAPI void DrawPolyLinesEx(Vector2 center, int sides, float radius, float rotation, float lineThick, Color color); // Draw a polygon outline of n sides with extended parameters

// Splines drawing functions
RLAPI void DrawSplineLinear(const Vector2 *points, int pointCount, float thick, Color color);            // Draw spline: Linear, minimum 2 points
RLAPI void DrawSplineBasis(const Vector2 *points, int pointCount, float thick, Color color);             // Draw spline: B-Spline, minimum 4 points
RLAPI void DrawSplineCatmullRom(const Vector2 *points, int pointCount, float thick, Color color);        // Draw spline: Catmull-Rom, minimum 4 points
RLAPI void DrawSplineBezierQuadratic(const Vector2 *points, int pointCount, float thick, Color color);   // Draw spline: Quadratic Bezier, minimum 3 points (1 control point): [p1, c2, p3, c4...]
RLAPI void DrawSplineBezierCubic(const Vector2 *points, int pointCount, float thick, Color color);       // Draw spline: Cubic Bezier, minimum 4 points (2 control points): [p1, c2, c3, p4, c5, c6...]
RLAPI void DrawSplineSegmentLinear(Vector2 p1, Vector2 p2, float thick, Color color);                    // Draw spline segment: Linear, 2 points
RLAPI void DrawSplineSegmentBasis(Vector2 p1, Vector2 p2, Vector2 p3, Vector2 p4, float thick, Color color); // Draw spline segment: B-Spline, 4 points
RLAPI void DrawSplineSegmentCatmullRom(Vector2 p1, Vector2 p2, Vector2 p3, Vector2 p4, float thick, Color color); // Draw spline segment: Catmull-Rom, 4 points
RLAPI void DrawSplineSegmentBezierQuadratic(Vector2 p1, Vector2 c2, Vector2 p3, float thick, Color color); // Draw spline segment: Quadratic Bezier, 2 points, 1 control point
RLAPI void DrawSplineSegmentBezierCubic(Vector2 p1, Vector2 c2, Vector2 c3, Vector2 p4, float thick, Color color); // Draw spline segment: Cubic Bezier, 2 points, 2 control points
'''

makeconnect("DrawPixel", [c_int, c_int, Color])
def draw_pixel(x: int, y: int, color: Color):
    lib.DrawPixel(x, y, color)

makeconnect("DrawPixelV", [Vector2, Color])
def draw_pixel_v(pos: Vector2, color: Color):
    lib.DrawPixelV(pos, color)

makeconnect("DrawLine", [c_int, c_int, c_int, c_int, Color])
def draw_line(x1: c_int, y1: c_int, x2: c_int, y2: c_int, color: Color):
    lib.DrawLine(x1, y1, x2, y2, color)

makeconnect("DrawLineV", [Vector2, Vector2, Color])
def draw_line_v(pos1: Vector2, pos2: Vector2, color: Color):
    lib.DrawLineV(pos1, pos2, color)

makeconnect("DrawLineEx", [Vector2, Vector2, c_float, Color])
def draw_line_ex(pos1: Vector2, pos2: Vector2, thick: float, color: Color):
    lib.DrawLineEx(pos1, pos2, thick, color)

makeconnect("DrawLineStrip", [POINTER(Vector2), c_int, Color])
"RLAPI void DrawLineStrip(const Vector2 *points, int pointCount, Color color);                            // Draw lines sequence (using gl lines)"

makeconnect("DrawLineBezier", [Vector2, Vector2, c_float, Color])
def draw_line_bezier(pos1: Vector2, pos2: Vector2, thick: float, color: Color):
    lib.DrawLineBezier(pos1, pos2, thick, color)

makeconnect("DrawCircle", [c_int, c_int, c_float, Color])
def draw_circle(center_x: int, center_y: int, radius: float, color: Color):
    lib.DrawCircle(center_x, center_y, radius, color)

makeconnect("DrawCircleSector", [Vector2, c_float, c_float, c_float, c_int, Color])
def draw_circle_sector(center: Vector2, radius: float, start_angle: float, end_angle: float, segments: int, color: Color):
    lib.DrawCircleSector(center, radius, start_angle, end_angle, segments, color)

makeconnect("DrawCircleSectorLines", [Vector2, c_float, c_float, c_float, c_int, Color])
def draw_circle_sector_lines(center: Vector2, radius: float, start_angle: float, end_angle: float, segments: int, color: Color):
    lib.DrawCircleSectorLines(center, radius, start_angle, end_angle, segments, color)

makeconnect("DrawCircleGradient", [c_int, c_int, c_float, Color, Color])
def draw_circle_gradient(center_x: int, center_y: int, radius: float, inner: Color, outer: Color):
    lib.DrawCircleGradient(center_x, center_y, radius, inner, outer)

makeconnect("DrawCircleV", [Vector2, c_float, Color])
def draw_circle_v(center: Vector2, radius: float, color: Color):
    lib.DrawCircleV(center, radius, color)

makeconnect("DrawCircleLines", [c_int, c_int, c_float, Color])
def draw_circle_lines(center_x: int, center_y: int, radius: float, color: Color):
    lib.DrawCircleLines(center_x, center_y, radius, color)

makeconnect("DrawCircleLinesV", [Vector2, c_float, Color])
def draw_circle_lines_v(center: Vector2, radius: float, color: Color):
    lib.DrawCircleLinesV(center, radius, color)

'''
RLAPI void DrawEllipse(int centerX, int centerY, float radiusH, float radiusV, Color color);             // Draw ellipse
RLAPI void DrawEllipseV(Vector2 center, float radiusH, float radiusV, Color color);                      // Draw ellipse (Vector version)
RLAPI void DrawEllipseLines(int centerX, int centerY, float radiusH, float radiusV, Color color);        // Draw ellipse outline
RLAPI void DrawEllipseLinesV(Vector2 center, float radiusH, float radiusV, Color color);                 // Draw ellipse outline (Vector version)
'''

makeconnect("DrawEllipse", [c_int, c_int, c_float, c_float, Color])
def draw_ellipse(center_x: int, center_y: int, radius_h: float, radius_v: float, color: Color):
    lib.DrawEllipse(center_x, center_y, radius_h, radius_v, color)
'''
makeconnect("DrawEllipseV", [c_int, c_int, c_float, c_float, Color])
def draw_ellipse_v(center: Vector2, radius_h: float, radius_v: float, color: Color):
    lib.DrawEllipseV(center, radius_h, radius_v, color)
'''
makeconnect("DrawEllipseLines", [c_int, c_int, c_float, c_float, Color])
def draw_ellipse_lines(center_x: int, center_y: int, radius_h: float, radius_v: float, color: Color):
    lib.DrawEllipseLines(center_x, center_y, radius_h, radius_v, color)
'''
makeconnect("DrawEllipseLinesV", [c_int, c_int, c_float, c_float, Color])
def draw_ellipse_lines_v(center: Vector2, radius_h: float, radius_v: float, color: Color):
    lib.DrawEllipseLinesV(center, radius_h, radius_v, color)
'''

'''
RLAPI void DrawRing(Vector2 center, float innerRadius, float outerRadius, float startAngle, float endAngle, int segments, Color color); // Draw ring
RLAPI void DrawRingLines(Vector2 center, float innerRadius, float outerRadius, float startAngle, float endAngle, int segments, Color color);    // Draw ring outline
'''

makeconnect("DrawRing", [Vector2, c_float, c_float, c_float, c_float, c_int, Color])
def draw_ring(center: Vector2, inner_radius: float, outer_radius: float, start_angle: float, end_angle: float, segments: int, color: Color):
    lib.DrawRing(center, inner_radius, outer_radius, start_angle, end_angle, segments, color)

makeconnect("DrawRingLines", [Vector2, c_float, c_float, c_float, c_float, c_int, Color])
def draw_ring_lines(center: Vector2, inner_radius: float, outer_radius: float, start_angle: float, end_angle: float, segments: int, color: Color):
    lib.DrawRingLines(center, inner_radius, outer_radius, start_angle, end_angle, segments, color)

'''
RLAPI void DrawRectangle(int posX, int posY, int width, int height, Color color);                        // Draw a color-filled rectangle
RLAPI void DrawRectangleV(Vector2 position, Vector2 size, Color color);                                  // Draw a color-filled rectangle (Vector version)
RLAPI void DrawRectangleRec(Rectangle rec, Color color);                                                 // Draw a color-filled rectangle

RLAPI void DrawRectanglePro(Rectangle rec, Vector2 origin, float rotation, Color color);                 // Draw a color-filled rectangle with pro parameters

RLAPI void DrawRectangleGradientV(int posX, int posY, int width, int height, Color top, Color bottom);   // Draw a vertical-gradient-filled rectangle
RLAPI void DrawRectangleGradientH(int posX, int posY, int width, int height, Color left, Color right);   // Draw a horizontal-gradient-filled rectangle
RLAPI void DrawRectangleGradientEx(Rectangle rec, Color topLeft, Color bottomLeft, Color bottomRight, Color topRight); // Draw a gradient-filled rectangle with custom vertex colors

RLAPI void DrawRectangleLines(int posX, int posY, int width, int height, Color color);                   // Draw rectangle outline
RLAPI void DrawRectangleLinesEx(Rectangle rec, float lineThick, Color color);                            // Draw rectangle outline with extended parameters

RLAPI void DrawRectangleRounded(Rectangle rec, float roundness, int segments, Color color);              // Draw rectangle with rounded edges
RLAPI void DrawRectangleRoundedLines(Rectangle rec, float roundness, int segments, Color color);         // Draw rectangle lines with rounded edges
RLAPI void DrawRectangleRoundedLinesEx(Rectangle rec, float roundness, int segments, float lineThick, Color color); // Draw rectangle with rounded edges outline
'''

makeconnect("DrawRectangle", [c_int, c_int, c_int, c_int, Color])
def draw_rectangle(x: int, y: int, width: int, height: int, color: Color):
    lib.DrawRectangle(x, y, width, height, color)

makeconnect("DrawRectangleV", [Vector2, Vector2, Color])
def draw_rectangle_v(pos: Vector2, size: Vector2, color: Color):
    lib.DrawRectangleV(pos, size, color)

makeconnect("DrawRectangleRec", [Rectangle, Color])
def draw_rectangle_rec(rec: Rectangle, color: Color):
    lib.DrawRectangleRec(rec, color)

makeconnect("DrawRectanglePro", [Rectangle, Vector2, c_float, Color])
def draw_rectangle_pro(rec: Rectangle, origin: Vector2, rotation: c_float, color: Color):
    lib.DrawRectanglePro(rec, origin, rotation, color)

makeconnect("DrawRectangleGradientV", [c_int, c_int, c_int, c_int, Color, Color])
def draw_rectangle_gradient_v(x: int, y: int, width: int, height: int, top: Color, bottom: Color):
    lib.DrawRectangleGradientV(x, y, width, height, top, bottom)

makeconnect("DrawRectangleGradientH", [c_int, c_int, c_int, c_int, Color, Color])
def draw_rectangle_gradient_h(x: int, y: int, width: int, height: int, left: Color, right: Color):
    lib.DrawRectangleGradientH(x, y, width, height, left, right)

makeconnect("DrawRectangleGradientEx", [Rectangle, Color, Color, Color, Color])
def draw_rectangle_gradient_ex(rec: Rectangle, top_left: Color, bottom_left: Color, bottom_right: Color, top_right: Color):
    lib.DrawRectangleGradientEx(rec, top_left, bottom_left, bottom_right, top_right)

makeconnect("DrawRectangleLines", [c_int, c_int, c_int, c_int, Color])
def draw_rectangle_lines(x: int, y: int, width: int, height: int, color: Color):
    lib.DrawRectangleLines(x, y, width, height, color)

makeconnect("DrawRectangleLinesEx", [Rectangle, c_float, Color])
def draw_rectangle_lines_ex(rec: Rectangle, line_thick: float, color: Color):
    lib.DrawRectangleLinesEx(rec, line_thick, color)

'''
RLAPI void DrawRectangleRounded(Rectangle rec, float roundness, int segments, Color color);              // Draw rectangle with rounded edges
RLAPI void DrawRectangleRoundedLines(Rectangle rec, float roundness, int segments, Color color);         // Draw rectangle lines with rounded edges
RLAPI void DrawRectangleRoundedLinesEx(Rectangle rec, float roundness, int segments, float lineThick, Color color); // Draw rectangle with rounded edges outline
'''

makeconnect("DrawRectangleRounded", [Rectangle, c_float, c_int, Color])
def draw_rectangle_rounded(rec: Rectangle, roundness: float, segments: int, color: Color):
    lib.DrawRectangleRounded(rec, roundness, segments, color)

makeconnect("DrawRectangleRoundedLines", [Rectangle, c_float, c_int, Color])
def draw_rectangle_rounded_lines(rec: Rectangle, roundness: float, segments: int, color: Color):
    lib.DrawRectangleRoundedLines(rec, roundness, segments, color)

makeconnect("DrawRectangleRoundedLinesEx", [Rectangle, c_float, c_int, c_float, Color])
def draw_rectangle_rounded_lines_ex(rec: Rectangle, roundness: float, segments: int, line_thick: float, color: Color):
    lib.DrawRectangleRoundedLinesEx(rec, roundness, segments, line_thick, color)

'''
RLAPI void DrawTriangle(Vector2 v1, Vector2 v2, Vector2 v3, Color color);                                // Draw a color-filled triangle (vertex in counter-clockwise order!)
RLAPI void DrawTriangleLines(Vector2 v1, Vector2 v2, Vector2 v3, Color color);                           // Draw triangle outline (vertex in counter-clockwise order!)
RLAPI void DrawTriangleFan(const Vector2 *points, int pointCount, Color color);                          // Draw a triangle fan defined by points (first vertex is the center)
RLAPI void DrawTriangleStrip(const Vector2 *points, int pointCount, Color color);                        // Draw a triangle strip defined by points
'''

makeconnect("DrawTriangle", [Vector2, Vector2, Vector2, Color])
def draw_triangle(v1: Vector2, v2: Vector2, v3: Vector2, color: Color):
    lib.DrawTriangle(v1, v2, v3, color)

makeconnect("DrawTriangleLines", [Vector2, Vector2, Vector2, Color])
def draw_triangle_lines(v1: Vector2, v2: Vector2, v3: Vector2, color: Color):
    lib.DrawTriangleLines(v1, v2, v3, color)

makeconnect("DrawTriangleFan", [POINTER(Vector2), c_int, Color])
def draw_triangle_fan(points: list[Vector2], color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawTriangleFan(c_points, count, color)

makeconnect("DrawTriangleStrip", [POINTER(Vector2), c_int, Color])
def draw_triangle_strip(points: list[Vector2], color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawTriangleStrip(c_points, count, color)

'''
RLAPI void DrawPoly(Vector2 center, int sides, float radius, float rotation, Color color);               // Draw a regular polygon (Vector version)
RLAPI void DrawPolyLines(Vector2 center, int sides, float radius, float rotation, Color color);          // Draw a polygon outline of n sides
RLAPI void DrawPolyLinesEx(Vector2 center, int sides, float radius, float rotation, float lineThick, Color color); // Draw a polygon outline of n sides with extended parameters
'''

makeconnect("DrawPoly", [Vector2, c_int, c_float, c_float, Color])
def draw_poly(center: Vector2, sides: int, radius: float, rotation: float, color: Color):
    lib.DrawPoly(center, sides, radius, rotation, color)

makeconnect("DrawPolyLines", [Vector2, c_int, c_float, c_float, Color])
def draw_poly_lines(center: Vector2, sides: int, radius: float, rotation: float, color: Color):
    lib.DrawPolyLines(center, sides, radius, rotation, color)

makeconnect("DrawPolyLinesEx", [Vector2, c_int, c_float, c_float, c_float, Color])
def draw_poly_lines_ex(center: Vector2, sides: int, radius: float, rotation: float, line_thick: float, color: Color):
    lib.DrawPolyLinesEx(center, sides, radius, rotation, line_thick, color)

'''
// Splines drawing functions
RLAPI void DrawSplineLinear(const Vector2 *points, int pointCount, float thick, Color color);            // Draw spline: Linear, minimum 2 points
RLAPI void DrawSplineBasis(const Vector2 *points, int pointCount, float thick, Color color);             // Draw spline: B-Spline, minimum 4 points

RLAPI void DrawSplineCatmullRom(const Vector2 *points, int pointCount, float thick, Color color);        // Draw spline: Catmull-Rom, minimum 4 points
RLAPI void DrawSplineBezierQuadratic(const Vector2 *points, int pointCount, float thick, Color color);   // Draw spline: Quadratic Bezier, minimum 3 points (1 control point): [p1, c2, p3, c4...]
RLAPI void DrawSplineBezierCubic(const Vector2 *points, int pointCount, float thick, Color color);       // Draw spline: Cubic Bezier, minimum 4 points (2 control points): [p1, c2, c3, p4, c5, c6...]

RLAPI void DrawSplineSegmentLinear(Vector2 p1, Vector2 p2, float thick, Color color);                    // Draw spline segment: Linear, 2 points

RLAPI void DrawSplineSegmentBasis(Vector2 p1, Vector2 p2, Vector2 p3, Vector2 p4, float thick, Color color); // Draw spline segment: B-Spline, 4 points
RLAPI void DrawSplineSegmentCatmu(Vector2 p1, Vector2 p2, Vector2 p3, Vector2 p4, float thick, Color color); // Draw spline segment: Catmull-Rom, 4 points

RLAPI void DrawSplineSegmentBezierQuadratic(Vector2 p1, Vector2 c2, Vector2 p3, float thick, Color color); // Draw spline segment: Quadratic Bezier, 2 points, 1 control point
RLAPI void DrawSplineSegmentBezierCubic(Vector2 p1, Vector2 c2, Vector2 c3, Vector2 p4, float thick, Color color); // Draw spline segment: Cubic Bezier, 2 points, 2 control points
'''
makeconnect("DrawSplineLinear", [POINTER(Vector2), c_int, c_float, Color])
def draw_spline_linear(points: list[Vector2], thick: float, color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawSplineLinear(c_points, count, thick, color)

makeconnect("DrawSplineBasis", [POINTER(Vector2), c_int, c_float, Color])
def draw_spline_basis(points: list[Vector2], thick: float, color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawSplineBasis(c_points, count, thick, color)

makeconnect("DrawSplineCatmullRom", [POINTER(Vector2), c_int, c_float, Color])
def draw_spline_catmull_rom(points: list[Vector2], thick: float, color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawSplineCatmullRom(c_points, count, thick, color)

makeconnect("DrawSplineBezierQuadratic", [POINTER(Vector2), c_int, c_float, Color])
def draw_spline_bezier_quadratic(points: list[Vector2], thick: float, color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawSplineBezierQuadratic(c_points, count, thick, color)

makeconnect("DrawSplineBezierCubic", [POINTER(Vector2), c_int, c_float, Color])
def draw_spline_bezier_cubic(points: list[Vector2], thick: float, color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector2 * count
    c_points = arr_type(*points)
    lib.DrawSplineBezierCubic(c_points, count, thick, color)

makeconnect("DrawSplineSegmentLinear", [Vector2, Vector2, c_float, Color])
def draw_spline_segment_linear(p1: Vector2, p2: Vector2, thick: float, color: Color):
    lib.DrawSplineSegmentLinear(p1, p2, thick, color)

makeconnect("DrawSplineSegmentBasis", [Vector2, Vector2, Vector2, Vector2, c_float, Color])
def draw_spline_segment_basis(p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2, thick: float, color: Color):
    lib.DrawSplineSegmentBasis(p1, p2, p3, p4, thick, color)

makeconnect("DrawSplineSegmentCatmullRom", [Vector2, Vector2, Vector2, Vector2, c_float, Color])
def draw_spline_segment_catmull_rom(p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2, thick: float, color: Color):
    lib.DrawSplineSegmentCatmullRom(p1, p2, p3, p4, thick, color)

"""
RLAPI void DrawSplineSegmentBezierQuadratic(Vector2 p1, Vector2 c2, Vector2 p3, float thick, Color color); // Draw spline segment: Quadratic Bezier, 2 points, 1 control point
RLAPI void DrawSplineSegmentBezierCubic(Vector2 p1, Vector2 c2, Vector2 c3, Vector2 p4, float thick, Color color); // Draw spline segment: Cubic Bezier, 2 points, 2 control points
"""

makeconnect("DrawSplineSegmentBezierQuadratic", [Vector2, Vector2, Vector2, c_float, Color])
def draw_spline_segment_bezier_quadratic(p1: Vector2, c2: Vector2, p3: Vector2, thick: float, color: Color):
    lib.DrawSplineSegmentBezierQuadratic(p1, c2, p3, thick, color)

makeconnect("DrawSplineSegmentBezierCubic", [Vector2, Vector2, Vector2, Vector2, c_float, Color])
def draw_spline_segment_bezier_cubic(p1: Vector2, c2: Vector2, c3: Vector2, p4: Vector2, thick: float, color: Color):
    lib.DrawSplineSegmentBezierCubic(p1, c2, c3, p4, thick, color)

'''
RLAPI void DrawModel(Model model, Vector3 position, float scale, Color tint);               // Draw a model (with texture if set)

RLAPI void DrawModelEx(Model model, Vector3 position, Vector3 rotationAxis, float rotationAngle, Vector3 scale, Color tint); // Draw a model with extended parameters

RLAPI void DrawModelWires(Model model, Vector3 position, float scale, Color tint);          // Draw a model wires (with texture if set)
RLAPI void DrawModelWiresEx(Model model, Vector3 position, Vector3 rotationAxis, float rotationAngle, Vector3 scale, Color tint); // Draw a model wires (with texture if set) with extended parameters

RLAPI void DrawModelPoints(Model model, Vector3 position, float scale, Color tint); // Draw a model as points
RLAPI void DrawModelPointsEx(Model model, Vector3 position, Vector3 rotationAxis, float rotationAngle, Vector3 scale, Color tint); // Draw a model as points with extended parameters

RLAPI void DrawBoundingBox(BoundingBox box, Color color);                                   // Draw bounding box (wires)
RLAPI void DrawBillboard(Camera camera, Texture2D texture, Vector3 position, float scale, Color tint);   // Draw a billboard texture
RLAPI void DrawBillboardRec(Camera camera, Texture2D texture, Rectangle source, Vector3 position, Vector2 size, Color tint); // Draw a billboard texture defined by source
RLAPI void DrawBillboardPro(Camera camera, Texture2D texture, Rectangle source, Vector3 position, Vector3 up, Vector2 size, Vector2 origin, float rotation, Color tint); // Draw a billboard texture defined by source and rotation
'''

makeconnect("DrawModel", [Model, Vector3, c_float, Color])
def draw_model(model: Model, position: Vector3, scale: float, tint: Color):
    lib.DrawModel(model, position, scale, tint)

makeconnect("DrawModelEx", [Model, Vector3, Vector3, c_float, Vector3, Color])
def draw_model_ex(model: Model, position: Vector3, rotation_axis: Vector3, rotation_angle: float, scale: Vector3, tint: Color):
    lib.DrawModelEx(model, position, rotation_axis, rotation_angle, scale, tint)

makeconnect("DrawModelWires", [Model, Vector3, c_float, Color])
def draw_model_wires(model: Model, position: Vector3, scale: float, tint: Color):
    lib.DrawModelWires(model, position, scale, tint)

makeconnect("DrawModelWiresEx", [Model, Vector3, Vector3, c_float, Vector3, Color])
def draw_model_wires_ex(model: Model, position: Vector3, rotation_axis: Vector3, rotation_angle: float, scale: Vector3, tint: Color):
    lib.DrawModelWiresEx(model, position, rotation_axis, rotation_angle, scale, tint)

makeconnect("DrawModelPoints", [Model, Vector3, c_float, Color])
def draw_model_points(model: Model, position: Vector3, scale: float, tint: Color):
    lib.DrawModelPoints(model, position, scale, tint)

makeconnect("DrawModelPointsEx", [Model, Vector3, Vector3, c_float, Vector3, Color])
def draw_model_points_ex(model: Model, position: Vector3, rotation_axis: Vector3, rotation_angle: float, scale: Vector3, tint: Color):
    lib.DrawModelPointsEx(model, position, rotation_axis, rotation_angle, scale, tint)

makeconnect("DrawBoundingBox", [BoundingBox, Color])
def draw_bounding_box(box: BoundingBox, color: Color):
    lib.DrawBoundingBox(box, color)

makeconnect("DrawBillboard", [Camera, Texture2D, Vector3, c_float, Color])
def draw_billboard(camera: Camera3D, texture: Texture2D, position: Vector3, scale: float, tint: Color):
    lib.DrawBillboard(camera, texture, position, scale, tint)

"""
RLAPI void DrawBillboardRec(Camera camera, Texture2D texture, Rectangle source, Vector3 position, Vector2 size, Color tint); // Draw a billboard texture defined by source

RLAPI void DrawBillboardPro(Camera camera, Texture2D texture, Rectangle source, Vector3 position, Vector3 up, Vector2 size, Vector2 origin, float rotation, Color tint); // Draw a billboard texture defined by source and rotation
"""

makeconnect("DrawBillboardRec", [Camera, Texture2D, Rectangle, Vector3, Vector2, Color])
def draw_billboard_rec(camera: Camera, texture: Texture2D, source: Rectangle, position: Vector3, size: Vector2, tint: Color):
    lib.DrawBillboardRec(camera, texture, source, position, size, tint)

makeconnect("DrawBillboardPro", [Camera, Texture2D, Rectangle, Vector3, Vector3, Vector2, Vector2, c_float, Color])
def draw_billboard_pro(camera: Camera3D, texture: Texture2D, source: Rectangle, position: Vector3, up: Vector3, size: Vector2, origin: Vector2, rotation: float, tint: Color):
    lib.DrawBillboardPro(camera, texture, source, position, up, size, origin, rotation, tint)

"""
RLAPI void DrawLine3D(Vector3 startPos, Vector3 endPos, Color color);                                    // Draw a line in 3D world space
RLAPI void DrawPoint3D(Vector3 position, Color color);                                                   // Draw a point in 3D space, actually a small line

RLAPI void DrawCircle3D(Vector3 center, float radius, Vector3 rotationAxis, float rotationAngle, Color color); // Draw a circle in 3D world space
RLAPI void DrawTriangle3D(Vector3 v1, Vector3 v2, Vector3 v3, Color color);                              // Draw a color-filled triangle (vertex in counter-clockwise order!)

RLAPI void DrawTriangleStrip3D(const Vector3 *points, int pointCount, Color color);                      // Draw a triangle strip defined by points

RLAPI void DrawCube(Vector3 position, float width, float height, float length, Color color);             // Draw cube
RLAPI void DrawCubeV(Vector3 position, Vector3 size, Color color);                                       // Draw cube (Vector version)
RLAPI void DrawCubeWires(Vector3 position, float width, float height, float length, Color color);        // Draw cube wires
RLAPI void DrawCubeWiresV(Vector3 position, Vector3 size, Color color);                                  // Draw cube wires (Vector version)

RLAPI void DrawSphere(Vector3 centerPos, float radius, Color color);                                     // Draw sphere
RLAPI void DrawSphereEx(Vector3 centerPos, float radius, int rings, int slices, Color color);            // Draw sphere with extended parameters
RLAPI void DrawSphereWires(Vector3 centerPos, float radius, int rings, int slices, Color color);         // Draw sphere wires

RLAPI void DrawCylinder(Vector3 position, float radiusTop, float radiusBottom, float height, int slices, Color color); // Draw a cylinder/cone
RLAPI void DrawCylinderEx(Vector3 startPos, Vector3 endPos, float startRadius, float endRadius, int sides, Color color); // Draw a cylinder with base at startPos and top at endPos
RLAPI void DrawCylinderWires(Vector3 position, float radiusTop, float radiusBottom, float height, int slices, Color color); // Draw a cylinder/cone wires
RLAPI void DrawCylinderWiresEx(Vector3 startPos, Vector3 endPos, float startRadius, float endRadius, int sides, Color color); // Draw a cylinder wires with base at startPos and top at endPos

RLAPI void DrawCapsule(Vector3 startPos, Vector3 endPos, float radius, int slices, int rings, Color color); // Draw a capsule with the center of its sphere caps at startPos and endPos
RLAPI void DrawCapsuleWires(Vector3 startPos, Vector3 endPos, float radius, int slices, int rings, Color color); // Draw capsule wireframe with the center of its sphere caps at startPos and endPos

RLAPI void DrawPlane(Vector3 centerPos, Vector2 size, Color color);                                      // Draw a plane XZ
RLAPI void DrawRay(Ray ray, Color color);                                                                // Draw a ray line
RLAPI void DrawGrid(int slices, float spacing);  
"""

makeconnect("DrawLine3D", [Vector3, Vector3, Color])
def draw_line_3d(start_pos: Vector3, end_pos: Vector3, color: Color):
    lib.DrawLine3D(start_pos, end_pos, color)

makeconnect("DrawPoint3D", [Vector3, Color])
def draw_point_3d(position: Vector3, color: Color):
    lib.DrawPoint3D(position, color)

makeconnect("DrawCircle3D", [Vector3, c_float, Vector3, c_float, Color])
def draw_circle_3d(center: Vector3, radius: float, rotation_axis: Vector3, rotation_angle: float, color: Color):
    lib.DrawCircle3D(center, radius, rotation_axis, rotation_angle, color)

makeconnect("DrawTriangle3D", [Vector3, Vector3, Vector3, Color])
def draw_triangle_3d(v1: Vector3, v2: Vector3, v3: Vector3, color: Color):
    lib.DrawTriangle3D(v1, v2, v3, color)

makeconnect("DrawTriangleStrip3D", [POINTER(Vector3), c_int, Color])
def draw_triangle_strip_3d(points: list[Vector3], color: Color):
    count = len(points)
    # Create a C array of Vector2
    arr_type = Vector3 * count
    c_points = arr_type(*points)
    lib.DrawSplineBasis(c_points, count, color)

makeconnect("DrawCube", [Vector3, c_float, c_float, c_float, Color])
def draw_cube(position: Vector3, width: float, height: float, length: float, color: Color):
    lib.DrawCube(position, width, height, length, color)

makeconnect("DrawCubeV", [Vector3, Vector3, Color])
def draw_cube_v(position: Vector3, size: Vector3, color: Color):
    lib.DrawCubeV(position, size, color)

makeconnect("DrawCubeWires", [Vector3, c_float, c_float, c_float, Color])
def draw_cube_wires(position: Vector3, width: float, height: float, length: float, color: Color):
    lib.DrawCubeWires(position, width, height, length, color)

makeconnect("DrawCubeWiresV", [Vector3, Vector3, Color])
def draw_cube_wires_v(position: Vector3, size: Vector3, color: Color):
    lib.DrawCubeWiresV(position, size, color)



"""
RLAPI void DrawSphere(Vector3 centerPos, float radius, Color color);                                     // Draw sphere
RLAPI void DrawSphereEx(Vector3 centerPos, float radius, int rings, int slices, Color color);            // Draw sphere with extended parameters
RLAPI void DrawSphereWires(Vector3 centerPos, float radius, int rings, int slices, Color color);         // Draw sphere wires

RLAPI void DrawCylinder(Vector3 position, float radiusTop, float radiusBottom, float height, int slices, Color color); // Draw a cylinder/cone
RLAPI void DrawCylinderEx(Vector3 startPos, Vector3 endPos, float startRadius, float endRadius, int sides, Color color); // Draw a cylinder with base at startPos and top at endPos
RLAPI void DrawCylinderWires(Vector3 position, float radiusTop, float radiusBottom, float height, int slices, Color color); // Draw a cylinder/cone wires
RLAPI void DrawCylinderWiresEx(Vector3 startPos, Vector3 endPos, float startRadius, float endRadius, int sides, Color color); // Draw a cylinder wires with base at startPos and top at endPos

RLAPI void DrawCapsule(Vector3 startPos, Vector3 endPos, float radius, int slices, int rings, Color color); // Draw a capsule with the center of its sphere caps at startPos and endPos
RLAPI void DrawCapsuleWires(Vector3 startPos, Vector3 endPos, float radius, int slices, int rings, Color color); // Draw capsule wireframe with the center of its sphere caps at startPos and endPos

RLAPI void DrawPlane(Vector3 centerPos, Vector2 size, Color color);                                      // Draw a plane XZ
RLAPI void DrawRay(Ray ray, Color color);                                                                // Draw a ray line
RLAPI void DrawGrid(int slices, float spacing);  
"""

makeconnect("DrawSphere", [Vector3, c_float, Color])
def draw_sphere(center_pos: Vector3, radius: float, color: Color):
    lib.DrawSphere(center_pos, radius, color)

makeconnect("DrawSphereEx", [Vector3, c_float, c_int, c_int, Color])
def draw_sphere_ex(center_pos: Vector3, radius: float, rings: int, slices: int, color: Color):
    lib.DrawSphereEx(center_pos, radius, rings, slices, color)

makeconnect("DrawSphereWires", [Vector3, c_float, c_int, c_int, Color])
def draw_sphere_wires(center_pos: Vector3, radius: float, rings: int, slices: int, color: Color):
    lib.DrawSphereWires(center_pos, radius, rings, slices, color)




makeconnect("DrawCylinder", [Vector3, c_float, c_float, c_float, c_int, Color])
def draw_cylinder(position: Vector3, radius_top: float, radius_bottom: float, height: float, slices: int, color: Color):
    lib.DrawCylinder(position, radius_top, radius_bottom, height, slices, color)

makeconnect("DrawCylinderEx", [Vector3, Vector3, c_float, c_float, c_int, Color])
def draw_cylinder_ex(start_pos: Vector3, end_pos: Vector3, start_radius: float, end_radius: float, sides: int, color: Color):
    lib.DrawCylinderEx(start_pos, end_pos, start_radius, end_radius, sides, color)

makeconnect("DrawCylinderWires", [Vector3, c_float, c_float, c_float, c_int, Color])
def draw_cylinder_wires(position: Vector3, radius_top: float, radius_bottom: float, height: float, slices: int, color: Color):
    lib.DrawCylinderWires(position, radius_top, radius_bottom, height, slices, color)

makeconnect("DrawCylinderWiresEx", [Vector3, Vector3, c_float, c_float, c_int, Color])
def draw_cylinder_wires_ex(start_pos: Vector3, end_pos: Vector3, start_radius: float, end_radius: float, sides: int, color: Color):
    lib.DrawCylinderWiresEx(start_pos, end_pos, start_radius, end_radius, sides, color)




makeconnect("DrawCapsule", [Vector3, Vector3, c_float, c_int, c_int, Color])
def draw_capsule(start_pos: Vector3, end_pos: Vector3, radius: float, slices: int, rings: int, color: Color):
    lib.DrawCapsule(start_pos, end_pos, radius, slices, rings, color)

makeconnect("DrawCapsuleWires", [Vector3, Vector3, c_float, c_int, c_int, Color])
def draw_capsule_wires(start_pos: Vector3, end_pos: Vector3, radius: float, slices: int, rings: int, color: Color):
    lib.DrawCapsuleWires(start_pos, end_pos, radius, slices, rings, color)





makeconnect("DrawPlane", [Vector3, Vector2, Color])
def draw_plane(center_pos: Vector3, size: Vector2, color: Color):
    lib.DrawPlane(center_pos, size, color)

makeconnect("DrawRay", [Ray, Color])
def draw_ray(ray: Ray, color: Color):
    lib.DrawRay(ray, color)

makeconnect("DrawGrid", [c_int, c_float])
def draw_grid(slices: int, spacing: float):
    lib.DrawGrid(slices, spacing)

"""
RLAPI void DrawFPS(int posX, int posY);                                                     // Draw current FPS
RLAPI void DrawText(const char *text, int posX, int posY, int fontSize, Color color);       // Draw text (using default font)
RLAPI void DrawTextEx(Font font, const char *text, Vector2 position, float fontSize, float spacing, Color tint); // Draw text using font and additional parameters
RLAPI void DrawTextPro(Font font, const char *text, Vector2 position, (Vector2 origin, float rotation,) float fontSize, float spacing, Color tint); // Draw text using Font and pro parameters (rotation)
RLAPI void DrawTextCodepoint(Font font, int codepoint, Vector2 position, float fontSize, Color tint); // Draw one character (codepoint)
RLAPI void DrawTextCodepoints(Font font, const int *codepoints, int codepointCount, Vector2 position, float fontSize, float spacing, Color tint); // Draw multiple character (codepoint)
"""

makeconnect("DrawFPS", [c_int, c_int])
def draw_fps(pos_x: int, pos_y: int):
    lib.DrawFPS(pos_x, pos_y)

makeconnect("DrawText", [c_char_p, c_int, c_int, c_int, Color])
def draw_text(text: str, pos_x: int, pos_y: int, font_size: int, color: Color):
    lib.DrawText(text.encode(), pos_x, pos_y, font_size, color)

makeconnect("DrawTextEx", [Font, c_char_p, Vector2, c_float, c_float, Color])
def draw_text_ex(font: Font, text: str, position: Vector2, font_size: float, spacing: float, tint: Color):
    lib.DrawTextEx(font, text.encode(), position, font_size, spacing, tint)

makeconnect("DrawTextPro", [Font, c_char_p, Vector2, Vector2, c_float, c_float, c_float, Color])
def draw_text_pro(font: Font, text: str, position: Vector2, origin: Vector2, rotation: float, font_size: float, spacing: float, tint: Color):
    lib.DrawTextPro(font, text.encode(), position, origin, rotation, font_size, spacing, tint)

makeconnect("DrawTextCodepoint", [Font, c_int, Vector2, c_float, Color])
def draw_text_codepoint(font: Font, codepoint: int, position: Vector2, font_size: float, tint: Color):
    lib.DrawTextCodepoint(font, codepoint, position, font_size, tint)

makeconnect("DrawTextCodepoints", [Font, POINTER(c_int), c_int, Vector2, c_float, c_float, Color])
def draw_text_codepoints(font: Font, codepoints: list[int], position: Vector2, font_size: float, spacing: float, tint: Color):
    count = len(codepoints)
    # Create a C array of Vector2
    arr_type = c_int * count
    c_points = arr_type(*codepoints)
    lib.DrawTextCodepoints(font, c_points, count, position, font_size, spacing, tint)

"""
RLAPI void DrawTexture(Texture2D texture, int posX, int posY, Color tint);                               // Draw a Texture2D
RLAPI void DrawTextureV(Texture2D texture, Vector2 position, Color tint);                                // Draw a Texture2D with position defined as Vector2
RLAPI void DrawTextureEx(Texture2D texture, Vector2 position, float rotation, float scale, Color tint);  // Draw a Texture2D with extended parameters
RLAPI void DrawTextureRec(Texture2D texture, Rectangle source, Vector2 position, Color tint);            // Draw a part of a texture defined by a rectangle

RLAPI void DrawTexturePro(Texture2D texture, Rectangle source, Rectangle dest, Vector2 origin, float rotation, Color tint); // Draw a part of a texture defined by a rectangle with 'pro' parameters

RLAPI void DrawTextureNPatch(Texture2D texture, NPatchInfo nPatchInfo, Rectangle dest, Vector2 origin, float rotation, Color tint); // Draws a texture (or part of it) that stretches or shrinks nicely
"""

makeconnect("DrawTexture", [Texture2D, c_int, c_int, Color])
def draw_texture(texture: Texture2D, pos_x: int, pos_y: int, tint: Color):
    lib.DrawTexture(texture, pos_x, pos_y, tint)

makeconnect("DrawTextureV", [Texture2D, Vector2, Color])
def draw_texture_v(texture: Texture2D, position: Vector2, tint: Color):
    lib.DrawTextureV(texture, position, tint)

makeconnect("DrawTextureEx", [Texture2D, Vector2, c_float, c_float, Color])
def draw_texture_ex(texture: Texture2D, position: Vector2, rotation: float, scale: float, tint: Color):
    lib.DrawTextureEx(texture, position, rotation, scale, tint)

makeconnect("DrawTextureRec", [Texture2D, Rectangle, Vector2, Color])
def draw_texture_rec(texture: Texture2D, source: Rectangle, position: Vector2, tint: Color):
    lib.DrawTextureRec(texture, source, position, tint)

makeconnect("DrawTexturePro", [Texture2D, Rectangle, Rectangle, Vector2, c_float, Color])
def draw_texture_pro(texture: Texture2D, source: Rectangle, dest: Rectangle, origin: Vector2, rotation: float, tint: Color):
    lib.DrawTexturePro(texture, source, dest, origin, rotation, tint)


makeconnect("DrawTextureNPatch", [Texture2D, NPatchInfo, Rectangle, Vector2, c_float, Color])
def draw_texture_n_patch(texture: Texture2D, n_patch_info: NPatchInfo, dest: Rectangle, origin: Vector2, rotation: float, tint: Color):
    lib.DrawTextureNPatch(texture, n_patch_info, dest, origin, rotation, tint)

