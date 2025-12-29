from ._classes import *








"""
// File system functions
RLAPI bool FileExists(const char *fileName);                      // Check if file exists
RLAPI bool DirectoryExists(const char *dirPath);                  // Check if a directory path exists
RLAPI bool IsFileExtension(const char *fileName, const char *ext); // Check file extension (recommended include point: .png, .wav)
RLAPI int GetFileLength(const char *fileName);                    // Get file length in bytes (NOTE: GetFileSize() conflicts with windows.h)
RLAPI const char *GetFileExtension(const char *fileName);         // Get pointer to extension for a filename string (includes dot: '.png')
RLAPI const char *GetFileName(const char *filePath);              // Get pointer to filename for a path string
RLAPI const char *GetFileNameWithoutExt(const char *filePath);    // Get filename string without extension (uses static string)
RLAPI const char *GetDirectoryPath(const char *filePath);         // Get full path for a given fileName with path (uses static string)
RLAPI const char *GetPrevDirectoryPath(const char *dirPath);      // Get previous directory path for a given path (uses static string)
RLAPI const char *GetWorkingDirectory(void);                      // Get current working directory (uses static string)
RLAPI const char *GetApplicationDirectory(void);                  // Get the directory of the running application (uses static string)
RLAPI int MakeDirectory(const char *dirPath);                     // Create directories (including full path requested), returns 0 on success
RLAPI bool ChangeDirectory(const char *dir);                      // Change working directory, return true on success
RLAPI bool IsPathFile(const char *path);                          // Check if a given path is a file or a directory
RLAPI bool IsFileNameValid(const char *fileName);                 // Check if fileName is valid for the platform/OS
RLAPI FilePathList LoadDirectoryFiles(const char *dirPath);       // Load directory filepaths
RLAPI FilePathList LoadDirectoryFilesEx(const char *basePath, const char *filter, bool scanSubdirs); // Load directory filepaths with extension filtering and recursive directory scan. Use 'DIR' in the filter string to include directories in the result
RLAPI void UnloadDirectoryFiles(FilePathList files);              // Unload filepaths
RLAPI bool IsFileDropped(void);                                   // Check if a file has been dropped into window
RLAPI FilePathList LoadDroppedFiles(void);                        // Load dropped filepaths
RLAPI void UnloadDroppedFiles(FilePathList files);                // Unload dropped filepaths
RLAPI long GetFileModTime(const char *fileName);                  // Get file modification time (last write time)
"""

# File system functions -----------------------------------------------------

makeconnect("FileExists", [c_char_p], c_bool)
def file_exists(path: str) -> bool:
    return lib.FileExists(path.encode())

makeconnect("DirectoryExists", [c_char_p], c_bool)
def directory_exists(path: str) -> bool:
    return lib.DirectoryExists(path.encode())

makeconnect("IsFileExtension", [c_char_p, c_char_p], c_bool)
def is_file_extension(fname: str, ext: str) -> bool:
    return lib.IsFileExtension(fname.encode(), ext.encode())

makeconnect("GetFileLength", [c_char_p], c_int)
def get_file_length(path: str) -> int:
    return lib.GetFileLength(path.encode())

makeconnect("GetFileExtension", [c_char_p], c_char_p)
def get_file_extension(path: str) -> str:
    return lib.GetFileExtension(path.encode()).decode()

makeconnect("GetFileName", [c_char_p], c_char_p)
def get_file_name(path: str) -> str:
    return lib.GetFileName(path.encode()).decode()

makeconnect("GetFileNameWithoutExt", [c_char_p], c_char_p)
def get_file_name_without_ext(path: str) -> str:
    return lib.GetFileNameWithoutExt(path.encode()).decode()

makeconnect("GetDirectoryPath", [c_char_p], c_char_p)
def get_directory_path(path: str) -> str:
    return lib.GetDirectoryPath(path.encode()).decode()

makeconnect("GetPrevDirectoryPath", [c_char_p], c_char_p)
def get_prev_directory_path(path: str) -> str:
    return lib.GetPrevDirectoryPath(path.encode()).decode()

makeconnect("GetWorkingDirectory", [], c_char_p)
def get_working_directory() -> str:
    return lib.GetWorkingDirectory().decode()

makeconnect("GetApplicationDirectory", [], c_char_p)
def get_application_directory() -> str:
    return lib.GetApplicationDirectory().decode()

makeconnect("MakeDirectory", [c_char_p], c_int)
def make_directory(path: str) -> int:
    return lib.MakeDirectory(path.encode())

makeconnect("ChangeDirectory", [c_char_p], c_bool)
def change_directory(path: str) -> bool:
    return lib.ChangeDirectory(path.encode())

makeconnect("IsPathFile", [c_char_p], c_bool)
def is_path_file(path: str) -> bool:
    return lib.IsPathFile(path.encode())

makeconnect("IsFileNameValid", [c_char_p], c_bool)
def is_file_name_valid(fname: str) -> bool:
    return lib.IsFileNameValid(fname.encode())

# Directory loading ---------------------------------------------------------

makeconnect("LoadDirectoryFiles", [c_char_p], FilePathList)
def load_directory_files(path: str) -> FilePathList:
    return lib.LoadDirectoryFiles(path.encode())

makeconnect("LoadDirectoryFilesEx", [c_char_p, c_char_p, c_bool], FilePathList)
def load_directory_files_ex(base: str, filter: str, scan_subdirs: bool) -> FilePathList:
    return lib.LoadDirectoryFilesEx(base.encode(), filter.encode(), scan_subdirs)

makeconnect("UnloadDirectoryFiles", [FilePathList], None)
def unload_directory_files(list_obj: FilePathList):
    lib.UnloadDirectoryFiles(list_obj)

# File dropping -------------------------------------------------------------

makeconnect("IsFileDropped", [], c_bool)
def is_file_dropped() -> bool:
    return lib.IsFileDropped()

makeconnect("LoadDroppedFiles", [], FilePathList)
def load_dropped_files() -> FilePathList:
    return lib.LoadDroppedFiles()

makeconnect("UnloadDroppedFiles", [FilePathList], None)
def unload_dropped_files(list_obj: FilePathList):
    lib.UnloadDroppedFiles(list_obj)

# Modification time ---------------------------------------------------------

makeconnect("GetFileModTime", [c_char_p], c_long)
def get_file_mod_time(path: str) -> int:
    return lib.GetFileModTime(path.encode())
