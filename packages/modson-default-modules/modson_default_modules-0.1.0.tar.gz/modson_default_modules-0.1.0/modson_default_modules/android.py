import os
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from modson_default_modules.java import JavaModule
from mesonbuild.build import CustomTarget, Target
from mesonbuild.modules import ModuleReturnValue, ModuleInfo, ModuleState, noKwargs
from mesonbuild.interpreter import Interpreter
from mesonbuild import mesonlib
from mesonbuild.interpreterbase.decorators import KwargInfo, typed_pos_args, typed_kwargs
from mesonbuild.interpreter.type_checking import NoneType


class AndroidModule(JavaModule):
    INFO = ModuleInfo('android', Path(__file__).parent.joinpath("VERSION").read_text(), None, unstable=True)

    def __init__(self, interpreter: Interpreter) -> None:
        super().__init__(interpreter)
        del self.methods["jar"]
        self.methods.update({
            "apk": self.compile_apk,
            "compile_dex": self.compile_dex,
            "get_nativeglue_dir": self.get_nativeglue_dep,
            "get_nativeglue_source": self.get_nativeglue_source,
            "get_android_jar": self.get_android_jar,
        })

    @typed_pos_args(
        'android_ext.apk',
        varargs=(str, mesonlib.File, Target),
        min_varargs=2,
    )
    @typed_kwargs(
        'android_ext.apk',
        KwargInfo('manifest', (str, mesonlib.File, NoneType), default=None),
        KwargInfo('ressources', (str, NoneType), default=None),
        KwargInfo('assets', (str, NoneType), default=None),
        KwargInfo('library', (str, mesonlib.File, NoneType), default=None),
        KwargInfo('debug', (bool), default=False),
        KwargInfo('append_libcxx_shared', (bool), default=False),
        KwargInfo('lib_cxx_name', (str, NoneType), default=None),
        KwargInfo('android_platform', (str, int, NoneType), default=None),
    )
    def compile_apk(self, state: ModuleState, args: Tuple[List[mesonlib.FileOrString]],
                    kwargs: Dict[str, Optional[str]]) -> ModuleReturnValue:
        """
        Compile Java class files into a Dalvik Executable (DEX) file.
        """
        manifest = cast('str | mesonlib.File | None', kwargs.get('manifest'))
        ressources = cast('str | None', kwargs.get('ressources'))
        assets = cast('str | None', kwargs.get('assets'))
        library = cast('str | mesonlib.File | None', kwargs.get('library'))
        debug = cast('bool', kwargs.get('debug'))
        append_libcxx_shared = cast('bool', kwargs.get('append_libcxx_shared'))
        lib_cxx_name = cast('str | None', kwargs.get('lib_cxx_name'))
        android_platform = cast('str | int | None', kwargs.get('android_platform'))

        if isinstance(library, mesonlib.File):
            library = library.__str__()

        if isinstance(manifest, mesonlib.File):
            manifest = manifest.__str__()

        name = str(args[0][0])
        files_args = mesonlib.listify(args[0][1:])

        files = [f for f in files_args if isinstance(f, mesonlib.File) or type(f) is str]

        custom_targets: List[CustomTarget] = [t for t in files_args if t not in files]

        targets_dex = [t for t in custom_targets if t.name.startswith('dex_')]

        targets = [t for t in custom_targets if t not in targets_dex] + files

        if len(targets_dex) > 1:
            raise mesonlib.MesonException('android_ext.apk can only accept one dex file as input')
        target_dex = targets_dex[0] if len(targets_dex) == 1 else None

        new_objects = []
        name = "apk_" + name
        if append_libcxx_shared:
            if lib_cxx_name is None:
                raise mesonlib.MesonException('When append_libcxx_shared is True, lib_cxx_name must be provided.')
            if android_platform is None:
                raise mesonlib.MesonException('When append_libcxx_shared is True, android_platform must be provided.')
            lib_folder = self._get_android_lib_folder(state, lib_cxx_name, android_platform)
            if not os.path.isdir(lib_folder):
                raise mesonlib.MesonException(f'Library folder "{lib_folder}" does not exist.')
            targets.append(os.path.join(lib_folder, '..', 'libc++_shared.so'))

        move_command = self._jar_move_javac_to_temp(state, name, targets, subdir="lib/arm64-v8a", target_is_dir=False)
        new_objects.append(move_command)
        inputs: List[Any] = []

        if target_dex is not None:
            mv_command = CustomTarget(
                name + '_dex_move',
                state.subdir,
                state.subproject,
                state.environment,
                mesonlib.listify([
                    'cp',
                    '-rf',
                    '@INPUT@',
                    '@OUTPUT@',
                ]),
                sources=[target_dex],
                outputs=[f'move_{name}_dir/classes.dex'],
                backend=state.backend,
                build_by_default=True,
            )
            new_objects.append(mv_command)
            inputs.append(mv_command)

        if manifest is not None:
            inputs.append(manifest)

        aapt = self._compile_apk(
            state,
            name,
            move_command,
            target_dex,
            inputs,
            manifest,
            ressources,
            assets,
            library,
            debug,
        )
        new_objects.append(aapt)
        return ModuleReturnValue(aapt, new_objects)

    @typed_pos_args(
        'android_ext.compile_dex',
        varargs=(str, mesonlib.File, Target),
        min_varargs=2,
    )
    @typed_kwargs(
        'android_ext.compile_dex',
        KwargInfo('library', (str, NoneType), default=None),
        KwargInfo('source', (str, int, NoneType), default=None),
        KwargInfo('target', (str, int, NoneType), default=None),
    )
    def compile_dex(self, state: ModuleState, args: Tuple[List[mesonlib.FileOrString]],
                    kwargs: Dict[str, Optional[str]]) -> ModuleReturnValue:
        """
        Compile Java class files into a Dalvik Executable (DEX) file.
        """
        library = cast('str | mesonlib.File | None', kwargs.get('library'))
        source = cast('str | int | None', kwargs.get('source'))
        target = cast('str | int | None', kwargs.get('target'))

        if isinstance(library, mesonlib.File):
            library = library.__str__()

        name = str(args[0][0])
        files_args = args[0][1:]

        # files to compile
        files = [f for f in files_args if isinstance(f, mesonlib.File) or type(f) is str]
        # targets that are already compiled
        targets: List[CustomTarget] = [t for t in files_args if t not in files]

        # new targets created in this function
        new_objects = []
        if len(files) != 0:
            # compile the given files first
            javac_target = self._javac_compile(
                state,
                name,
                files,
                source=source,
                target=target,
                bootclasspath=library,
            )
            new_objects.append(javac_target)
            targets.append(javac_target)
        self._test_target_compatibility(targets)
        name = "dex_" + name
        move_commands = self._jar_move_javac_to_temp(state, name, targets)
        new_objects.append(move_commands)

        dex_commands = self._compile_dex(
            state,
            name,
            javac=[move_commands],
            library=library,
        )
        print(f"{name}_dir/classes.dex will be generated.")
        new_objects.append(dex_commands)

        return ModuleReturnValue(dex_commands, new_objects)

    @typed_pos_args('android_ext.get_android_jar', (str, int))
    @noKwargs
    def get_android_jar(self, state: ModuleState, args: Tuple, kwargs: Dict[str, Any]) -> ModuleReturnValue:
        android_sdk_root = self._get_android_sdk_root()
        android_version = args[0]
        android_jar_path = os.path.join(android_sdk_root, 'platforms', f'android-{android_version}', 'android.jar')
        if not os.path.isfile(android_jar_path):
            raise mesonlib.MesonException(f'android.jar not found at expected location "{android_jar_path}".')
        return ModuleReturnValue(android_jar_path, [android_jar_path])

    @typed_pos_args('android_ext.get_nativeglue_source')
    @noKwargs
    def get_nativeglue_source(self, state: ModuleState, args: Tuple, kwargs: Dict[str, Any]) -> ModuleReturnValue:
        native_glue_dir = self._get_nativeglue_source_dir()
        source_files = glob.glob(os.path.join(native_glue_dir, '*.c'))
        if not source_files:
            raise mesonlib.MesonException(f'No source files found in native glue directory "{native_glue_dir}".')
        return ModuleReturnValue(source_files, [source_files])

    @typed_pos_args('android_ext.get_nativeglue_dep')
    @noKwargs
    def get_nativeglue_dep(self, state: ModuleState, args: Tuple, kwargs: Dict[str, Any]) -> ModuleReturnValue:
        """
        Get the directory containing the Android native app glue source files.
        """

        source_dir = self._get_nativeglue_source_dir()
        return ModuleReturnValue(source_dir, [source_dir])

    def _compile_apk(self, state: ModuleState, name: str,
                     move_command: CustomTarget,
                     input_dex: CustomTarget | None,
                     inputs: List[Any],
                     manifest: str | None,
                     ressources: str | None,
                     assets: str | None,
                     library: str | None,
                     debug: bool,
                     ) -> CustomTarget:
        """
        Compile the APK using aapt tool.

        Can include manifest, ressources, assets, dex file and native library.
        """
        appt_command = mesonlib.listify([
            "aapt",
            "package",
            "-f",
            *(['--debug-mode'] if debug else []),
            *(['-M', str(manifest)] if manifest else []),
            *(['-S', str(ressources)] if ressources else []),
            *(['-A', str(assets)] if assets else []),
            *(["-D", 'classes.dex'] if input_dex else []),
            "-I", str(library) if library else "",
            "-F", "@OUTPUT@",
            "@INPUT0@_dir",
        ])

        sources = [move_command] + ([input_dex] if input_dex else []) + inputs

        output = f'{name}.apk'
        return CustomTarget(
            name,
            state.subdir,
            state.subproject,
            state.environment,
            appt_command,
            sources=sources,
            outputs=[output],
            backend=state.backend,
            build_by_default=True,
        )

    def _compile_dex(self, state: ModuleState, name: str,
                     javac: List[CustomTarget],
                     library: str | None) -> CustomTarget:
        """
        Compile Java class files into a Dalvik Executable (DEX) file.
        """
        command = mesonlib.listify([
            'mkdir',
            '-p',
            '@OUTDIR@',
            '&&',
            'sh',
            '-c',
            'echo $(find @INPUT@_dir -name "*.class") > /tmp/dex_input_$(basename @INPUT@_dir).txt',
            '&&',
            'xargs',
            '-a',
            '/tmp/dex_input_@PLAINNAME@_dir.txt',
            'd8',
            '--output',
            '@OUTDIR@',
            *(["--lib", str(library)] if library else []),
        ])
        output = f'{name}_dir/classes.dex'

        return CustomTarget(
            name,
            state.subdir,
            state.subproject,
            state.environment,
            command,
            sources=javac,
            outputs=[output],
            backend=state.backend,
            build_by_default=True,
        )

    def _get_android_lib_folder(self, state: ModuleState, lib_cxx_name: str, android_platform: str | int) -> str:
        """
        Get the Android library folder for the given C++ standard library and platform.

        Raises an exception if the library folder does not exist.
        """
        ndk_root = self._get_android_ndk_root()
        build_machine_name = f"{state.environment.machines.build.system}-{state.environment.machines.build.cpu}"
        lib_folder = os.path.join(
            ndk_root, 'toolchains', 'llvm', 'prebuilt',
            build_machine_name, 'sysroot', 'usr', 'lib', lib_cxx_name,
            str(android_platform)
        )
        if not os.path.isdir(lib_folder):
            raise mesonlib.MesonException(f'Library folder "{lib_folder}" does not exist.')
        return lib_folder

    def _get_nativeglue_source_dir(self) -> str:
        """
        Get the directory containing the Android native app glue source files.
        """

        ndk_root = self._get_android_ndk_root()
        native_glue_dir = os.path.join(ndk_root, 'sources', 'android', 'native_app_glue')
        if not os.path.isdir(native_glue_dir):
            raise mesonlib.MesonException(f'Native glue source directory "{native_glue_dir}" does not exist.')
        return native_glue_dir

    def _get_android_ndk_root(self) -> str:
        """
        Get the Android NDK root directory from environment variables.

        Raises an exception if the NDK root is not set or invalid.
        """
        android_ndk_root = os.environ.get('ANDROID_NDK_ROOT')
        if not android_ndk_root:
            android_sdk_root = self._get_android_sdk_root()
            possible_ndk_paths = glob.glob(os.path.join(android_sdk_root, 'ndk', '*'))
            if not possible_ndk_paths:
                raise mesonlib.MesonException(f'No NDK installations found in ANDROID_SDK_ROOT "{android_sdk_root}".')
            # Pick the latest version based on directory name sorting
            android_ndk_root = sorted(possible_ndk_paths)[-1]
        if not os.path.isdir(android_ndk_root):
            raise mesonlib.MesonException(f'ANDROID_NDK_ROOT "{android_ndk_root}" is not a valid directory.')
        return android_ndk_root

    def _get_android_sdk_root(self) -> str:
        """
        Get the Android SDK root directory from environment variables.

        Raises an exception if the SDK root is not set or invalid.
        """
        android_sdk_root = (
            os.environ.get('ANDROID_HOME') or
            os.environ.get('ANDROID_SDK_ROOT') or
            os.environ.get('ANDROID_SDK_HOME')
        )
        if not android_sdk_root:
            raise mesonlib.MesonException('ANDROID_SDK_ROOT environment variable is not set.')
        if not os.path.isdir(android_sdk_root):
            raise mesonlib.MesonException(f'ANDROID_SDK_ROOT "{android_sdk_root}" is not a valid directory.')
        return android_sdk_root


def initialize(*args: Any, **kwargs: Any) -> JavaModule:
    return AndroidModule(*args, **kwargs)
