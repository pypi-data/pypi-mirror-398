#cython: c_string_type=unicode, c_string_encoding=utf8
'''OpenGL utilities - Dummy implementations for Android compatibility'''

# Capability constants
GLCAP_BGRA = 0x0001
GLCAP_NPOT = 0x0002
GLCAP_S3TC = 0x0004
GLCAP_DXT1 = 0x0008
GLCAP_DT = 0x0010
GLCAP_ETC1 = 0x0020
GLCAP_PVRTC = 0x0040
GLCAP_IMG = 0x0080
GLCAP_ASTC = 0x0100
GLCAP_ATITC = 0x0200
GLCAP_BPTC = 0x0400

cpdef list gl_get_extensions():
    return []

cpdef int gl_has_extension(name):
    return 0

cpdef gl_register_get_size(int constid, int size):
    pass

cpdef int gl_has_capability(int cap):
    return 0

cpdef tuple gl_get_texture_formats():
    return ()

cpdef int gl_has_texture_native_format(fmt):
    return 0

cpdef int gl_has_texture_conversion(fmt):
    return 0

cpdef int gl_has_texture_format(fmt):
    return 0

cpdef tuple gl_get_version():
    return (3, 0)

cpdef int gl_get_version_major():
    return 3

cpdef int gl_get_version_minor():
    return 0
