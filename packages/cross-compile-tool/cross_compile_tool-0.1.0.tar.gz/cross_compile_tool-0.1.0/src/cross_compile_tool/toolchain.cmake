set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# 1. Compiler Configuration
# Assumes aarch64-linux-gnu-g++ is in the PATH
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

# 2. Sysroot Configuration
# Read from environment variable (set by build.py before invoking colcon)
# We DO NOT use CMAKE_SYSROOT because it causes CMake to strip prefixes from libraries,
# which breaks Ninja builds. Instead, we pass --sysroot flags manually to compiler/linker.
if(NOT DEFINED ENV{TARGET_SYSROOT})
    message(FATAL_ERROR "TARGET_SYSROOT environment variable must be set")
endif()
set(TARGET_SYSROOT $ENV{TARGET_SYSROOT})

# Pass sysroot to compiler/linker
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --sysroot=${TARGET_SYSROOT}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --sysroot=${TARGET_SYSROOT}")

# Add sysroot to linker flags
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --sysroot=${TARGET_SYSROOT}")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} --sysroot=${TARGET_SYSROOT}")
set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} --sysroot=${TARGET_SYSROOT}")

# Set find root path for CMake package/library discovery
set(CMAKE_FIND_ROOT_PATH ${TARGET_SYSROOT})

# 3. Search Behavior
# Never search for programs in the sysroot (we want to use host tools like cmake, python)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# Only search for libraries, headers, and packages in the sysroot
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# 4. Performance Tuning (Mold Linker & CCache)
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    set(CMAKE_C_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
    set(CMAKE_CXX_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
endif()

# find_program(MOLD_LINKER mold)
# if(MOLD_LINKER)
#     set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fuse-ld=mold")
#     set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -fuse-ld=mold")
#     set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} -fuse-ld=mold")
# endif()

# Python SOABI for cross-compilation (dynamic version detection)
# Read from environment variables (set by build.py before invoking colcon)
if(DEFINED ENV{PYTHON_VERSION} AND DEFINED ENV{PYTHON_VERSION_NODOT})
    set(PYTHON_VERSION $ENV{PYTHON_VERSION})
    set(PYTHON_VERSION_NODOT $ENV{PYTHON_VERSION_NODOT})

    # Construct SOABI dynamically: cpython-<version_nodot>-<arch>
    set(PYTHON_SOABI "cpython-${PYTHON_VERSION_NODOT}-aarch64-linux-gnu")
    set(Python3_SOABI "cpython-${PYTHON_VERSION_NODOT}-aarch64-linux-gnu" CACHE STRING "Python3 SOABI for ARM64" FORCE)
    set(CMAKE_SHARED_MODULE_SUFFIX_CXX ".cpython-${PYTHON_VERSION_NODOT}-aarch64-linux-gnu.so" CACHE STRING "" FORCE)
    set(NB_SUFFIX ".cpython-${PYTHON_VERSION_NODOT}-aarch64-linux-gnu.so" CACHE INTERNAL "" FORCE)

    message(STATUS "Cross-compilation Python: ${PYTHON_VERSION} (SOABI: ${PYTHON_SOABI})")
else()
    message(STATUS "Cross-compilation Python: Disabled (PYTHON_VERSION not set)")
endif()
