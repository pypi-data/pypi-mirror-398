import os
import subprocess
from typing import Optional

from . import Configuration
from ..builders import Builder


def configuration_to_cmake_target(configuration: Configuration):
    compiler = configuration.compiler
    if compiler.name in ('gcc', 'llvm'):
        return 'Unix Makefiles'
    elif compiler.name_is('vs'):
        if compiler.version == '2017':
            return 'Visual Studio 15 2017 Win64'
        if compiler.version == '2022':
            return 'Visual Studio 17 2022'
    raise Exception(f"cmake doesn't know how to handle compiler '{compiler}'")


def configuration_to_compiler_name(configuration: Configuration) -> str:
    compiler = configuration.compiler
    if compiler.name_is('gcc'):
        return 'GCC with Makefiles'
    elif compiler.name_is('llvm'):
        return 'LLVM with Makefiles'
    elif compiler.name_is('vs'):
        if compiler.version == '2017':
            return 'Visual Studio 2017'
        elif compiler.version == '2022':
            return 'Visual Studio 2022'
    raise Exception(f"cmake doesn't know how to handle compiler '{compiler}'")


def configuration_to_extra_arguments(configuration: Configuration) -> str:
    compiler = configuration.compiler
    if compiler.name_is('gcc'):
        return "-DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Debug"
    elif compiler.name_is('llvm'):
        return '-DCMAKE_C_COMPILER=clang-19 -DCMAKE_CXX_COMPILER=clang++-19 -DCMAKE_BUILD_TYPE=Debug'
    elif compiler.name_is('vs'):
        if compiler.version == '2022':
            return '-A x64'
    return ''


def configuration_to_toolchain(configuration: Configuration) -> Optional[str]:
    return None

def generate_build_from_configuration(configuration: Configuration, builder: Builder):
    generate_build(
        archName='x86 64-bit',
        builder=builder,
        cmakeTarget=configuration_to_cmake_target(configuration),
        compilerName=configuration_to_compiler_name(configuration),
        extraArgs=configuration_to_extra_arguments(configuration),
        noGraphics=False,
        outDir=configuration.output_directory,
        buildNameDir=configuration.build_directory,
        pathToSource=configuration.source_directory,
        platformName=configuration.platform.name.capitalize(),
        toolchain=configuration_to_toolchain(configuration),
        unityBuild=False,
    )


def generate_build(
        *,
        archName: str,
        builder: Builder,
        cmakeTarget: str,
        compilerName: str,
        extraArgs: Optional[str]=None,
        noGraphics: bool,
        outDir: str,
        buildNameDir: str,
        pathToSource: str,
        platformName: str,
        toolchain: Optional[str]=None,
        unityBuild: bool,
):
    # determine whether or not we need graphics.
    noGraphicsStr = "-DNO_SYSTEM_GRAPHICS=0"
    if noGraphics:
        noGraphicsStr = "-DNO_SYSTEM_GRAPHICS=1"
        #outDir += "_NO_GFX"

    # print information about the build system we're preparing to generate.
    print( "Generating build system..." )
    print( outDir )
    print( "Target platform:  {}".format( platformName ) )
    print( "Target processor: {}".format( archName ) )
    print( "Target compiler:  {}".format( compilerName ) )

    # set the current working directory to the output directory.
    fullOutDir = outDir

    # run CMake in the output folder.
    unityBuildStr = "-DUNITY_BUILD=0"
    if unityBuild:
        unityBuildStr = "-DUNITY_BUILD=1"

    # security option string.
    secureStr = "-DSECURE_BUILD=0"
    #if options.secure:
    #    secureStr = "-DSECURE_BUILD=1"

    if toolchain != None:
        cmakeExecStr = f'cmake -DBUILD_DIRECTORY={outDir} {pathToSource} -G"{cmakeTarget}" ' \
                       f'-T"{toolchain}" --no-warn-unused-cli -DBUILD_CONFIG_DIR="{buildNameDir}" ' \
                       f'{unityBuildStr} {noGraphicsStr} {secureStr}'
    else:
        cmakeExecStr = f'cmake -DBUILD_DIRECTORY={outDir} {pathToSource} -G"{cmakeTarget}" ' \
                       f'--no-warn-unused-cli -DBUILD_CONFIG_DIR="{buildNameDir}" '\
                       f'{unityBuildStr} {noGraphicsStr} {secureStr}'

    if extraArgs != None:
        cmakeExecStr = '{0} {1}'.format( cmakeExecStr, extraArgs )

    builder.build(fullOutDir, cmakeExecStr)

    print(f"cmakeExecStr=='{cmakeExecStr}'")
    #prevDir = os.getcwd()
    ## change to the output folder, making it if needed.
    #if not os.path.exists( fullOutDir ):
    #    os.makedirs( fullOutDir )
    #os.chdir( fullOutDir )
#
#    p = subprocess.Popen(cmakeExecStr, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
#    if p:
#        (output, err) = p.communicate()
#        print( output )
#
#    # restore the previous working directory.
#    os.chdir( prevDir )
