from ._classes import *


'''
// Text font info functions
RLAPI Vector2 MeasureTextEx(Font font, const char *text, float fontSize, float spacing);    // Measure string size for Font
RLAPI int GetGlyphIndex(Font font, int codepoint);                                          // Get glyph index position in font for a codepoint (unicode character), fallback to '?' if not found
RLAPI GlyphInfo GetGlyphInfo(Font font, int codepoint);                                     // Get glyph font info data for a codepoint (unicode character), fallback to '?' if not found
RLAPI Rectangle GetGlyphAtlasRec(Font font, int codepoint);                                 // Get glyph rectangle in font atlas for a codepoint (unicode character), fallback to '?' if not found
'''
makeconnect("SetTextLineSpacing", [c_int])
def set_text_line_spacing(spacing: int):
    'Set vertical line spacing when drawing with line-breaks'
    lib.SetTextLineSpacing(spacing)

makeconnect("MeasureText", [c_char_p, c_int], c_int)
def measure_text(text: str, font_size: int) -> int:
    'Measure string width for default font'
    return lib.MeasureText(text.encode(), font_size)

makeconnect("MeasureTextEx", [Font, c_char_p, c_float, c_float], Vector2)
def measure_text_ex(font: Font, text: str, font_size: float, spacing: float) -> Vector2:
    return lib.MeasureTextEx(font, text.encode(), font_size, spacing)

makeconnect("GetGlyphInfo", [Font, c_int], GlyphInfo)
'''
// Text codepoints management functions (unicode characters)
RLAPI char *LoadUTF8(const int *codepoints, int length);                                    // Load UTF-8 text encoded from codepoints array
RLAPI void UnloadUTF8(char *text);                                                          // Unload UTF-8 text encoded from codepoints array
RLAPI int *LoadCodepoints(const char *text, int *count);                                    // Load all codepoints from a UTF-8 text string, codepoints count returned by parameter
RLAPI void UnloadCodepoints(int *codepoints);                                               // Unload codepoints data from memory
RLAPI int GetCodepointCount(const char *text);                                              // Get total number of codepoints in a UTF-8 encoded string
RLAPI int GetCodepoint(const char *text, int *codepointSize);                               // Get next codepoint in a UTF-8 encoded string, 0x3f('?') is returned on failure
RLAPI int GetCodepointNext(const char *text, int *codepointSize);                           // Get next codepoint in a UTF-8 encoded string, 0x3f('?') is returned on failure
RLAPI int GetCodepointPrevious(const char *text, int *codepointSize);                       // Get previous codepoint in a UTF-8 encoded string, 0x3f('?') is returned on failure
RLAPI const char *CodepointToUTF8(int codepoint, int *utf8Size);                            // Encode one codepoint into UTF-8 byte array (array length returned as parameter)
'''

'''
// Text strings management functions (no UTF-8 strings, only byte chars)
// WARNING 1: Most of these functions use internal static buffers, it's recommended to store returned data on user-side for re-use
// WARNING 2: Some strings allocate memory internally for the returned strings, those strings must be free by user using MemFree()
RLAPI char **LoadTextLines(const char *text, int *count);                                   // Load text as separate lines ('\n')
RLAPI void UnloadTextLines(char **text);                                                    // Unload text lines
RLAPI int TextCopy(char *dst, const char *src);                                             // Copy one string to another, returns bytes copied
RLAPI bool TextIsEqual(const char *text1, const char *text2);                               // Check if two text string are equal
RLAPI unsigned int TextLength(const char *text);                                            // Get text length, checks for '\0' ending
RLAPI const char *TextFormat(const char *text, ...);                                        // Text formatting with variables (sprintf() style)
RLAPI const char *TextSubtext(const char *text, int position, int length);                  // Get a piece of a text string
RLAPI char *TextReplace(const char *text, const char *replace, const char *by);             // Replace text string (WARNING: memory must be freed!)
RLAPI char *TextInsert(const char *text, const char *insert, int position);                 // Insert text in a position (WARNING: memory must be freed!)
RLAPI char *TextJoin(char **textList, int count, const char *delimiter);                    // Join text strings with delimiter
RLAPI char **TextSplit(const char *text, char delimiter, int *count);                       // Split text into multiple strings, using MAX_TEXTSPLIT_COUNT static strings
RLAPI void TextAppend(char *text, const char *append, int *position);                       // Append text at specific position and move cursor!
RLAPI int TextFindIndex(const char *text, const char *find);                                // Find first text occurrence within a string, -1 if not found
RLAPI char *TextToUpper(const char *text);                                                  // Get upper case version of provided string
RLAPI char *TextToLower(const char *text);                                                  // Get lower case version of provided string
RLAPI char *TextToPascal(const char *text);                                                 // Get Pascal case notation version of provided string
RLAPI char *TextToSnake(const char *text);                                                  // Get Snake case notation version of provided string
RLAPI char *TextToCamel(const char *text);                                                  // Get Camel case notation version of provided string
RLAPI int TextToInteger(const char *text);                                                  // Get integer value from text
RLAPI float TextToFloat(const char *text);                                                  // Get float value from text
'''
