cmake_minimum_required(VERSION 3.16)

project(sshp LANGUAGES C)

include(GNUInstallDirs)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Match the Makefile default: kqueue on Darwin/FreeBSD; epoll everywhere else.
set(_default_use_kqueue OFF)
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin" OR CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")
	set(_default_use_kqueue ON)
endif()

option(USE_KQUEUE "Use kqueue instead of epoll (if supported)" ${_default_use_kqueue})

add_executable(sshp
	sshp/src/sshp.c
	sshp/src/fdwatcher.c
)

target_include_directories(sshp PRIVATE sshp/src)
target_compile_definitions(sshp PRIVATE USE_KQUEUE=$<BOOL:${USE_KQUEUE}>)

target_compile_options(sshp PRIVATE
	$<$<AND:$<C_COMPILER_ID:AppleClang,Clang,GNU>,$<CONFIG:Release>>:-O2>
)

# ---- install ----
if(DEFINED SKBUILD)
	# scikit-build-core: put executables in the wheel's *.data/scripts/ directory.
	install(TARGETS sshp RUNTIME DESTINATION "${SKBUILD_SCRIPTS_DIR}")
else()
	# Standalone CMake install.
	install(TARGETS sshp RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
endif()
