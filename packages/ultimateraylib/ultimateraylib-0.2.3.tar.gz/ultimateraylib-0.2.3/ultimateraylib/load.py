from ._classes import *








'''
RLAPI Texture2D LoadTexture(const char *fileName);                                                       // Load texture from file into GPU memory (VRAM)
RLAPI Texture2D LoadTextureFromImage(Image image);                                                       // Load texture from image data
RLAPI TextureCubemap LoadTextureCubemap(Image image, int layout);                                        // Load cubemap from image, multiple image cubemap layouts supported
RLAPI RenderTexture2D LoadRenderTexture(int width, int height);                                          // Load texture for rendering (framebuffer)

RLAPI bool IsTextureValid(Texture2D texture);                                                            // Check if a texture is valid (loaded in GPU)
RLAPI void UnloadTexture(Texture2D texture);                                                             // Unload texture from GPU memory (VRAM)
RLAPI bool IsRenderTextureValid(RenderTexture2D target);                                                 // Check if a render texture is valid (loaded in GPU)
RLAPI void UnloadRenderTexture(RenderTexture2D target);                                                  // Unload render texture from GPU memory (VRAM)
RLAPI void UpdateTexture(Texture2D texture, const void *pixels);                                         // Update GPU texture with new data (pixels should be able to fill texture)
RLAPI void UpdateTextureRec(Texture2D texture, Rectangle rec, const void *pixels);                       // Update GPU texture rectangle with new data (pixels and rec should fit in texture)
'''

makeconnect("LoadTexture", [c_char_p], Texture2D)
def load_texture(file_name: str):
    return lib.LoadTexture(file_name.encode())

makeconnect("LoadTextureFromImage", [Image], Texture2D)
def load_texture_from_image(image: Image):
    return lib.LoadTextureFromImage(image)

makeconnect("LoadTextureCubemap", [Image, c_int], TextureCubemap)
def load_texture_cubemap(image: Image, layout: int):
    return lib.LoadTextureCubemap(image, layout)

makeconnect("LoadRenderTexture", [c_int, c_int], RenderTexture2D)
def load_render_texture(width: int, height: int):
    return lib.LoadRenderTexture(width, height)

makeconnect("IsTextureValid", [Texture2D], c_bool)
def is_texture_valid(texture: Texture2D) -> bool:
    return lib.IsTextureValid(texture)

makeconnect("IsRenderTextureValid", [RenderTexture], c_bool)
def is_render_texture_valid(target: RenderTexture) -> bool:
    return lib.IsRenderTextureValid(target)

makeconnect("UpdateTexture", [Texture2D, c_void_p])
def update_texture(texture: Texture2D, pixels: list):
    arr = c_void_p * len(pixels)
    opo = arr(*pixels)
    lib.UpdateTexture(texture, opo)


"""
RLAPI Model LoadModel(const char *fileName);                                                // Load model from files (meshes and materials)
RLAPI Model LoadModelFromMesh(Mesh mesh);                                                   // Load model from generated mesh (default material)
RLAPI bool IsModelValid(Model model);                                                       // Check if a model is valid (loaded in GPU, VAO/VBOs)
RLAPI void UnloadModel(Model model);                                                        // Unload model (including meshes) from memory (RAM and/or VRAM)
RLAPI BoundingBox GetModelBoundingBox(Model model);                                         // Compute model bounding box limits (considers all meshes)
"""

makeconnect("LoadModel", [c_char_p], Model)
def load_model(file_name: str):
    return lib.LoadModel(file_name.encode())

makeconnect("LoadModelFromMesh", [Mesh], Model)
def load_model_from_mesh(mesh: Mesh):
    return lib.LoadModelFromMesh(mesh)

makeconnect("IsModelValid", [Model], c_bool)
def is_model_valid(model: Model):
    return lib.IsModelValid(model)

makeconnect("UnloadModel", [Model])
def unload_model(model: Model):
    lib.UnloadModel(model)

makeconnect("GetModelBoundingBox", [Model], BoundingBox)
def get_model_bounding_box(model: Model):
    return lib.GetModelBoundingBox(model)

"""
// NOTE: These functions do not require GPU access
RLAPI Image LoadImage(const char *fileName);                                                             // Load image from file into CPU memory (RAM)
RLAPI Image LoadImageRaw(const char *fileName, int width, int height, int format, int headerSize);       // Load image from RAW file data
RLAPI Image LoadImageAnim(const char *fileName, int *frames);                                            // Load image sequence from file (frames appended to image.data)

RLAPI Image LoadImageAnimFromMemory(const char *fileType, const unsigned char *fileData, int dataSize, int *frames); // Load image sequence from memory buffer

RLAPI Image LoadImageFromMemory(const char *fileType, const unsigned char *fileData, int dataSize);      // Load image from memory buffer, fileType refers to extension: i.e. '.png'
RLAPI Image LoadImageFromTexture(Texture2D texture);                                                     // Load image from GPU texture data
RLAPI Image LoadImageFromScreen(void);                                                                   // Load image from screen buffer and (screenshot)
RLAPI bool IsImageValid(Image image);                                                                    // Check if an image is valid (data and parameters)
RLAPI void UnloadImage(Image image);                                                                     // Unload image from CPU memory (RAM)
RLAPI bool ExportImage(Image image, const char *fileName);                                               // Export image data to file, returns true on success
RLAPI unsigned char *ExportImageToMemory(Image image, const char *fileType, int *fileSize);              // Export image to memory buffer
RLAPI bool ExportImageAsCode(Image image, const char *fileName);                                         // Export image as code file defining an array of bytes, returns true on success
"""

makeconnect("LoadImage", [c_char_p], Image)
def load_image(file_name: str):
    return lib.LoadImage(file_name.encode())

# ---- LoadImageRaw ----
makeconnect("LoadImageRaw", [c_char_p, c_int, c_int, c_int, c_int], Image)
def load_image_raw(file_name: str, width: int, height: int, format: int, header_size: int):
    return lib.LoadImageRaw(file_name.encode(), width, height, format, header_size)

# ---- LoadImageAnim ----
makeconnect("LoadImageAnim", [c_char_p, POINTER(c_int)], Image)
def load_image_anim(file_name: str):
    frames = c_int(0)
    img = lib.LoadImageAnim(file_name.encode(), byref(frames))
    return img, frames.value

# ---- LoadImageAnimFromMemory ----
makeconnect("LoadImageAnimFromMemory", [c_char_p, POINTER(c_ubyte), c_int, POINTER(c_int)], Image)
def load_image_anim_from_memory(file_type: str, file_data: bytes):
    data = (c_ubyte * len(file_data))(*file_data)
    frames = c_int(0)
    img = lib.LoadImageAnimFromMemory(file_type.encode(), data, len(file_data), byref(frames))
    return img, frames.value

makeconnect("LoadImageFromMemory", [c_char_p, POINTER(c_ubyte), c_int], Image)
def load_image_from_memory(file_type: str, file_data: bytes):
    data = (c_ubyte * len(file_data))(*file_data)
    return lib.LoadImageFromMemory(file_type.encode(), data, len(file_data))

makeconnect("LoadImageFromTexture", [Texture2D], Image)
def load_image_from_texture(texture: Texture2D):
    return lib.LoadImageFromTexture(texture)

makeconnect("LoadImageFromScreen", [], Image)
def load_image_from_screen():
    return lib.LoadImageFromScreen()

makeconnect("IsImageValid", [Image], c_bool)
def is_image_valid(image: Image) -> bool:
    return lib.IsImageValid(image)

makeconnect("ExportImage", [Image, c_char_p], c_bool)
def export_image(image: Image, file_name: str) -> bool:
    "Export image data to file, returns true on success"
    return lib.ExportImage(image, file_name.encode())

makeconnect("ExportImageToMemory", [Image, c_char_p, POINTER(c_int)], POINTER(c_ubyte))
def export_image_to_memory(image: Image, file_type: str) -> bytes:
    'Export image to memory buffer (please put file_type as like .png)'
    o = c_int()
    ptr = lib.ExportImageToMemory(image, file_type.encode(), byref(o))
    return ctypes.string_at(ptr, o.value)

"""
// NOTE: Shader functionality is not available on OpenGL 1.1
RLAPI Shader LoadShader(const char *vsFileName, const char *fsFileName);   // Load shader from files and bind default locations
RLAPI Shader LoadShaderFromMemory(const char *vsCode, const char *fsCode); // Load shader from code strings and bind default locations
RLAPI bool IsShaderValid(Shader shader);                                   // Check if a shader is valid (loaded on GPU)
RLAPI int GetShaderLocation(Shader shader, const char *uniformName);       // Get shader uniform location
RLAPI int GetShaderLocationAttrib(Shader shader, const char *attribName);  // Get shader attribute location

RLAPI void SetShaderValue(Shader shader, int locIndex, const void *value, int uniformType);               // Set shader uniform value
RLAPI void SetShaderValueV(Shader shader, int locIndex, const void *value, int uniformType, int count);   // Set shader uniform value vector
RLAPI void SetShaderValueMatrix(Shader shader, int locIndex, Matrix mat);         // Set shader uniform value (matrix 4x4)
RLAPI void SetShaderValueTexture(Shader shader, int locIndex, Texture2D texture); // Set shader uniform value and bind the texture (sampler2d)
RLAPI void UnloadShader(Shader shader);      
"""
makeconnect("LoadShader", [c_char_p, c_char_p], Shader)
def load_shader(vs_file_name: str, fs_file_name: str) -> Shader:
    return lib.LoadShader(vs_file_name.encode(), fs_file_name.encode())

makeconnect("LoadShaderFromMemory", [c_char_p, c_char_p], Shader)
def load_shader_from_memory(vs_code: str, fs_code: str) -> Shader:
    return lib.LoadShaderFromMemory(vs_code.encode(), fs_code.encode())

makeconnect("IsShaderValid", [Shader], c_bool)
def is_shader_valid(shader: Shader) -> bool:
    return lib.IsShaderValid(shader)

makeconnect("GetShaderLocation", [Shader, c_char_p], c_int)
def get_shader_location(shader: Shader, uniform_name: str) -> int:
    return lib.GetShaderLocation(shader, uniform_name.encode())

makeconnect("GetShaderLocationAttrib", [Shader, c_char_p], c_int)
def get_shader_location_attrib(shader: Shader, attrib_name: str) -> int:
    return lib.GetShaderLocationAttrib(shader, attrib_name.encode())

makeconnect("SetShaderValue", [Shader, c_int, c_void_p, c_int])
def set_shader_value(shader: Shader, loc_index: int, value, uniform_type: int):
    # Python sequences → ctypes arrays (vec2/vec3/vec4/matrix rows, etc.)
    if isinstance(value, (list, tuple)):
        value = (c_float * len(value))(*value)

    # Scalars
    elif isinstance(value, float):
        value = c_float(value)
    elif isinstance(value, int):
        value = c_int(value)

    lib.SetShaderValue(
        shader,
        loc_index,
        byref(value),
        uniform_type
    )

makeconnect("SetShaderValueV", [Shader, c_int, c_void_p, c_int, c_int])
def set_shader_value_v(shader: Shader, loc_index: int, value: c_void_p, uniform_type: int, count: int):
    lib.SetShaderValueV(shader, loc_index, value, uniform_type, count)



"""
RLAPI void UploadMesh(Mesh *mesh, bool dynamic);                                            // Upload mesh vertex data in GPU and provide VAO/VBO ids
RLAPI void UpdateMeshBuffer(Mesh mesh, int index, const void *data, int dataSize, int offset); // Update mesh vertex data in GPU for a specific buffer index
RLAPI void UnloadMesh(Mesh mesh);                                                           // Unload mesh data from CPU and GPU
RLAPI void DrawMesh(Mesh mesh, Material material, Matrix transform);                        // Draw a 3d mesh with material and transform
RLAPI void DrawMeshInstanced(Mesh mesh, Material material, const Matrix *transforms, int instances); // Draw multiple mesh instances with material and different transforms

RLAPI BoundingBox GetMeshBoundingBox(Mesh mesh);                                            // Compute mesh bounding box limits
RLAPI void GenMeshTangents(Mesh *mesh);                                                     // Compute mesh tangents
RLAPI bool ExportMesh(Mesh mesh, const char *fileName);                                     // Export mesh data to file, returns true on success
RLAPI bool ExportMeshAsCode(Mesh mesh, const char *fileName);                               // Export mesh as code file (.h) defining multiple arrays of vertex attributes
"""

makeconnect("UploadMesh", [POINTER(Mesh), c_bool])
def upload_mesh(mesh:Mesh, dynamic:bool):
    'Upload mesh vertex data in GPU and provide VAO/VBO ids'
    lib.UploadMesh(byref(mesh), dynamic)

makeconnect("UpdateMeshBuffer", [Mesh, c_int, c_void_p, c_int, c_int])
def update_mesh_buffer(mesh: Mesh, index, data, offset):
    'Update mesh vertex data in GPU for a specific buffer index'
    size = len(data)
    lib.UpdateMeshBuffer(mesh, index, data, size, offset)

makeconnect("UnloadMesh", [Mesh])
def unload_mesh(mesh: Mesh):
    lib.UnloadMesh(mesh)

makeconnect("DrawMesh", [Mesh, Material, Matrix])
def draw_mesh(mesh: Mesh, material: Material, transform: Matrix):
    lib.DrawMesh(mesh, material, transform)

makeconnect("DrawMeshInstanced", [Mesh, Material, POINTER(Matrix), c_int])
def draw_mesh_instanced(mesh: Mesh, material: Material, transforms: list[Matrix]):
    count = len(transforms)
    if count == 0:
        return  # nothing to draw

    # Create C array of Matrix
    arr_type = Matrix * count
    c_transforms = arr_type(*transforms)

    lib.DrawMeshInstanced(mesh, material, c_transforms, count)

makeconnect("GetMeshBoundingBox", [Mesh], BoundingBox)
def get_mesh_bounding_box(mesh: Mesh) -> BoundingBox:
    return lib.GetMeshBoundingBox(mesh)

makeconnect("GenMeshTangents", [POINTER(Mesh)])
def gen_mesh_tangents(mesh: Mesh):
    lib.GenMeshTangents(byref(mesh))

'''
RLAPI bool ExportMesh(Mesh mesh, const char *fileName);                                     // Export mesh data to file, returns true on success
RLAPI bool ExportMeshAsCode(Mesh mesh, const char *fileName);                               // Export mesh as code file (.h) defining multiple arrays of vertex attributes
'''
makeconnect("ExportMesh", [Mesh, c_char_p], c_bool)
def export_mesh(mesh: Mesh, file_name: str) -> bool:
    'Export mesh data to file, returns true on success'
    return lib.ExportMesh(mesh, file_name.encode())

makeconnect("ExportMeshAsCode", [Mesh, c_char_p], c_bool)
def export_mesh_as_c(mesh: Mesh, file_name: str) -> bool:
    'Export mesh as c header file (.h) defining multiple arrays of vertex attributes'
    return lib.ExportMeshAsCode(mesh, file_name.encode())



"""
RLAPI Wave LoadWave(const char *fileName);                            // Load wave data from file
RLAPI Wave LoadWaveFromMemory(const char *fileType, const unsigned char *fileData, int dataSize); // Load wave from memory buffer, fileType refers to extension: i.e. '.wav'
RLAPI bool IsWaveValid(Wave wave);                                    // Checks if wave data is valid (data loaded and parameters)
RLAPI Sound LoadSound(const char *fileName);                          // Load sound from file
RLAPI Sound LoadSoundFromWave(Wave wave);                             // Load sound from wave data
RLAPI Sound LoadSoundAlias(Sound source);                             // Create a new sound that shares the same sample data as the source sound, does not own the sound data
RLAPI bool IsSoundValid(Sound sound);                                 // Checks if a sound is valid (data loaded and buffers initialized)
RLAPI void UpdateSound(Sound sound, const void *data, int sampleCount); // Update sound buffer with new data (data and frame count should fit in sound)
RLAPI void UnloadWave(Wave wave);                                     // Unload wave data
RLAPI void UnloadSound(Sound sound);                                  // Unload sound
RLAPI void UnloadSoundAlias(Sound alias);                             // Unload a sound alias (does not deallocate sample data)
RLAPI bool ExportWave(Wave wave, const char *fileName);               // Export wave data to file, returns true on success
RLAPI bool ExportWaveAsCode(Wave wave, const char *fileName);         // Export wave sample data to code (.h), returns true on success
"""

makeconnect("LoadWave", [c_char_p], Wave)
def load_wave(file_name: str) -> Wave: 
    return lib.LoadWave(file_name.encode())

makeconnect("LoadWaveFromMemory", [c_char_p, ubyte_p, c_int], Wave)

makeconnect("IsWaveValid", [Wave], c_bool)
def is_wave_valid(wave: Wave)  -> bool:
    return lib.IsWaveValid(wave)

makeconnect("LoadSound", [c_char_p], Sound)
def load_sound(file_name: str): 
    return lib.LoadSound(file_name.encode())

makeconnect("LoadSoundFromWave", [Wave], Sound)
def load_sound_from_wave(wave: Wave):
    return lib.LoadSoundFromWave(wave)

makeconnect("LoadSoundAlias", [Sound], Sound)
def load_sound_alias(source: Sound):
    return lib.LoadSoundAlias(source)

makeconnect("IsSoundValid", [Sound], c_bool)
def is_sound_valid(sound: Sound)  -> bool:
    return lib.IsSoundValid(sound)

makeconnect("UpdateSound", [Sound, c_void_p, c_int])
def update_sound(sound: Sound, data, sample_count: int):
    lib.UpdateSound(sound, data, sample_count)

makeconnect("UnloadWave", [Wave])
def unload_wave(wave: Wave):
    lib.UnloadSound(wave)

makeconnect("UnloadSound", [Sound])
def unload_sound(sound: Sound):
    lib.UnloadSound(sound)

makeconnect("UnloadSoundAlias", [Sound])
def unload_sound_alias(alias: Sound):
    lib.UnloadSoundAlias(alias)

makeconnect("ExportWave", [Wave, c_char_p], c_bool)
def export_wave(wave: Wave, file_name: str)  -> bool:
    return lib.ExportWave(wave, file_name.encode())

makeconnect("ExportWaveAsCode", [Wave, c_char_p], c_bool)
def export_wave_as_code(wave: Wave, file_name: str) -> bool:
    return lib.ExportWaveAsCode(wave, file_name.encode())

"""
RLAPI Music LoadMusicStream(const char *fileName);                    // Load music stream from file
RLAPI Music LoadMusicStreamFromMemory(const char *fileType, const unsigned char *data, int dataSize); // Load music stream from data
"""

makeconnect("LoadMusicStream", [c_char_p], Music)
def load_music_stream(file_name: str) -> Music:
    return lib.LoadMusicStream(file_name.encode())

makeconnect("LoadMusicStreamFromMemory", [c_char_p, ubyte_p, c_int])
def load_music_stream_from_memory(file_type: str, data: bytes) -> Music:
    # Convert Python bytes → ctypes unsigned char buffer
    size = len(data)
    buf = (c_ubyte * size).from_buffer_copy(data)

    music = lib.LoadMusicStreamFromMemory(
        file_type.encode(),
        buf,
        size
    )

    # Keep buffer alive!
    music._buffer = buf
    music._size = size

    return music

"""
RLAPI ModelAnimation *LoadModelAnimations(const char *fileName, int *animCount);            // Load model animations from file
RLAPI void UpdateModelAnimation(Model model, ModelAnimation anim, int frame);               // Update model animation pose (CPU)
RLAPI void UpdateModelAnimationBones(Model model, ModelAnimation anim, int frame);          // Update model animation mesh bone matrices (GPU skinning)
RLAPI void UnloadModelAnimation(ModelAnimation anim);                                       // Unload animation data
RLAPI void UnloadModelAnimations(ModelAnimation *animations, int animCount);                // Unload animation array data
RLAPI bool IsModelAnimationValid(Model model, ModelAnimation anim);                         // Check model animation skeleton match
"""
lib.LoadModelAnimations.restype = POINTER(ModelAnimation)
lib.LoadModelAnimations.argtypes = [c_char_p, POINTER(c_int)]

lib.UpdateModelAnimation.restype = None
lib.UpdateModelAnimation.argtypes = [POINTER(Model), POINTER(ModelAnimation), c_int]

lib.UpdateModelAnimationBones.restype = None
lib.UpdateModelAnimationBones.argtypes = [POINTER(Model), POINTER(ModelAnimation), c_int]

lib.UnloadModelAnimation.restype = None
lib.UnloadModelAnimation.argtypes = [POINTER(ModelAnimation)]

lib.UnloadModelAnimations.restype = None
lib.UnloadModelAnimations.argtypes = [POINTER(ModelAnimation), c_int]

lib.IsModelAnimationValid.restype = c_bool
lib.IsModelAnimationValid.argtypes = [POINTER(Model), POINTER(ModelAnimation)]

# --- Python-friendly wrapper functions ---
def load_model_animations(file: str):
    count = c_int()
    anims_ptr = lib.LoadModelAnimations(file.encode('utf-8'), byref(count))
    if not anims_ptr:
        return []  # Return empty list if failed

    # Convert pointer array to Python list
    anim_list = [anims_ptr[i] for i in range(count.value)]
    return anim_list


def update_model_animation(model:Model, anim: ModelAnimation, frame: int):
    lib.UpdateModelAnimation(byref(model), byref(anim), frame)

def update_model_animation_bones(model, anim, frame):
    lib.UpdateModelAnimationBones(byref(model), byref(anim), frame)

def unload_model_animation(anim):
    lib.UnloadModelAnimation(byref(anim))

def unload_model_animations(anims, count):
    lib.UnloadModelAnimations(anims, count)

def is_model_animation_valid(model, anim):
    return lib.IsModelAnimationValid(byref(model), anim)

'''
RLAPI Font LoadFontEx(const char *fileName, int fontSize, int *codepoints, int codepointCount); // Load font from file with extended parameters, use NULL for codepoints and 0 for codepointCount to load the default character set, font size is provided in pixels height
RLAPI Font LoadFontFromImage(Image image, Color key, int firstChar);                        // Load font from Image (XNA style)
RLAPI Font LoadFontFromMemory(const char *fileType, const unsigned char *fileData, int dataSize, int fontSize, int *codepoints, int codepointCount); // Load font from memory buffer, fileType refers to extension: i.e. '.ttf'
RLAPI bool IsFontValid(Font font);                                                          // Check if a font is valid (font data loaded, WARNING: GPU texture not checked)
RLAPI GlyphInfo *LoadFontData(const unsigned char *fileData, int dataSize, int fontSize, int *codepoints, int codepointCount, int type); // Load font data for further use
RLAPI Image GenImageFontAtlas(const GlyphInfo *glyphs, Rectangle **glyphRecs, int glyphCount, int fontSize, int padding, int packMethod); // Generate image font atlas using chars info
RLAPI void UnloadFontData(GlyphInfo *glyphs, int glyphCount);                               // Unload font chars info data (RAM)
RLAPI void UnloadFont(Font font);                                                           // Unload font from GPU memory (VRAM)
RLAPI bool ExportFontAsCode(Font font, const char *fileName);                               // Export font as code file, returns true on success
'''

makeconnect("GetFontDefault", [], Font)
def get_font_default() -> Font:
    'Get the default Font'
    return lib.GetFontDefault()

makeconnect("LoadFont", [c_char_p], Font)
def load_font(file_name: str) -> Font:
    'Load font from file into GPU memory (VRAM)'
    return lib.LoadFont(file_name.encode())

makeconnect("LoadFontEx", [c_char_p, c_int, c_int_p, c_int], Font)
def load_font_ex(file_name: str, font_size: int, codepoints: list[int]) -> Font:
    'Load font from file with extended parameters, use NULL for codepoints and 0 for codepointCount to load the default character set, font size is provided in pixels height'
    arrtype = c_int * len(codepoints)
    opo = arrtype(*codepoints)
    return lib.LoadFontEx(file_name.encode(), font_size, opo, len(codepoints))

'''
RLAPI Mesh GenMeshPoly(int sides, float radius);                                            // Generate polygonal mesh
RLAPI Mesh GenMeshPlane(float width, float length, int resX, int resZ);                     // Generate plane mesh (with subdivisions)
RLAPI Mesh GenMeshCube(float width, float height, float length);                            // Generate cuboid mesh

RLAPI Mesh GenMeshSphere(float radius, int rings, int slices);                              // Generate sphere mesh (standard sphere)
RLAPI Mesh GenMeshHemiSphere(float radius, int rings, int slices);                          // Generate half-sphere mesh (no bottom cap)
RLAPI Mesh GenMeshCylinder(float radius, float height, int slices);                         // Generate cylinder mesh
RLAPI Mesh GenMeshCone(float radius, float height, int slices);                             // Generate cone/pyramid mesh
RLAPI Mesh GenMeshTorus(float radius, float size, int radSeg, int sides);                   // Generate torus mesh
RLAPI Mesh GenMeshKnot(float radius, float size, int radSeg, int sides);                    // Generate trefoil knot mesh
RLAPI Mesh GenMeshHeightmap(Image heightmap, Vector3 size);                                 // Generate heightmap mesh from image data
RLAPI Mesh GenMeshCubicmap(Image cubicmap, Vector3 cubeSize);                               // Generate cubes-based map mesh from image data
'''

makeconnect("GenMeshPoly", [c_int, c_float], Mesh)
def gen_mesh_poly(sides: int, radius: float) -> Mesh:
    return lib.GenMeshPoly(sides, radius)

makeconnect("GenMeshPlane", [c_float, c_float, c_int, c_int], Mesh)
def gen_mesh_plane(width: float, length: float, res_x: int, res_z: int) -> Mesh:
    return lib.GenMeshPlane(width, length, res_x, res_z)

makeconnect("GenMeshCube", [c_float, c_float, c_float], Mesh)
def gen_mesh_cube(width: float, height: float, length: float) -> Mesh:
    return lib.GenMeshCube(width, height, length)

makeconnect("GenMeshSphere", [c_float, c_int, c_int], Mesh)


makeconnect("GenMeshHemiSphere", [c_float, c_int, c_int], Mesh)


makeconnect("GenMeshCylinder", [c_float, c_float, c_int], Mesh)


makeconnect("GenMeshCone", [c_float, c_float, c_int], Mesh)


