cmake_minimum_required(VERSION 3.20)
project(cent)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

## raylib
set(RAYLIB_VERSION 5.0)
find_package(raylib ${RAYLIB_VERSION} QUIET) # QUIET or REQUIRED

if (NOT raylib_FOUND) # If there's none, fetch and build raylib
  include(FetchContent)
  
  FetchContent_Declare(
    raylib
    URL https://github.com/raysan5/raylib/archive/refs/tags/${RAYLIB_VERSION}.tar.gz
  )

  FetchContent_GetProperties(raylib)
  
  if (NOT raylib_POPULATED) # Have we downloaded raylib yet?
    set(FETCHCONTENT_QUIET NO)
    FetchContent_Populate(raylib)
    set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE) # don't build the supplied examples
    add_subdirectory(${raylib_SOURCE_DIR} ${raylib_BINARY_DIR})
  endif()

endif()

###############################################################################

file(GLOB_RECURSE source
  ${PROJECT_SOURCE_DIR}/main.cpp
  ${PROJECT_SOURCE_DIR}/source/*.cpp)

  include_directories(${PROJECT_SOURCE_DIR}/source)
include_directories(${PROJECT_SOURCE_DIR}/source/library)
include_directories(${PROJECT_SOURCE_DIR}/source/object)
include_directories(${PROJECT_SOURCE_DIR}/source/scene)

add_executable(${PROJECT_NAME} ${source})
target_link_libraries(${PROJECT_NAME} raylib)

# Checks if OSX and links appropriate frameworks (only required on MacOS)
if (APPLE)
    target_link_libraries(${PROJECT_NAME} "-framework IOKit")
    target_link_libraries(${PROJECT_NAME} "-framework Cocoa")
    target_link_libraries(${PROJECT_NAME} "-framework OpenGL")
endif()

if (MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE )
else()
    target_compile_options(${PROJECT_NAME} PRIVATE -Wpedantic -O3)
endif()