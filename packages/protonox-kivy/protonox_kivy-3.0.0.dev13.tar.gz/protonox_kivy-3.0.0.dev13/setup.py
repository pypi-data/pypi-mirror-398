#
# Kivy - Cross-platform UI framework
# https://kivy.org/
#

import sys
build_examples = False
if "--build_examples" in sys.argv:
    build_examples = True
    sys.argv.remove("--build_examples")

import os
from os.path import join, dirname, exists, basename, isdir, relpath
from os import walk, environ, makedirs
from collections import OrderedDict
from time import sleep
from pathlib import Path
import logging
import sysconfig
import textwrap
import tempfile
from copy import deepcopy

# Import version directly from _version.py to avoid circular import
exec(open(join(dirname(__file__), 'kivy', '_version.py')).read())
pi_version = None

from setuptools import Distribution, Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

if sys.version_info[0] == 2:
    logging.critical(
        'Unsupported Python version detected!: Kivy 2.0.0 and higher does not '
        'support Python 2. Please upgrade to Python 3, or downgrade Kivy to '
        '1.11.1 - the last Kivy release that still supports Python 2.')


def ver_equal(self, other):
    return self.version == other


def get_description():
    with open(join(dirname(__file__), 'README.md'), 'rb') as fileh:
        return fileh.read().decode("utf8").replace('\r\n', '\n')


def getoutput(cmd, env=None):
    import subprocess
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=env)
    p.wait()
    if p.returncode:  # if not returncode == 0
        print('WARNING: A problem occurred while running {0} (code {1})\n'
              .format(cmd, p.returncode))
        stderr_content = p.stderr.read()
        if stderr_content:
            print('{0}\n'.format(stderr_content))
        return ""
    return p.stdout.read()


def pkgconfig(*packages, **kw):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    lenviron = None

    if platform == 'win32':
        pconfig = join(sys.prefix, 'libs', 'pkgconfig')
        if isdir(pconfig):
            lenviron = environ.copy()
            lenviron['PKG_CONFIG_PATH'] = '{};{}'.format(
                environ.get('PKG_CONFIG_PATH', ''), pconfig)

    if KIVY_DEPS_ROOT and platform != 'win32':
        lenviron = environ.copy()
        lenviron["PKG_CONFIG_PATH"] = "{}:{}:{}".format(
            environ.get("PKG_CONFIG_PATH", ""),
            join(
                KIVY_DEPS_ROOT, "dist", "lib", "pkgconfig"
            ),
            join(
                KIVY_DEPS_ROOT, "dist", "lib64", "pkgconfig"
            ),
        )

    cmd = 'pkg-config --libs --cflags {}'.format(' '.join(packages))
    results = getoutput(cmd, lenviron).split()
    for token in results:
        ext = token[:2].decode('utf-8')
        flag = flag_map.get(ext)
        if not flag:
            continue
        kw.setdefault(flag, []).append(token[2:].decode('utf-8'))
    return kw


def get_isolated_env_paths():
    try:
        # sdl3_dev is installed before setup.py is run, when installing from
        # source due to pyproject.toml. However, it is installed to a
        # pip isolated env, which we need to add to compiler
        import kivy_deps.sdl3_dev as sdl3_dev
    except ImportError:
        return [], []

    root = os.path.abspath(join(sdl3_dev.__path__[0], '../../../..'))
    includes = [join(root, 'Include')] if isdir(join(root, 'Include')) else []
    libs = [join(root, 'libs')] if isdir(join(root, 'libs')) else []
    return includes, libs


def check_c_source_compiles(code, include_dirs=None):
    """Check if C code compiles.
    This function can be used to check if a specific feature is available on
    the current platform, and therefore enable or disable some modules.
    """

    def get_compiler():
        """Get the compiler instance used by setuptools.
        This is a bit hacky, but seems the only way to get the compiler instance
        used by setuptools, without using private APIs or the deprecated
        distutils module. (See: https://github.com/pypa/setuptools/issues/2806)
        """
        fake_dist_build_ext = Distribution().get_command_obj("build_ext")
        fake_dist_build_ext.finalize_options()
        # register an extension to ensure a compiler is created
        fake_dist_build_ext.extensions = [Extension("ignored", ["ignored.c"])]
        # disable building fake extensions
        fake_dist_build_ext.build_extensions = lambda: None
        # run to populate self.compiler
        fake_dist_build_ext.run()
        return fake_dist_build_ext.compiler

    # Create a temporary file which contains the code
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "test.c")
        build_dir = os.path.join(tmpdir, "build")
        with open(temp_file, "w", encoding="utf-8") as tf:
            tf.write(code)
        try:
            get_compiler().compile(
                [temp_file],
                extra_postargs=[],
                include_dirs=include_dirs,
                output_dir=build_dir,
            )
        except Exception as ex:
            print(ex)
            return False
    return True


# -----------------------------------------------------------------------------

# Determine on which platform we are

build_examples = build_examples or \
    os.environ.get('KIVY_BUILD_EXAMPLES', '0') == '1'

platform = sys.platform

# Detect Python for android project (http://github.com/kivy/python-for-android)
ndkplatform = environ.get('NDKPLATFORM')
if ndkplatform is not None and environ.get('LIBLINK'):
    platform = 'android'
kivy_ios_root = environ.get('KIVYIOSROOT', None)
if kivy_ios_root is not None:
    platform = 'ios'
# proprietary broadcom video core drivers
if exists('/opt/vc/include/bcm_host.h'):
    used_pi_version = pi_version
    # Force detected Raspberry Pi version for cross-builds, if needed
    if 'KIVY_RPI_VERSION' in environ:
        used_pi_version = int(environ['KIVY_RPI_VERSION'])
    # The proprietary broadcom video core drivers are not available on the
    # Raspberry Pi 4
    if (used_pi_version or 4) < 4:
        platform = 'rpi'
# use mesa video core drivers
if environ.get('VIDEOCOREMESA', None) == '1':
    platform = 'vc'
mali_paths = (
    '/usr/lib/arm-linux-gnueabihf/libMali.so',
    '/usr/lib/arm-linux-gnueabihf/mali-egl/libmali.so',
    '/usr/local/mali-egl/libmali.so')
if any((exists(path) for path in mali_paths)):
    platform = 'mali'

# Needed when cross-compiling
if environ.get('KIVY_CROSS_PLATFORM'):
    platform = environ.get('KIVY_CROSS_PLATFORM')

# If the user has specified a KIVY_DEPS_ROOT, use that as the root for
# (ATM only SDL) dependencies. Otherwise, use the default locations.
KIVY_DEPS_ROOT = os.environ.get('KIVY_DEPS_ROOT', None)

# Fallback: if a `kivy-dependencies` directory exists inside the source tree,
# use it as a local dependency root. This lets us ship prebuilt native libs
# inside the repository (or CI artifacts) and have `setup.py` pick them up
# automatically when building wheels. It does not change default behavior
# unless that directory is present or the env var is provided.
if not KIVY_DEPS_ROOT:
    local_kivy_deps = join(dirname(__file__), 'kivy-dependencies')
    if exists(local_kivy_deps):
        KIVY_DEPS_ROOT = local_kivy_deps
        print('Using local kivy-dependencies at: {}'.format(KIVY_DEPS_ROOT))

# Heuristic: when building inside python-for-android / p4a, the build runs
# in a cross-compile environment where sys.platform is still the host (e.g.
# 'linux'). Detect common p4a environment variables and force platform to
# 'android' so we avoid enabling desktop-only modules (X11, GStreamer, GL).
if platform != 'android':
    # Broad set of indicators to detect python-for-android / cross-compile
    env_keys = set(environ.keys())
    p4a_indicators = (
        any((k.startswith('P4A_') for k in env_keys)),
        'P4A_protonox-kivy_DIR' in env_keys,
        'PYTHON_FOR_ANDROID' in env_keys,
        'ANDROIDNDK' in env_keys,
        'ANDROID_NDK' in env_keys,
        'ANDROID_NDK_HOME' in env_keys,
        'ANDROID_NDK_ROOT' in env_keys,
        'ANDROID_SDK_ROOT' in env_keys,
        'ANDROID_ARGUMENT' in env_keys,
        'ANDROID_BOOTLOGO' in env_keys,
    )

    # Also inspect common compiler/linker env hints used in isolated build
    cc = environ.get('CC', '')
    cflags = environ.get('CFLAGS', '')
    ldflags = environ.get('LDFLAGS', '')
    if any([
        'android' in cc.lower(),
        'aarch64-linux-android' in cc,
        '-target aarch64-linux-android' in cflags,
        '-DANDROID' in cflags,
        '-landroid' in ldflags,
        '-lGLESv2' in ldflags,
    ]):
        p4a_indicators = tuple(list(p4a_indicators) + [True])

    if any(p4a_indicators):
        platform = 'android'
        print('Forcing platform=android due to python-for-android / cross-compile environment')

# if KIVY_DEPS_ROOT is None and platform is linux or darwin show a warning
# message, because using a system provided SDL3 is not recommended.
# (will be shown only in verbose mode)
if KIVY_DEPS_ROOT is None and platform in ('linux', 'darwin'):
    print("###############################################")
    print("WARNING: KIVY_DEPS_ROOT is not set, using system provided SDL")
    print("which is not recommended as it may be incompatible with Kivy.")
    print("Please build dependencies from source via the provided script")
    print("and set KIVY_DEPS_ROOT to the root of the dependencies directory.")
    print("###############################################")


# -----------------------------------------------------------------------------
# Detect options
#
c_options = OrderedDict()
c_options['use_rpi_vidcore_lite'] = platform == 'rpi'
c_options['use_egl'] = False
c_options['use_opengl_es2'] = None
c_options['use_opengl_mock'] = environ.get('READTHEDOCS', None) == 'True'
c_options['use_sdl3'] = True
c_options['use_pangoft2'] = None
c_options['use_ios'] = False
c_options['use_android'] = False
c_options['use_mesagl'] = False
c_options['use_x11'] = False
c_options['use_wayland'] = None
c_options['use_gstreamer'] = None
c_options['use_avfoundation'] = platform in ['darwin', 'ios']
c_options['use_osx_frameworks'] = platform == 'darwin'
c_options['use_angle_gl_backend'] = platform in ['darwin', 'ios']
c_options['debug_gl'] = False

# now check if environ is changing the default values
for key in list(c_options.keys()):
    ukey = key.upper()
    if ukey in environ:
        value = bool(int(environ[ukey]))
        print('Environ change {0} -> {1}'.format(key, value))
        c_options[key] = value

# If we've detected an Android/p4a build environment, enforce conservative
# defaults: disable desktop-only backends and enable Android-friendly GL.
if platform == 'android':
    print('Applying Android-safe c_options overrides')
    c_options['use_egl'] = True
    c_options['use_opengl_es2'] = True
    c_options['use_opengl_mock'] = False
    c_options['use_sdl3'] = True
    c_options['use_pangoft2'] = False
    c_options['use_ios'] = False
    c_options['use_android'] = True
    c_options['use_mesagl'] = False
    c_options['use_x11'] = False
    c_options['use_wayland'] = False
    c_options['use_gstreamer'] = False
    c_options['use_angle_gl_backend'] = False
    c_options['debug_gl'] = False

use_embed_signature = environ.get('USE_EMBEDSIGNATURE', '0') == '1'
use_embed_signature = use_embed_signature or bool(
    platform not in ('ios', 'android'))

# Auto-detect X11 support on Linux
if platform == 'linux' and not c_options['use_x11']:
    try:
        result = getoutput('pkg-config --exists x11')
        if not result:  # pkg-config returns empty string on success
            print('X11 found via pkg-config, enabling X11 support')
            c_options['use_x11'] = True
    except:
        pass

# -----------------------------------------------------------------------------
# We want to be able to install kivy as a wheel without a dependency
# on cython, but we also want to use cython where possible as a setup
# time dependency through `pyproject.toml` if building from source.

# There are issues with using cython at all on some platforms;
# exclude them from using or declaring cython.

# This determines whether Cython specific functionality may be used.
can_use_cython = True

if platform in ('ios', 'android'):
    # NEVER use or declare cython on these platforms
    print('Not using cython on %s' % platform)
    can_use_cython = False


# -----------------------------------------------------------------------------
# Setup classes

# the build path where kivy is being compiled
src_path = build_path = dirname(__file__)
print("Current directory is: {}".format(os.getcwd()))
print("Source and initial build directory is: {}".format(src_path))

# __version__ is imported by exec, but help linter not complain
__version__ = None
with open(join(src_path, 'kivy', '_version.py'), encoding="utf-8") as f:
    exec(f.read())


class KivyBuildExt(build_ext, object):

    def finalize_options(self):
        super().finalize_options()

        # Build the extensions in parallel if the options has not been set
        if hasattr(self, 'parallel') and self.parallel is None:
            # Use a maximum of 4 cores. If cpu_count returns None, then parallel
            # build will be disabled
            self.parallel = min(4, os.cpu_count() or 0)
            if self.parallel:
                print('Building extensions in parallel using {} cores'.format(
                    self.parallel))

        global build_path
        if (self.build_lib is not None and exists(self.build_lib) and
                not self.inplace):
            build_path = self.build_lib
            print("Updated build directory to: {}".format(build_path))

    def build_extensions(self):
        # build files
        config_h_fn = ('include', 'config.h')
        config_pxi_fn = ('include', 'config.pxi')
        config_py_fn = ('setupconfig.py', )

        # generate headers
        config_h = '// Autogenerated file for Kivy C configuration\n'
        config_pxi = '# Autogenerated file for Kivy Cython configuration\n'
        config_py = '# Autogenerated file for Kivy configuration\n'
        config_py += 'CYTHON_MIN = {0}\nCYTHON_MAX = {1}\n'.format(
            repr(MIN_CYTHON_STRING), repr(MAX_CYTHON_STRING))
        config_py += 'CYTHON_BAD = {0}\n'.format(repr(', '.join(map(
            str, CYTHON_UNSUPPORTED))))

        # generate content
        print('Build configuration is:')
        for opt, value in c_options.items():
            value = int(bool(value))
            print(' * {0} = {1}'.format(opt, value))
            opt = opt.upper()
            config_h += '#define __{0} {1}\n'.format(opt, value)
            config_pxi += 'DEF {0} = {1}\n'.format(opt, value)
            config_py += '{0} = {1}\n'.format(opt, value)
        debug = bool(self.debug)
        print(' * debug = {0}'.format(debug))

        config_pxi += 'DEF DEBUG = {0}\n'.format(debug)
        config_py += 'DEBUG = {0}\n'.format(debug)
        config_pxi += 'DEF PLATFORM = "{0}"\n'.format(platform)
        config_py += 'PLATFORM = "{0}"\n'.format(platform)
        # Backwards compatibility: define USE_SDL2 for code expecting the
        # legacy variable. If SDL3 is enabled, mark SDL2 as disabled.
        try:
            use_sdl3_val = int(bool(c_options.get('use_sdl3')))
        except Exception:
            use_sdl3_val = 0
        config_py += 'USE_SDL2 = {0}\n'.format(0 if use_sdl3_val else 1)
        for fn, content in (
                (config_h_fn, config_h), (config_pxi_fn, config_pxi),
                (config_py_fn, config_py)):
            build_fn = expand(build_path, *fn)
            if self.update_if_changed(build_fn, content):
                print('Updated {}'.format(build_fn))
            src_fn = expand(src_path, *fn)
            if src_fn != build_fn and self.update_if_changed(src_fn, content):
                print('Updated {}'.format(src_fn))

        c = self.compiler.compiler_type
        print('Detected compiler is {}'.format(c))
        if c != 'msvc':
            for e in self.extensions:
                e.extra_link_args += ['-lm']

        # Dump extension maps when building for android or when explicitly
        # requested via env `DUMP_KIVY_EXTENSIONS=1`. This helps detect
        # residual desktop sources/flags (e.g. -lGL, X11 sources) in the
        # isolated pip/p4a wheel build environment.
        try:
            dump_exts = environ.get('DUMP_KIVY_EXTENSIONS', '0') == '1' or platform == 'android'
        except Exception:
            dump_exts = False

        if dump_exts:
            print('=== Kivy extension summary (dump) ===')
            for e in self.extensions:
                print('EXTENSION:', getattr(e, 'name', '<unnamed>'))
                print('  sources:', getattr(e, 'sources', []))
                print('  include_dirs:', getattr(e, 'include_dirs', []))
                print('  libraries:', getattr(e, 'libraries', []))
                print('  extra_link_args:', getattr(e, 'extra_link_args', []))
                print('  extra_compile_args:', getattr(e, 'extra_compile_args', []))
            print('=== end dump ===')

        super().build_extensions()

    def update_if_changed(self, fn, content):
        need_update = True
        if exists(fn):
            with open(fn) as fd:
                need_update = fd.read() != content
        if need_update:
            directory_name = dirname(fn)
            if not exists(directory_name):
                makedirs(directory_name)
            with open(fn, 'w') as fd:
                fd.write(content)
        return need_update


# -----------------------------------------------------------------------------
print("Python path is:\n{}\n".format('\n'.join(sys.path)))
# extract version (simulate doc generation, kivy will be not imported)
environ['KIVY_DOC_INCLUDE'] = '1'
import kivy

# Cython check
# on python-for-android and kivy-ios, cython usage is external
from kivy.tools.packaging.cython_cfg import get_cython_versions, get_cython_msg
CYTHON_REQUIRES_STRING, MIN_CYTHON_STRING, MAX_CYTHON_STRING, \
    CYTHON_UNSUPPORTED = get_cython_versions()
cython_min_msg, cython_max_msg, cython_unsupported_msg = get_cython_msg()

if can_use_cython:
    import Cython
    from packaging import version
    print('\nFound Cython at', Cython.__file__)

    cy_version_str = Cython.__version__
    cy_ver = version.parse(cy_version_str)
    print('Detected supported Cython version {}'.format(cy_version_str))

    if cy_ver < version.Version(MIN_CYTHON_STRING):
        print(cython_min_msg)
    elif cy_ver in CYTHON_UNSUPPORTED:
        print(cython_unsupported_msg)
    elif cy_ver > version.Version(MAX_CYTHON_STRING):
        print(cython_max_msg)
    sleep(1)

# extra build commands go in the cmdclass dict {'command-name': CommandClass}
# see tools.packaging.{platform}.build.py for custom build commands for
# portable packages. Also e.g. we use build_ext command from cython if its
# installed for c extensions.
from kivy.tools.packaging.factory import FactoryBuild
cmdclass = {
    'build_factory': FactoryBuild,
    'build_ext': KivyBuildExt}

try:
    # add build rules for portable packages to cmdclass
    if platform == 'win32':
        from kivy.tools.packaging.win32.build import WindowsPortableBuild
        cmdclass['build_portable'] = WindowsPortableBuild
    elif platform == 'darwin':
        from kivy.tools.packaging.osx.build import OSXPortableBuild
        cmdclass['build_portable'] = OSXPortableBuild
except ImportError:
    print('User distribution detected, avoid portable command.')

# Detect which opengl version headers to use
if platform in ('android', 'darwin', 'ios', 'rpi', 'mali', 'vc'):
    c_options['use_opengl_es2'] = True
elif c_options['use_opengl_es2'] is None:
    c_options['use_opengl_es2'] = \
        environ.get('KIVY_GRAPHICS', '').lower() == 'gles'

print('Using this graphics system: {}'.format(
    ['OpenGL', 'OpenGL ES 2'][int(c_options['use_opengl_es2'] or False)]))

# check if we are in a kivy-ios build
if platform == 'ios':
    print('Kivy-IOS project environment detect, use it.')
    print('Kivy-IOS project located at {0}'.format(kivy_ios_root))
    c_options['use_ios'] = True
    c_options['use_sdl3'] = True

elif platform == 'android':
    c_options['use_android'] = True
    # When building for Android (including cross-compiles), avoid enabling
    # desktop-only modules that require X11/GStreamer/etc. These are not
    # available on Android and will cause compilation failures during
    # python-for-android (p4a) wheel builds.
    c_options['use_x11'] = False
    c_options['use_wayland'] = False
    c_options['use_gstreamer'] = False
    c_options['use_pangoft2'] = False
    c_options['use_osx_frameworks'] = False

# detect gstreamer, only on desktop
# works if we forced the options or in autodetection
if platform not in ('ios', 'android') and (c_options['use_gstreamer']
                                           in (None, True)):
    gstreamer_valid = False
    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        f_path = '/Library/Frameworks/GStreamer.framework'
        if not exists(f_path):
            c_options['use_gstreamer'] = False
            print('GStreamer framework not found, fallback on pkg-config')
        else:
            print('GStreamer framework found')
            gstreamer_valid = True
            c_options['use_gstreamer'] = True
            gst_flags = {
                'extra_link_args': [
                    '-F/Library/Frameworks',
                    '-Xlinker', '-rpath',
                    '-Xlinker', '/Library/Frameworks',
                    '-Xlinker', '-headerpad',
                    '-Xlinker', '190',
                    '-framework', 'GStreamer'],
                'include_dirs': [join(f_path, 'Headers')]}
    elif platform == 'win32':
        gst_flags = pkgconfig('gstreamer-1.0')
        if 'libraries' in gst_flags:
            print('GStreamer found via pkg-config')
            gstreamer_valid = True
            c_options['use_gstreamer'] = True
        else:
            _includes = get_isolated_env_paths()[0] + [
                sysconfig.get_path("include")
            ]
            for include_dir in _includes:
                if exists(join(include_dir, 'gst', 'gst.h')):
                    print('GStreamer found via gst.h')
                    gstreamer_valid = True
                    c_options['use_gstreamer'] = True
                    gst_flags = {
                        'libraries':
                            ['gstreamer-1.0', 'glib-2.0', 'gobject-2.0']}
                    break

    if not gstreamer_valid:
        # use pkg-config approach instead
        gst_flags = pkgconfig('gstreamer-1.0')
        if 'libraries' in gst_flags:
            print('GStreamer found via pkg-config')
            c_options['use_gstreamer'] = True



# detect SDL3 only when explicitly requested (env USE_SDL3=1) or when
# platform-specific code set it (e.g., iOS above). Default is to keep SDL2.
sdl3_flags = {}
sdl3_source = None
if c_options['use_sdl3']:

    sdl3_valid = False
    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        if KIVY_DEPS_ROOT:
            default_sdl3_frameworks_search_path = join(
                KIVY_DEPS_ROOT, "dist", "Frameworks"
            )
        else:
            default_sdl3_frameworks_search_path = "/Library/Frameworks"
        sdl3_frameworks_search_path = environ.get(
            "KIVY_SDL3_FRAMEWORKS_SEARCH_PATH",
            default_sdl3_frameworks_search_path
        )
        sdl3_valid = True

        sdl3_flags = {
            'extra_link_args': [
                '-F{}'.format(sdl3_frameworks_search_path),
                '-Xlinker', '-rpath',
                '-Xlinker', sdl3_frameworks_search_path,
                '-Xlinker', '-headerpad',
                '-Xlinker', '190'],
            'include_dirs': [],
            'extra_compile_args': ['-F{}'.format(sdl3_frameworks_search_path)]
        }

        for name in ('SDL3', 'SDL3_ttf', 'SDL3_image', 'SDL3_mixer'):
            f_path = '{}/{}.framework'.format(sdl3_frameworks_search_path, name)
            if not exists(f_path):
                print('Missing framework {}'.format(f_path))
                sdl3_valid = False
                continue
            sdl3_flags['extra_link_args'] += ['-framework', name]
            sdl3_flags['include_dirs'] += [join(f_path, 'Headers')]
            print('Found sdl3 frameworks: {}'.format(f_path))

        if not sdl3_valid:
            c_options['use_sdl3'] = False
            print('SDL3 frameworks not found, fallback on pkg-config')
        else:
            c_options['use_sdl3'] = True
            sdl3_source = 'macos-frameworks'
            print('Activate SDL3 compilation')

    if not sdl3_valid and platform != "ios":
        # use pkg-config approach instead
        sdl3_flags = pkgconfig('sdl3', 'sdl3-ttf', 'sdl3-image', 'sdl3-mixer')
        if 'libraries' in sdl3_flags:
            print('SDL3 found via pkg-config')
            c_options['use_sdl3'] = True
            sdl3_source = 'pkg-config'


can_autodetect_wayland = (
    platform == "linux" and c_options["use_wayland"] is None
)

if c_options["use_wayland"] or can_autodetect_wayland:
    c_options["use_wayland"] = check_c_source_compiles(
        textwrap.dedent(
            """
        #include <wayland-client.h>
        int main() {
            struct wl_display *display = wl_display_connect(NULL);
            if (display == NULL) {
                return 1;
            }
            wl_display_disconnect(display);
            return 0;
        }
        """
        ),
        include_dirs=[],
    )

# -----------------------------------------------------------------------------
# declare flags

def expand(root, *args):
    return join(root, 'kivy', *args)


class CythonExtension(Extension):

    def __init__(self, *args, **kwargs):
        Extension.__init__(self, *args, **kwargs)
        self.cython_directives = {
            'c_string_encoding': 'utf-8',
            'profile': 'USE_PROFILE' in environ,
            'embedsignature': use_embed_signature,
            'language_level': 3,
            'unraisable_tracebacks': True,
        }


def merge(d1, *args):
    d1 = deepcopy(d1)
    for d2 in args:
        for key, value in d2.items():
            value = deepcopy(value)
            if key in d1:
                d1[key].extend(value)
            else:
                d1[key] = value
    return d1


def determine_base_flags():
    includes, libs = get_isolated_env_paths()

    flags = {
        'libraries': [],
        'include_dirs': [join(src_path, 'kivy', 'include')] + includes,
        'library_dirs': [] + libs,
        'extra_link_args': [],
        'extra_compile_args': []}
    if c_options['use_ios']:
        sysroot = environ.get('IOSSDKROOT', environ.get('SDKROOT'))
        if not sysroot:
            raise Exception('IOSSDKROOT is not set')
        flags['include_dirs'] += [sysroot]
        flags['extra_compile_args'] += ['-isysroot', sysroot]
        flags['extra_link_args'] += ['-isysroot', sysroot]
    elif platform.startswith('freebsd'):
        flags['include_dirs'] += [join(
            environ.get('LOCALBASE', '/usr/local'), 'include')]
        flags['library_dirs'] += [join(
            environ.get('LOCALBASE', '/usr/local'), 'lib')]
    elif platform == 'darwin' and c_options['use_osx_frameworks']:
        v = os.uname()
        if v[2] >= '13.0.0':
            if 'SDKROOT' in environ:
                sysroot = join(environ['SDKROOT'], 'System/Library/Frameworks')
            else:
                # use xcode-select to search on the right Xcode path
                # XXX use the best SDK available instead of a specific one
                import platform as _platform
                xcode_dev = getoutput('xcode-select -p').splitlines()[0]
                sdk_mac_ver = '.'.join(_platform.mac_ver()[0].split('.')[:2])
                print('Xcode detected at {}, and using OS X{} sdk'.format(
                    xcode_dev, sdk_mac_ver))
                sysroot = join(
                    xcode_dev.decode('utf-8'),
                    'Platforms/MacOSX.platform/Developer/SDKs',
                    'MacOSX{}.sdk'.format(sdk_mac_ver),
                    'System/Library/Frameworks')
        else:
            sysroot = ('/System/Library/Frameworks/'
                       'ApplicationServices.framework/Frameworks')
        flags['extra_compile_args'] += ['-F%s' % sysroot]
        flags['extra_link_args'] += ['-F%s' % sysroot]
    elif platform == 'win32':
        flags['include_dirs'] += [sysconfig.get_path('include')]
        flags['library_dirs'] += [join(sys.prefix, "libs")]
    return flags


def determine_angle_flags():
    flags = {'include_dirs': [], 'libraries': []}

    default_include_dir = ""
    default_lib_dir = ""

    if KIVY_DEPS_ROOT:

        default_include_dir = os.path.join(KIVY_DEPS_ROOT, "dist", "include")
        default_lib_dir = os.path.join(KIVY_DEPS_ROOT, "dist", "lib")

    kivy_angle_include_dir = environ.get(
        "KIVY_ANGLE_INCLUDE_DIR", default_include_dir
    )
    kivy_angle_lib_dir = environ.get(
        "KIVY_ANGLE_LIB_DIR", default_lib_dir
    )

    if platform == "darwin":
        flags['libraries'] = ['EGL', 'GLESv2']
        flags['library_dirs'] = [kivy_angle_lib_dir]
        flags['include_dirs'] = [kivy_angle_include_dir]
        flags['extra_link_args'] = [
            "-Wl,-rpath,{}".format(kivy_angle_lib_dir)
        ]
    elif platform == "ios":
        flags['include_dirs'] = [kivy_angle_include_dir]
    else:
        raise Exception("ANGLE is not supported on this platform")

    return flags


def determine_gl_flags():
    kivy_graphics_include = join(src_path, 'kivy', 'include')
    flags = {'include_dirs': [kivy_graphics_include], 'libraries': []}
    base_flags = {'include_dirs': [kivy_graphics_include], 'libraries': []}
    cross_sysroot = environ.get('KIVY_CROSS_SYSROOT')

    if c_options['use_opengl_mock']:
        return flags, base_flags

    if c_options['use_angle_gl_backend']:
        return determine_angle_flags(), base_flags

    if platform == 'win32':
        flags['libraries'] = ['opengl32', 'glew32']
    elif platform == 'ios':
        flags['libraries'] = ['GLESv2']
        flags['extra_link_args'] = ['-framework', 'OpenGLES']
    elif platform == 'darwin':
        flags['extra_link_args'] = ['-framework', 'OpenGL']
    elif platform.startswith('freebsd'):
        flags['libraries'] = ['GL']
    elif platform.startswith('openbsd'):
        flags['include_dirs'] = ['/usr/X11R6/include']
        flags['library_dirs'] = ['/usr/X11R6/lib']
        flags['libraries'] = ['GL']
    elif platform == 'android':
        flags['include_dirs'] = [join(ndkplatform, 'usr', 'include')]
        flags['library_dirs'] = [join(ndkplatform, 'usr', 'lib')]
        flags['libraries'] = ['GLESv2']
    elif platform == 'rpi':

        if not cross_sysroot:
            flags['include_dirs'] = [
                '/opt/vc/include',
                '/opt/vc/include/interface/vcos/pthreads',
                '/opt/vc/include/interface/vmcs_host/linux']
            flags['library_dirs'] = ['/opt/vc/lib']
            brcm_lib_files = (
                '/opt/vc/lib/libbrcmEGL.so',
                '/opt/vc/lib/libbrcmGLESv2.so')

        else:
            print("KIVY_CROSS_SYSROOT: " + cross_sysroot)
            flags['include_dirs'] = [
                cross_sysroot + '/usr/include',
                cross_sysroot + '/usr/include/interface/vcos/pthreads',
                cross_sysroot + '/usr/include/interface/vmcs_host/linux']
            flags['library_dirs'] = [cross_sysroot + '/usr/lib']
            brcm_lib_files = (
                cross_sysroot + '/usr/lib/libbrcmEGL.so',
                cross_sysroot + '/usr/lib/libbrcmGLESv2.so')

        if all((exists(lib) for lib in brcm_lib_files)):
            print('Found brcmEGL and brcmGLES library files '
                  'for rpi platform at ' + dirname(brcm_lib_files[0]))
            gl_libs = ['brcmEGL', 'brcmGLESv2']
        else:
            print(
                'Failed to find brcmEGL and brcmGLESv2 library files '
                'for rpi platform, falling back to EGL and GLESv2.')
            gl_libs = ['EGL', 'GLESv2']
        flags['libraries'] = ['bcm_host'] + gl_libs
    elif platform in ['mali', 'vc']:
        flags['include_dirs'] = ['/usr/include/']
        flags['library_dirs'] = ['/usr/lib/arm-linux-gnueabihf']
        flags['libraries'] = ['GLESv2']
        c_options['use_x11'] = True
        c_options['use_egl'] = True
    else:
        flags['libraries'] = ['GL']
    return flags, base_flags


def determine_sdl3():
    flags = {}
    if not c_options['use_sdl3']:
        return flags

    # If darwin has already been configured with frameworks, don't
    # configure sdl3 via libs.
    # TODO: Move framework configuration here.
    if sdl3_source == "macos-frameworks":
        return sdl3_flags

    default_sdl3_path = None

    if KIVY_DEPS_ROOT:

        default_sdl3_path = os.pathsep.join(
            [
                join(KIVY_DEPS_ROOT, "dist", "lib"),
                join(KIVY_DEPS_ROOT, "dist", "lib64"),
                join(KIVY_DEPS_ROOT, "dist", "include"),
                join(KIVY_DEPS_ROOT, "dist", "include", "SDL3"),
                join(KIVY_DEPS_ROOT, "dist", "include", "SDL3_image"),
                join(KIVY_DEPS_ROOT, "dist", "include", "SDL3_mixer"),
                join(KIVY_DEPS_ROOT, "dist", "include", "SDL3_ttf"),
            ]
        )

    kivy_sdl3_path = environ.get('KIVY_SDL3_PATH', default_sdl3_path)

    includes, _ = get_isolated_env_paths()

    # no pkgconfig info, or we want to use a specific sdl3 path, so perform
    # manual configuration
    flags['libraries'] = ['SDL3', 'SDL3_ttf', 'SDL3_image', 'SDL3_mixer']

    sdl3_paths = kivy_sdl3_path.split(os.pathsep) if kivy_sdl3_path else []

    if not sdl3_paths:
        # Try to find sdl3 in default locations if we don't have a custom path
        sdl3_paths = []
        for include in includes + [join(sys.prefix, 'include')]:
            for _sdl_sub in ['SDL3', 'SDL3_image', 'SDL3_mixer', 'SDL3_ttf']:
                sdl_inc = join(include, _sdl_sub)
                if isdir(sdl_inc):
                    sdl3_paths.append(sdl_inc)

        sdl3_paths.extend(['/usr/local/include/SDL3', '/usr/include/SDL3'])

    flags['include_dirs'] = sdl3_paths
    flags['extra_link_args'] = []
    flags['extra_compile_args'] = []
    flags['library_dirs'] = (
        sdl3_paths if sdl3_paths else
        ['/usr/local/lib/'])

    if kivy_sdl3_path:
        # If we have a custom path, we need to add the rpath to the linker
        # so that the libraries can be found and loaded without having to
        # set LD_LIBRARY_PATH every time.
        flags["extra_link_args"] = [
            f"-Wl,-rpath,{l_path}"
            for l_path in sdl3_paths
            if l_path.endswith("lib")
        ]

    if sdl3_flags:
        flags = merge(flags, sdl3_flags)

    # ensure headers for all the SDL3 and sub libraries are available
    libs_to_check = ['SDL', 'SDL_mixer', 'SDL_ttf', 'SDL_image']
    can_compile = True
    for lib in libs_to_check:
        found = False
        for d in flags['include_dirs']:
            fn = join(d, '{}.h'.format(lib))
            if exists(fn):
                found = True
                print('SDL3: found {} header at {}'.format(lib, fn))
                break

        if not found:
            print('SDL3: missing sub library {}'.format(lib))
            can_compile = False

    if not can_compile:
        c_options['use_sdl3'] = False
        return {}

    return flags


base_flags = determine_base_flags()
gl_flags, gl_flags_base = determine_gl_flags()

# -----------------------------------------------------------------------------
# sources to compile
# all the dependencies have been found manually with:
# grep -inr -E '(cimport|include)' kivy/graphics/context_instructions.{pxd,pyx}
graphics_dependencies = {
    'boxshadow.pxd': ['fbo.pxd', 'context_instructions.pxd',
                      'vertex_instructions.pxd', 'instructions.pxd'],
    'boxshadow.pyx': ['fbo.pxd', 'context_instructions.pxd',
                      'instructions.pyx'],
    'buffer.pyx': ['common.pxi'],
    'context.pxd': ['instructions.pxd', 'texture.pxd', 'vbo.pxd', 'cgl.pxd'],
    'cgl.pxd': ['common.pxi', 'config.pxi', 'gl_redirect.h'],
    'compiler.pxd': ['instructions.pxd'],
    'compiler.pyx': ['context_instructions.pxd'],
    'cgl.pyx': ['cgl.pxd'],
    'cgl_mock.pyx': ['cgl.pxd'],
    'cgl_sdl3.pyx': ['cgl.pxd'],
    'cgl_gl.pyx': ['cgl.pxd'],
    'cgl_glew.pyx': ['cgl.pxd'],
    'context_instructions.pxd': [
        'transformation.pxd', 'instructions.pxd', 'texture.pxd'],
    'fbo.pxd': ['cgl.pxd', 'instructions.pxd', 'texture.pxd'],
    'fbo.pyx': [
        'config.pxi', 'opcodes.pxi', 'transformation.pxd', 'context.pxd'],
    'gl_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd', 'instructions.pxd'],
    'instructions.pxd': [
        'vbo.pxd', 'context_instructions.pxd', 'compiler.pxd', 'shader.pxd',
        'texture.pxd', '../_event.pxd'],
    'instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd',
        'context.pxd', 'common.pxi', 'vertex.pxd', 'transformation.pxd'],
    'opengl.pyx': [
        'config.pxi', 'common.pxi', 'cgl.pxd', 'gl_redirect.h'],
    'opengl_utils.pyx': [
        'opengl_utils_def.pxi', 'cgl.pxd', ],
    'shader.pxd': ['cgl.pxd', 'transformation.pxd', 'vertex.pxd'],
    'shader.pyx': [
        'config.pxi', 'common.pxi', 'cgl.pxd',
        'vertex.pxd', 'transformation.pxd', 'context.pxd',
        'gl_debug_logger.pxi'],
    'stencil_instructions.pxd': ['instructions.pxd'],
    'stencil_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd',
        'gl_debug_logger.pxi'],
    'scissor_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd'],
    'svg.pyx': ['config.pxi', 'common.pxi', 'texture.pxd', 'instructions.pxd',
                'vertex_instructions.pxd', 'tesselator.pxd'],
    'texture.pxd': ['cgl.pxd'],
    'texture.pyx': [
        'config.pxi', 'common.pxi', 'opengl_utils_def.pxi', 'context.pxd',
        'cgl.pxd', 'opengl_utils.pxd',
        'img_tools.pxi', 'gl_debug_logger.pxi'],
    'vbo.pxd': ['buffer.pxd', 'cgl.pxd', 'vertex.pxd'],
    'vbo.pyx': [
        'config.pxi', 'common.pxi', 'context.pxd',
        'instructions.pxd', 'shader.pxd', 'gl_debug_logger.pxi'],
    'vertex.pxd': ['cgl.pxd'],
    'vertex.pyx': ['config.pxi', 'common.pxi'],
    'vertex_instructions.pyx': [
        'config.pxi', 'common.pxi', 'vbo.pxd', 'vertex.pxd',
        'instructions.pxd', 'vertex_instructions.pxd',
        'cgl.pxd', 'texture.pxd', 'vertex_instructions_line.pxi'],
    'vertex_instructions_line.pxi': ['stencil_instructions.pxd']}

sources = {
    '_event.pyx': merge(base_flags, {'depends': ['properties.pxd']}),
    '_clock.pyx': {},
    'weakproxy.pyx': {},
    'properties.pyx': merge(
        base_flags, {'depends': ['_event.pxd', '_metrics.pxd']}),
    '_metrics.pyx': merge(base_flags, {'depends': ['_event.pxd']}),
    'graphics/buffer.pyx': merge(base_flags, gl_flags_base),
    'graphics/context.pyx': merge(base_flags, gl_flags_base),
    'graphics/compiler.pyx': merge(base_flags, gl_flags_base),
    'graphics/context_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/fbo.pyx': merge(base_flags, gl_flags_base),
    'graphics/gl_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/opengl.pyx': merge(base_flags, gl_flags_base),
    'graphics/opengl_utils.pyx': merge(base_flags, gl_flags_base),
    'graphics/shader.pyx': merge(base_flags, gl_flags_base),
    'graphics/stencil_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/scissor_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/texture.pyx': merge(base_flags, gl_flags_base),
    'graphics/transformation.pyx': merge(base_flags, gl_flags_base),
    'graphics/vbo.pyx': merge(base_flags, gl_flags_base),
    'graphics/vertex.pyx': merge(base_flags, gl_flags_base),
    'graphics/vertex_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_mock.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_gl.pyx': merge(base_flags, gl_flags),
    'graphics/cgl_backend/cgl_glew.pyx': merge(base_flags, gl_flags),
    'graphics/cgl_backend/cgl_sdl3.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_angle.pyx': merge(base_flags, gl_flags),
    'graphics/cgl_backend/cgl_debug.pyx': merge(base_flags, gl_flags_base),
    'graphics/egl_backend/egl_angle.pyx': merge(base_flags, gl_flags),
    'core/text/text_layout.pyx': base_flags,
    'core/window/window_info.pyx': base_flags,
    'graphics/tesselator.pyx': merge(base_flags, {
        'include_dirs': ['kivy/lib/libtess2/Include'],
        'c_depends': [
            'lib/libtess2/Source/bucketalloc.c',
            'lib/libtess2/Source/dict.c',
            'lib/libtess2/Source/geom.c',
            'lib/libtess2/Source/mesh.c',
            'lib/libtess2/Source/priorityq.c',
            'lib/libtess2/Source/sweep.c',
            'lib/libtess2/Source/tess.c'
        ]
    }),
    'graphics/svg.pyx': merge(base_flags, gl_flags_base),
    'graphics/boxshadow.pyx': merge(base_flags, gl_flags_base)
}
# -----------------------------------------------------------------------------
# Remove or avoid compiling desktop-only modules when targeting Android.
# Some sources reference X11, GStreamer or desktop GL (glew/angle) and will
# fail during cross-compilation for Android. We defensively drop them from
# the `sources` mapping when building for Android so pip/p4a won't try to
# compile them.
p4a_env_indicators = (
    any((k.startswith('P4A_') for k in environ.keys())),
    'P4A_protonox-kivy_DIR' in environ,
    'PYTHON_FOR_ANDROID' in environ,
    'ANDROIDNDK' in environ,
)

# If we are in a python-for-android / cross-compile environment, or the
# build is explicitly forcing Android-like packaging, strip desktop-only
# modules aggressively to avoid accidental host header/library usage.
if platform == 'android' or any(p4a_env_indicators) or environ.get('FORCE_DROP_DESKTOP_SOURCES') == '1':
    desktop_patterns = (
        'window_x11',
        'window_x11_core',
        'gstplayer',
        '_gstplayer',
        'cgl_glew',
        'cgl_gl',
        'egl_angle',
        'egl_angle_metal',
        'pango',
        'pangoft2',
        'X11',
        'GL',
        'cgl_backend/cgl_debug',  # Additional problematic modules
        'core/window/window_x11',
        # 'graphics/boxshadow',  # Commented out - needed for basic functionality
        'core/text/_text_pango',
        'graphics/svg',
        'graphics/tesselator',
    )
    for key in list(sources.keys()):
        for pat in desktop_patterns:
            if pat in key:
                print(f"Removing desktop-only source for Android/p4a: {key}")
                sources.pop(key, None)
                break

if c_options["use_sdl3"]:
    sdl3_flags = determine_sdl3()

if c_options['use_sdl3'] and sdl3_flags:
    sources['graphics/cgl_backend/cgl_sdl3.pyx'] = merge(
        sources['graphics/cgl_backend/cgl_sdl3.pyx'], sdl3_flags)
    sdl3_depends = {'depends': ['lib/sdl3.pxi']}
    if platform in ('ios', 'darwin'):
        _extra_args_c = {
            'extra_compile_args': ['-ObjC'],
        }
        _extra_args_cpp = {
            'extra_compile_args': ['-ObjC++'],
        }
    else:
        _extra_args_c = {}
        _extra_args_cpp = {}
    for source_file in ('core/window/_window_sdl3.pyx',
                        'core/text/_text_sdl3.pyx',
                        'core/audio_output/audio_sdl3.pyx',
                        'core/clipboard/_clipboard_sdl3.pyx'):

        sources[source_file] = merge(
            base_flags, sdl3_flags, sdl3_depends, _extra_args_c
        )

    sources["core/image/_img_sdl3.pyx"] = merge(
        base_flags, sdl3_flags, sdl3_depends, _extra_args_cpp
    )

if c_options['use_pangoft2'] in (None, True) and platform not in (
                                      'android', 'ios', 'win32'):
    pango_flags = pkgconfig('pangoft2')
    if pango_flags and 'libraries' in pango_flags:
        print('Pango: pangoft2 found via pkg-config')
        c_options['use_pangoft2'] = True
        pango_depends = {'depends': [
            'lib/pango/pangoft2.pxi',
            'lib/pango/pangoft2.h']}
        sources['core/text/_text_pango.pyx'] = merge(
                base_flags, pango_flags, pango_depends)
        print(sources['core/text/_text_pango.pyx'])

if platform in ('darwin', 'ios'):
    # activate ImageIO provider for our core image
    if platform == 'ios':
        osx_flags = {'extra_link_args': [
            '-framework', 'Foundation',
            '-framework', 'UIKit',
            '-framework', 'AudioToolbox',
            '-framework', 'CoreGraphics',
            '-framework', 'QuartzCore',
            '-framework', 'ImageIO',
            '-framework', 'Accelerate']}
    else:
        osx_flags = {'extra_link_args': [
            '-framework', 'ApplicationServices']}
    osx_flags['extra_compile_args'] = ['-ObjC++']
    sources['core/image/img_imageio.pyx'] = merge(
        base_flags, osx_flags)

    sources['core/window/window_info.pyx'] = merge(
        sources['core/window/window_info.pyx'], osx_flags)

if c_options['use_avfoundation']:
    import platform as _platform
    mac_ver = [int(x) for x in _platform.mac_ver()[0].split('.')[:2]]
    if mac_ver >= [10, 7] or platform == 'ios':
        osx_flags = {
            'extra_link_args': ['-framework', 'AVFoundation'],
            'extra_compile_args': ['-ObjC++']
        }
        sources['core/camera/camera_avfoundation.pyx'] = merge(
            base_flags, osx_flags)
    else:
        print('AVFoundation cannot be used, OSX >= 10.7 is required')

if c_options["use_angle_gl_backend"]:

    # kivy.graphics.egl_backend.egl_angle is always compiled,
    # but it only acts as a proxy to the real implementation.

    if platform in ("darwin", "ios"):

        sources["graphics/egl_backend/egl_angle_metal.pyx"] = merge(
            base_flags,
            merge(
                gl_flags,
                {
                    "extra_compile_args": ["-ObjC++"],
                }
            )
        )
        sources["graphics/egl_backend/egl_angle.pyx"] = merge(
            sources["graphics/egl_backend/egl_angle.pyx"],
            {
                "extra_compile_args": ["-ObjC++"],
            }
        )

if c_options['use_rpi_vidcore_lite']:

    # DISPMANX is only available on old versions of Raspbian (Buster).
    # For this reason, we need to be sure that EGL_DISPMANX_* is available
    # before compiling the vidcore_lite module, even if we're on a RPi.
    HAVE_DISPMANX = check_c_source_compiles(
        textwrap.dedent(
            """
        #include <bcm_host.h>
        #include <EGL/eglplatform.h>
        int main(int argc, char **argv) {
            EGL_DISPMANX_WINDOW_T window;
            bcm_host_init();
        }
        """
        ),
        include_dirs=gl_flags["include_dirs"],
    )
    if HAVE_DISPMANX:
        sources['lib/vidcore_lite/egl.pyx'] = merge(
            base_flags, gl_flags)
        sources['lib/vidcore_lite/bcm.pyx'] = merge(
            base_flags, gl_flags)

if c_options['use_x11']:
    libs = ['Xrender', 'X11']
    if c_options['use_egl']:
        libs += ['EGL']
    else:
        libs += ['GL']
    sources['core/window/window_x11.pyx'] = merge(
        base_flags, gl_flags, {
            # FIXME add an option to depend on them but not compile them
            # cause keytab is included in core, and core is included in
            # window_x11
            #
            # 'depends': [
            #    'core/window/window_x11_keytab.c',
            #    'core/window/window_x11_core.c'],
            'libraries': libs})

if c_options['use_gstreamer']:
    sources['lib/gstplayer/_gstplayer.pyx'] = merge(
        base_flags, gst_flags, {
            'depends': ['lib/gstplayer/_gstplayer.h']})

# -----------------------------------------------------------------------------
# extension modules


def get_dependencies(name, deps=None):
    if deps is None:
        deps = []
    for dep in graphics_dependencies.get(name, []):
        if dep not in deps:
            deps.append(dep)
            get_dependencies(dep, deps)
    return deps


def resolve_dependencies(fn, depends):
    fn = basename(fn)
    deps = []
    get_dependencies(fn, deps)
    get_dependencies(fn.replace('.pyx', '.pxd'), deps)

    deps_final = []
    paths_to_test = ['graphics', 'include']
    for dep in deps:
        found = False
        for path in paths_to_test:
            filename = expand(src_path, path, dep)
            if exists(filename):
                deps_final.append(relpath(filename, src_path))
                found = True
                break
        if not found:
            print('ERROR: Dependency for {} not resolved: {}'.format(
                fn, dep
            ))

    return deps_final


def get_extensions_from_sources(sources):

    def _get_cythonized_source_extension(cython_file: str, flags: dict) -> str:
        # The cythonized file can be either a .c or .cpp file
        # depending on the language tag in the .pyx file, or the
        # flag passed to the extension.

        # If the language tag or the flag is not set, we assume
        # the file is a .c file.

        def _to_extension(language: str) -> str:
            return "cpp" if language == "c++" else "c"

        if "language" in flags:
            return _to_extension(flags["language"])

        with open(cython_file, "r", encoding="utf-8") as _source_file:
            for line in _source_file:

                line = line.lstrip()
                if not line:
                    continue
                if line[0] != "#":
                    break

                line = line[1:].lstrip()
                if not line.startswith("distutils:"):
                    continue

                distutils_settings_key, _, distutils_settings_value = [
                    s.strip() for s in line[len("distutils:"):].partition("=")
                ]
                if distutils_settings_key == "language":
                    return _to_extension(distutils_settings_value)

        return _to_extension("c")

    ext_modules = []
    if environ.get('KIVY_FAKE_BUILDEXT'):
        print('Fake build_ext asked, will generate only .h/.c')
        return ext_modules

    # Aggressively prune desktop-only sources and link flags when building
    # for Android or when explicitly requested. This prevents host desktop
    # headers/libs (GL, X11, etc.) from leaking into the p4a pip wheel build.
    try:
        force_drop = environ.get('FORCE_DROP_DESKTOP_SOURCES', '0') == '1' or platform == 'android'
        is_linux = platform.startswith('linux') or platform.startswith('freebsd') or platform.startswith('openbsd')
    except Exception:
        force_drop = platform == 'android'
        is_linux = False
    
    if force_drop:
        print(f"FORCE_DROP is enabled (Android/p4a), filtering desktop modules. Total sources before filtering: {len(sources)}")
        # Remove specific problematic modules completely BEFORE creating extensions
        modules_to_remove = [
            'cgl_backend/cgl_debug',
            'cgl_backend/cgl_angle',  # Add this - causes GL header issues
            'cgl_backend/cgl_mock',  # Add this - also causes GL header issues
            'core/window/window_x11',
            # 'graphics/boxshadow',  # Commented out - needed for basic functionality
            'core/text/_text_pango',
            'graphics/svg',
            'graphics/tesselator',
            'lib/gstplayer/_gstplayer',
            # 'graphics/fbo',  # Commented out - needed for boxshadow
            'graphics/opengl.pyx',  # Add this - uses GL constants not available in Android build
            # 'graphics/opengl_utils.pyx',  # Commented out - now compiles as empty dummy
            'core/image/_img_sdl3',  # SDL3 modules that require external libs
            'core/text/_text_sdl3',
            'core/audio_output/audio_sdl3',
            'core/clipboard/_clipboard_sdl3',
            'core/window/_window_sdl3',  # Add this one
        ]
        sources_to_remove = []
        for pyx in sources.keys():
            for module in modules_to_remove:
                if pyx == module or pyx.endswith('/' + module) or pyx.endswith(module + '.pyx'):
                    sources_to_remove.append(pyx)
                    print(f"FOUND AND SKIPPING desktop-only module for Android/p4a: {pyx} (matched pattern: {module})")
                    break
            # Also filter any module containing 'sdl3' to be safe
            if 'sdl3' in pyx.lower():
                if pyx not in sources_to_remove:
                    sources_to_remove.append(pyx)
                    print(f"FOUND AND SKIPPING SDL3 module for Android/p4a: {pyx}")
        print(f"Removing {len(sources_to_remove)} problematic sources")
        for pyx in sources_to_remove:
            sources.pop(pyx, None)
        print(f"Total sources after filtering: {len(sources)}")
    elif is_linux:
        print(f"Linux build detected, filtering only SDL3 and X11 modules. Total sources before filtering: {len(sources)}")
        # For Linux, only filter SDL3 modules (not installed) and X11 (if needed), but keep graphics and SDL2
        modules_to_remove_linux = [
            'core/image/_img_sdl3',  # SDL3 modules that require external libs
            'core/text/_text_sdl3',
            'core/audio_output/audio_sdl3',
            'core/clipboard/_clipboard_sdl3',
            # Keep _window_sdl3.pyx for Linux compatibility
            'core/window/window_x11',  # Filter X11 for now to avoid compilation issues
        ]
        sources_to_remove = []
        for pyx in sources.keys():
            for module in modules_to_remove_linux:
                if module in pyx:
                    sources_to_remove.append(pyx)
                    print(f"FOUND AND SKIPPING SDL3 module for Linux: {pyx} (matched pattern: {module})")
                    break
            # Also filter any module containing 'sdl3' to be safe
            if 'sdl3' in pyx.lower():
                if pyx not in sources_to_remove:
                    sources_to_remove.append(pyx)
                    print(f"FOUND AND SKIPPING SDL3 module for Linux: {pyx}")
        print(f"Removing {len(sources_to_remove)} problematic sources for Linux")
        for pyx in sources_to_remove:
            sources.pop(pyx, None)
        print(f"Total sources after filtering: {len(sources)}")

    for pyx, flags in sources.items():
        is_graphics = pyx.startswith('graphics')
        pyx_path = join('kivy', pyx)
        depends = [join('kivy', x) for x in flags.pop('depends', [])]
        c_depends = [join('kivy', x) for x in flags.pop('c_depends', [])]
        if not can_use_cython:
            # can't use cython, so use the .c or .cpp files instead.
            _ext = _get_cythonized_source_extension(pyx_path, flags)
            pyx_path = f"{pyx_path[:-4]}.{_ext}"
        if is_graphics:
            depends = resolve_dependencies(pyx_path, depends)
        f_depends = [x for x in depends if x.rsplit('.', 1)[-1] in (
            'c', 'cpp', 'm')]
        module_name = '.'.join(['kivy'] + pyx[:-4].split('/'))
        flags_clean = {'depends': depends}
        for key, value in flags.items():
            if len(value):
                flags_clean[key] = value
        ext_modules.append(CythonExtension(
            module_name, [pyx_path] + f_depends + c_depends, **flags_clean))

    # Apply additional pruning for Android builds after all extensions are created
    if force_drop:
        print('Pruning desktop sources/libs for Android/p4a build')
        
        # Filter out entire problematic extensions BEFORE they cause compilation issues
        modules_to_remove_from_ext = [
            'kivy.cgl_backend.cgl_debug',
            'kivy.cgl_backend.cgl_angle',  # Add this
            'kivy.cgl_backend.cgl_mock',  # Add this - also causes GL header issues
            'kivy.core.window.window_x11', 
            # 'kivy.graphics.boxshadow',  # Commented out - needed for basic functionality
            'kivy.core.text._text_pango',
            'kivy.graphics.svg',
            'kivy.graphics.tesselator',
            'kivy.lib.gstplayer._gstplayer',
            # 'kivy.graphics.fbo',  # Commented out - needed for boxshadow
            'kivy.graphics.opengl',  # Add this - uses GL constants not available in Android build
            'kivy.core.image._img_sdl3',
            'kivy.core.text._text_sdl3',
            'kivy.core.audio_output.audio_sdl3',
            'kivy.core.clipboard._clipboard_sdl3',
            'kivy.core.window._window_sdl3',  # Add this one
        ]
        ext_modules = [e for e in ext_modules if getattr(e, 'name', '') not in modules_to_remove_from_ext]
        print(f'Removed {len(modules_to_remove_from_ext)} problematic extensions for Android build')
        
        for e in ext_modules:
            # filter sources referencing X11 or desktop window backends
            old_sources = list(getattr(e, 'sources', []) or [])
            new_sources = [s for s in old_sources if 'window_x11' not in s and '/x11/' not in s and 'x11' not in s.lower()]
            if len(new_sources) != len(old_sources):
                print(' * trimmed sources for', getattr(e, 'name', '<ext>'))
                e.sources = new_sources

            # remove desktop GL libraries and link args
            old_link_args = list(getattr(e, 'extra_link_args', []) or [])
            e.extra_link_args = [a for a in old_link_args if '-lGL' not in a and a.strip() != '-lGL']
            if old_link_args != e.extra_link_args:
                print(' * removed -lGL from extra_link_args for', getattr(e, 'name', '<ext>'))

            old_libs = list(getattr(e, 'libraries', []) or [])
            # blacklist common desktop libraries that must not be linked
            desktop_lib_blacklist = ('GL', 'GLU', 'gl', 'X11', 'Xrender', 'Xrandr', 'gstreamer-1.0', 'gstreamer', 'gst', 'Xxf86vm')
            e.libraries = [l for l in old_libs if l not in desktop_lib_blacklist]
            if old_libs != e.libraries:
                print(' * removed desktop libraries for', getattr(e, 'name', '<ext>'))

            # sanitize include_dirs: drop host system includes that can leak
    elif is_linux:
        print('Pruning SDL3 sources/libs for Linux build')
        
        # Filter out only SDL3 extensions for Linux
        modules_to_remove_from_ext_linux = [
            'kivy.core.image._img_sdl3',
            'kivy.core.text._text_sdl3',
            'kivy.core.audio_output.audio_sdl3',
            'kivy.core.clipboard._clipboard_sdl3',
            'kivy.core.window._window_sdl3',
        ]
        ext_modules = [e for e in ext_modules if getattr(e, 'name', '') not in modules_to_remove_from_ext_linux]
        print(f'Removed {len(modules_to_remove_from_ext_linux)} SDL3 extensions for Linux build')
        
        for e in ext_modules:
            # For Linux, only filter SDL3-related link args and libraries
            old_link_args = list(getattr(e, 'extra_link_args', []) or [])
            e.extra_link_args = [a for a in old_link_args if 'SDL3' not in a]
            if old_link_args != e.extra_link_args:
                print(' * removed SDL3 from extra_link_args for', getattr(e, 'name', '<ext>'))

            old_libs = list(getattr(e, 'libraries', []) or [])
            # Only blacklist SDL3 libraries for Linux
            sdl3_lib_blacklist = ('SDL3', 'SDL3_ttf', 'SDL3_image', 'SDL3_mixer')
            e.libraries = [l for l in old_libs if l not in sdl3_lib_blacklist]
            if old_libs != e.libraries:
                print(' * removed SDL3 libraries for', getattr(e, 'name', '<ext>'))

    return ext_modules


ext_modules = get_extensions_from_sources(sources)

# Diagnostic mode: when building from an external script we may want to
# only dump the extension metadata (sources, include_dirs, libraries,
# link args) without attempting to compile. This is useful to inspect
# residual desktop flags during p4a/pip isolated wheel builds.
try:
    dump_only = environ.get('DUMP_KIVY_EXTENSIONS_ONLY', '0') == '1'
except Exception:
    dump_only = False

if dump_only:
    dump_path = environ.get('DUMP_KIVY_EXTENSIONS_PATH', None)
    header = '=== Kivy extension summary (dump-only) ===\n'
    lines = [header]
    for e in ext_modules:
        lines.append(f"EXTENSION: {getattr(e, 'name', '<unnamed>')}\n")
        lines.append(f"  sources: {getattr(e, 'sources', [])}\n")
        lines.append(f"  include_dirs: {getattr(e, 'include_dirs', [])}\n")
        lines.append(f"  libraries: {getattr(e, 'libraries', [])}\n")
        lines.append(f"  extra_link_args: {getattr(e, 'extra_link_args', [])}\n")
        lines.append(f"  extra_compile_args: {getattr(e, 'extra_compile_args', [])}\n")
    lines.append('=== end dump-only ===\n')
    output = ''.join(lines)
    if dump_path:
        try:
            with open(dump_path, 'w', encoding='utf-8') as fd:
                fd.write(output)
            print(f"Wrote dump-only output to: {dump_path}")
        except Exception as ex:
            print('Failed writing dump file:', ex)
            print(output)
    else:
        print(output)
    # Do not exit here: allow the build backend to continue preparing
    # metadata. The dump is informational only.
    # Prevent setuptools/pip from attempting to build C extensions in this
    # dump-only diagnostic mode — return an empty extension list so the
    # backend only generates metadata.
    ext_modules = []


# -----------------------------------------------------------------------------
# automatically detect data files
split_examples = int(environ.get('KIVY_SPLIT_EXAMPLES', '1'))
data_file_prefix = 'share/protonox-kivy-'
examples = {}
examples_allowed_ext = ('readme', 'py', 'wav', 'png', 'jpg', 'svg', 'json',
                        'avi', 'gif', 'txt', 'ttf', 'obj', 'mtl', 'kv', 'mpg',
                        'glsl', 'zip')
for root, subFolders, files in walk('examples'):
    for fn in files:
        ext = fn.split('.')[-1].lower()
        if ext not in examples_allowed_ext:
            continue
        filename = join(root, fn)
        directory = '%s%s' % (data_file_prefix, dirname(filename))
        if directory not in examples:
            examples[directory] = []
        examples[directory].append(filename)

binary_deps = []
binary_deps_path = join(src_path, 'kivy', 'binary_deps')
if isdir(binary_deps_path):
    for root, dirnames, filenames in walk(binary_deps_path):
        for fname in filenames:
            binary_deps.append(
                join(root.replace(binary_deps_path, 'binary_deps'), fname))


def glob_paths(*patterns, excludes=('.pyc', )):
    files = []
    base = Path(join(src_path, 'kivy'))

    for pat in patterns:
        for f in base.glob(pat):
            if f.suffix in excludes:
                continue
            files.append(str(f.relative_to(base)))
    return files


# -----------------------------------------------------------------------------
# setup !
if not build_examples:
    setup(
        name='protonox-kivy',
        version=__version__,
        author='ProtonoxDEV (fork maintainers)',
        author_email='contact@protonox.dev',
        url='https://github.com/ProtonoxDEV/Protonox-Kivy-Multiplatform-Framework',
        project_urls={
            'Source': 'https://github.com/ProtonoxDEV/Protonox-Kivy-Multiplatform-Framework',
            'Documentation': 'https://github.com/ProtonoxDEV/Protonox-Kivy-Multiplatform-Framework/tree/codex/normalize-and-clean-repository-structure/kivy-protonox-version/doc',
            'Bug Reports': 'https://github.com/ProtonoxDEV/Protonox-Kivy-Multiplatform-Framework/issues',
            'Upstream Kivy': 'https://github.com/kivy/kivy',
        },
        license='MIT',
        description=(
            'Protonox-maintained fork of Kivy intended as a '
            'drop-in compatible build for Protonox tooling and deployments.'),
        long_description=get_description(),
        long_description_content_type='text/markdown',
        ext_modules=ext_modules,
        cmdclass=cmdclass,
        packages=find_packages(include=['kivy*']),
        package_dir={'kivy': 'kivy'},
        package_data={
            'kivy':
                glob_paths('*.pxd', '*.pxi') +
                glob_paths('**/*.pxd', '**/*.pxi') +
                glob_paths('data/**/*.*') +
                glob_paths('include/**/*.*') +
                glob_paths('tools/**/*.*', excludes=('.pyc', '.enc')) +
                glob_paths('graphics/**/*.h') +
                glob_paths('tests/**/*.*') +
                [
                    'setupconfig.py',
                ] + binary_deps
        },
        data_files=[] if split_examples else list(examples.items()),
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: MacOS X',
            'Environment :: Win32 (MS Windows)',
            'Environment :: X11 Applications',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: BSD :: FreeBSD',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            'Programming Language :: Python :: 3.13',
            'Programming Language :: Python :: 3.14',
            'Topic :: Artistic Software',
            'Topic :: Games/Entertainment',
            'Topic :: Multimedia :: Graphics :: 3D Rendering',
            'Topic :: Multimedia :: Graphics :: Capture :: Digital Camera',
            'Topic :: Multimedia :: Graphics :: Presentation',
            'Topic :: Multimedia :: Graphics :: Viewers',
            'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
            'Topic :: Multimedia :: Video :: Display',
            'Topic :: Scientific/Engineering :: Human Machine Interfaces',
            'Topic :: Scientific/Engineering :: Visualization',
            ('Topic :: Software Development :: Libraries :: '
             'Application Frameworks'),
            'Topic :: Software Development :: User Interfaces'])
else:
    setup(
        name='protonox-kivy-examples',
        version=__version__,
        author='ProtonoxDEV (fork maintainers)',
        author_email='contact@protonox.dev',
        url='https://github.com/ProtonoxDEV/Protonox-Kivy-Multiplatform-Framework',
        license='MIT',
        description=('Protonox examples and assets for the protonox-kivy fork.'),
        long_description_content_type='text/markdown',
        long_description=get_description(),
        data_files=list(examples.items()))
