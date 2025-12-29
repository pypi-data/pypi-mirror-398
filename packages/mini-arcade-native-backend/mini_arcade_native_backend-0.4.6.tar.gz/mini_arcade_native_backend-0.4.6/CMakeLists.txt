cmake_minimum_required(VERSION 3.16)
project(mini_arcade_native_backend LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Let vcpkg toolchain be used if user sets CMAKE_TOOLCHAIN_FILE env var.
# (scikit-build-core will pass env vars to CMake.)

find_package(pybind11 CONFIG REQUIRED)
find_package(SDL2 CONFIG REQUIRED)
find_package(SDL2_ttf CONFIG REQUIRED)

set(TARGET_NAME _native)

# C++ sources live under cpp/
pybind11_add_module(${TARGET_NAME}
    cpp/bindings.cpp
    cpp/engine.cpp
)

target_link_libraries(${TARGET_NAME} PRIVATE SDL2::SDL2 SDL2_ttf::SDL2_ttf)

# Install the compiled extension into the Python package directory
# so it ends up as mini_arcade_native_backend/_native.*.pyd
install(TARGETS ${TARGET_NAME}
        LIBRARY DESTINATION mini_arcade_native_backend
        RUNTIME DESTINATION mini_arcade_native_backend
        ARCHIVE DESTINATION mini_arcade_native_backend)
