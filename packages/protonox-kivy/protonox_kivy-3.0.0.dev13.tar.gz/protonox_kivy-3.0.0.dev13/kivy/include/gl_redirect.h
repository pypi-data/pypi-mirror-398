/*
 * Includes GL headers.
 */
#ifndef __gl_redirect_h_
#define __gl_redirect_h_

#include "config.h"

/* Normalize Android macro when toolchains define __ANDROID__ */
#if defined(__ANDROID__) && !defined(ANDROID)
#define ANDROID 1
#endif

#if defined(_WIN32)
#  include <windows.h>
#  include <string.h>
#endif

/* If building for Android, prefer GLES2 headers and avoid desktop GL. */
#if defined(ANDROID) || defined(__ANDROID__)
#  ifdef __APPLE__
#    include <OpenGLES/ES2/gl.h>
#    include <OpenGLES/ES2/glext.h>
#  else
#    include <GLES2/gl2.h>
#    include <GLES2/gl2ext.h>
#  endif

/* Provide minimal typedefs if GLES headers are not available */
#  ifndef GLsizei
typedef int GLsizei;
#  endif
#  ifndef GLint
typedef int GLint;
#  endif
#  ifndef GLuint
typedef unsigned int GLuint;
#  endif
#  ifndef GLfloat
typedef float GLfloat;
#  endif

#else /* non-Android: try to include desktop GL headers */

#  if __USE_OPENGL_ES2
#    if __APPLE__
#      include "common_subset.h"
#    else
#      include <GLES2/gl2.h>
#      include <GLES2/gl2ext.h>
#    endif
#  else
#    ifndef __USE_OPENGL_MOCK
#      ifdef __APPLE__
#        include <OpenGL/gl.h>
#        include <OpenGL/glext.h>
#      else
#        if defined(__has_include)
#          if __has_include(<GL/gl.h>)
#          endif
#        else
#        endif
			 /* Avoid including desktop <GL/gl.h> or <GL/glext.h> during
				 cross-compiles. If the build truly needs desktop GL, it must
				 explicitly provide appropriate include paths or enable a
				 desktop-only build configuration. */
			 /* Intentionally omitted: <GL/gl.h> and <GL/glext.h> */
#      endif
#    endif
#  endif

#endif /* ANDROID */

#endif /* __gl_redirect_h_ */
