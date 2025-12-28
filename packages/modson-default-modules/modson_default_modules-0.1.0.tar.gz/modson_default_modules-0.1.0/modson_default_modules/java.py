import os
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from mesonbuild.build import CustomTarget, Target
from mesonbuild.modules import ModuleReturnValue, NewExtensionModule, ModuleInfo, ModuleState, noKwargs
from mesonbuild import mesonlib
from mesonbuild.interpreterbase.decorators import KwargInfo, typed_pos_args, typed_kwargs
from mesonbuild.interpreter.type_checking import NoneType
from mesonbuild.compilers import detect_compiler_for
from mesonbuild.mesonlib import MachineChoice
from mesonbuild.compilers import Compiler
from mesonbuild.interpreter import Interpreter


class JavaModule(NewExtensionModule):
    INFO = ModuleInfo('java_custom', Path(__file__).parent.joinpath("VERSION").read_text(), None, unstable=True)

    def __init__(self, interpreter: Interpreter):
        super().__init__()
        self.methods.update({
            'folder_sources': self.folder_sources,
            "compile": self.compile_class,
            "jar": self.generate_jar,
        })

    @typed_pos_args('java_ext.folder_sources', str)
    @noKwargs
    def folder_sources(self, state: ModuleState, args: Tuple[List[mesonlib.FileOrString]],
                       kwargs: Dict[str, Optional[str]]) -> List[mesonlib.FileOrString]:
        """
        Recursively collect all Java source files from a given folder.

        # TODO if a file is added or removed from the folder, the build system should detect it and re-run the build.
        That not the case currently. This will require implementing a file watcher or similar mechanism.
        (Is ninja capable of this kind of thing?)
        """
        current_abs = os.path.abspath(os.path.join(state.environment.get_source_dir(), state.subdir))
        folder_abs = os.path.join(current_abs, str(args[0]))
        sources: List[mesonlib.FileOrString] = [
            os.path.relpath(f, start=current_abs)
            for f in glob.glob(os.path.join(folder_abs, '**', '*.java'), recursive=True)
        ]
        return sources

    @typed_pos_args(
        'java_ext.compile',
        varargs=(str, mesonlib.File),
        min_varargs=2,
    )
    @typed_kwargs(
        'java_ext.compile',
        KwargInfo('source', (str, int, NoneType), default=None),
        KwargInfo('target', (str, int, NoneType), default=None),
        KwargInfo('bootclasspath', (str, NoneType), default=None),
    )
    def compile_class(self, state: ModuleState, args: Tuple[List[mesonlib.FileOrString]],
                      kwargs: Dict[str, Optional[str]]) -> ModuleReturnValue:
        """
        Compile Java source files into .class files

        Returns a CustomTarget representing the compiled classes.

        The output of the target is a single file that acts as a timestamp for the compilation.
        The actual .class files are located in a directory alongside this file.
        (e.g., if the output file is 'javac_myclasses', the compiled .class files will be in 'javac_myclasses_dir/')
        """
        source = cast('str | int | None', kwargs.get('source'))
        target = cast('str | int | None', kwargs.get('target'))
        bootclasspath = cast('str | None', kwargs.get('bootclasspath'))
        name = str(args[0][0])
        files = mesonlib.listify(args[0][1:])

        javac_target = self._javac_compile(
            state,
            name,
            files,
            source=source,
            target=target,
            bootclasspath=bootclasspath,
        )

        return ModuleReturnValue(javac_target, [javac_target])

    @typed_pos_args(
        'java_ext.jar',
        varargs=(str, mesonlib.File, Target),
        min_varargs=2,
    )
    @typed_kwargs(
        'java_ext.jar',
        KwargInfo('source', (str, int, NoneType), default=None),
        KwargInfo('target', (str, int, NoneType), default=None),
        KwargInfo('bootclasspath', (str, NoneType), default=None),
        KwargInfo('main_class', (str, NoneType), default=None),
        KwargInfo('manifest_file', (str, mesonlib.File, NoneType), default=None),
    )
    def generate_jar(self, state: ModuleState, args: Tuple[List[mesonlib.FileOrString]],
                     kwargs: Dict[str, Any]) -> ModuleReturnValue:
        """
        Compile Java source files and package them into a jar file.

        If java source files are provided, they will be compiled first.
        Otherwise, only the provided compiled targets will be packaged into a jar.
        """
        main_class = cast('str | None', kwargs.get('main_class'))
        manifest_file = cast('str | mesonlib.File | None', kwargs.get('manifest_file'))
        source = cast('str | int | None', kwargs.get('source'))
        target = cast('str | int | None', kwargs.get('target'))
        bootclasspath = cast('str | None', kwargs.get('bootclasspath'))
        name = str(args[0][0])
        files_args = mesonlib.listify(args[0][1:])
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
                bootclasspath=bootclasspath,
            )
            new_objects.append(javac_target)
            targets.append(javac_target)
        jar_targets = self._jar_package(
            state,
            name,
            targets,
            main_class=main_class,
            manifest_file=manifest_file,
        )
        new_objects.extend(jar_targets)
        return ModuleReturnValue(jar_targets[-1], new_objects)

    def _jar_package(self, state: ModuleState, name: str,
                     targets: List[CustomTarget],
                     main_class: Optional[str] = None,
                     manifest_file: Optional[mesonlib.FileOrString] = None) -> List[CustomTarget]:
        """
        Package compiled classes into a jar file

        # TODO add support for resources and assets
        """
        self._test_target_compatibility(targets)
        name = 'jar_' + name
        move_commands = self._jar_move_javac_to_temp(state, name, targets)
        jar_targets = self._jar_create_from_temp(
            state,
            name,
            [move_commands],
            main_class=main_class,
            manifest_file=manifest_file,
        )
        return [move_commands, jar_targets]

    def _javac_compile(self, state: ModuleState, name: str,
                       files: List[mesonlib.FileOrString],
                       source: Optional[str | int] = None,
                       target: Optional[str | int] = None,
                       bootclasspath: Optional[str] = None) -> CustomTarget:
        """
        Compile Java source files into .class files
        """
        name = 'javac_' + name
        javac = self.__get_java_compiler(state)
        command = mesonlib.listify([
            javac.exelist,
            '-d', '@OUTPUT@_dir',
            *(['-source', str(source)] if source is not None else []),
            *(['-target', str(target)] if target is not None else []),
            *(['-bootclasspath', bootclasspath] if bootclasspath is not None else []),
            '@INPUT@',
            '&&',
            'touch',
            '-m',
            '@OUTPUT@',
        ])
        return CustomTarget(
            name,
            state.subdir,
            state.subproject,
            state.environment,
            command,
            sources=files,
            outputs=[name],
            backend=state.backend,
            build_by_default=True,
        )

    def _test_target_compatibility(self, targets: List[CustomTarget]) -> None:
        """
        Ensure that all inputs to jar() are outputs of compile()

        Used to prevent users from passing arbitrary files to jar()

        # TODO modify this function to allow assets or resources files
        """
        for target in targets:
            if not target.name.startswith("javac_"):  # added by _javac_compile
                raise mesonlib.MesonException("All inputs to jar() must be outputs of compile()")
        if (len(targets) == 0):
            raise mesonlib.MesonException("Can't generate a jar() without inputs")

    def _jar_move_javac_to_temp(self, state: ModuleState, name: str, targets: List[CustomTarget | mesonlib.FileOrString],
                                subdir: str | None = None, target_is_dir: bool = True) -> CustomTarget:
        """
        Move all compiled classes to a temporary folder for jar creation

        if target_is_dir is True, it means that the input targets are directories
        containing compiled classes, else all targets are files

        add a subdir inside the temporary folder if needed
        """
        name = 'move_' + name
        command_move_files = mesonlib.listify([
            'mkdir',
            '-p',
            '@OUTPUT@_dir' + (f'/{subdir}' if subdir else ''),
            '&&',
            'cp',
            # force recursive copy for be sure that the file who already exist will be overwrite
            '-rf',
            # add a dot to copy content of the folder and not the folder itself (happens the second time, when a file is modified)
            '@INPUT@' + ('_dir' if target_is_dir else ''),
            '@OUTPUT@_dir' + (f'/{subdir}' if subdir else ''),
            '&&',
            # Workaround to update timestamp of the target file
            # Meson don't check subfile modification time, only target file modification time
            # so the move files target will output this file for being sure modification is propagated properly
            'touch',
            '-m',
            '@OUTPUT@',
        ])
        return CustomTarget(
            name,
            state.subdir,
            state.subproject,
            state.environment,
            command_move_files,
            sources=targets,
            outputs=[name],
            backend=state.backend,
            build_by_default=True,
        )

    def _jar_create_from_temp(self, state: ModuleState, name: str,
                              move_commands: List[CustomTarget],
                              main_class: Optional[str] = None,
                              manifest_file: Optional[mesonlib.FileOrString] = None) -> CustomTarget:
        """
        Create a jar file from previously moved compiled classes
        """
        jar_output = name + ".jar"

        command_modifiers: List[str] = ["c", "f"]
        command_parameters: List[str] = ["@OUTPUT@"]
        if manifest_file:
            command_modifiers.append("m")
            command_parameters.append(str(manifest_file))
        if main_class:
            command_modifiers.append("e")
            command_parameters.append(main_class)

        command = mesonlib.listify([
            'jar',
            "".join(command_modifiers),
            *command_parameters,
            '-C', "@INPUT@_dir",
            "."
        ])

        return CustomTarget(
            name,
            state.subdir,
            state.subproject,
            state.environment,
            command,
            sources=move_commands,
            outputs=[jar_output],
            backend=state.backend,
            build_by_default=True,
        )

    def __get_java_compiler(self, state: ModuleState) -> Compiler:
        """
        Get the Java compiler for the build machine.
        If not found, try to detect it.
        """
        if 'java' not in state.environment.coredata.compilers[MachineChoice.BUILD]:
            detect_compiler_for(state.environment, 'java', MachineChoice.BUILD, False, state.subproject)
        return state.environment.coredata.compilers[MachineChoice.BUILD]['java']


def initialize(*args: Any, **kwargs: Any) -> JavaModule:
    return JavaModule(*args, **kwargs)
