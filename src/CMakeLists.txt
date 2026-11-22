# Builds the native shim libraries that the add-ons' VIs call:
#   FRC_NetworkTablesLV  (wpilib add-on)  NetworkTables, MrcLib, and data log wrappers
#   FRC_REVLibLV         (REVlib add-on)  SPARK configuration parameter wrappers
#
# Configure with -DDEPS=build/deps/<platform>, filled by
# `python scripts/fetch_natives.py --build-deps <platform>`; scripts/build-shims.sh does both.
# The libraries install to <prefix>/<add-on>/1/resource/.
cmake_minimum_required(VERSION 3.20)
project(wpilib_labview_shims LANGUAGES C CXX)

set(DEPS "" CACHE PATH "Headers and link libraries from fetch_natives.py --build-deps")
if(NOT IS_DIRECTORY "${DEPS}/include" OR NOT IS_DIRECTORY "${DEPS}/lib")
  message(FATAL_ERROR "Set DEPS to build/deps/<platform> (see scripts/fetch_natives.py --build-deps)")
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(MSVC)
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
  # Same warnings NI's build turned off for these sources
  add_compile_options(/wd4005 /wd4244 /wd4267 /wd4985 /wd4996)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  add_compile_options(-Wno-psabi)
endif()

# A library from DEPS/lib, or empty if this platform doesn't have it
function(find_dep var name)
  find_library(${var} NAMES ${name} PATHS "${DEPS}/lib" NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
endfunction()

# A shared library exporting exactly the functions in <dir>/<name>.exports
function(lv_shim name dir addon)
  add_library(${name} SHARED ${ARGN})
  target_include_directories(${name} PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/cintools" "${DEPS}/include")

  file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/${dir}/${name}.exports" lines)
  list(FILTER lines EXCLUDE REGEX "^[ \t]*(\\[.*)?$")
  list(TRANSFORM lines STRIP)
  set(exports "${CMAKE_CURRENT_BINARY_DIR}/${name}.exports")
  if(WIN32)
    list(JOIN lines "\n  " body)
    file(WRITE "${exports}.def" "EXPORTS\n  ${body}\n")
    target_sources(${name} PRIVATE "${exports}.def" "${CMAKE_CURRENT_SOURCE_DIR}/common/lvapi_win.c")
  elseif(APPLE)
    list(TRANSFORM lines PREPEND "_")
    list(JOIN lines "\n" body)
    file(WRITE "${exports}.txt" "${body}\n")
    # LabVIEW's functions come from the process that loads the library
    target_link_options(${name} PRIVATE -undefined dynamic_lookup
                        "LINKER:-exported_symbols_list,${exports}.txt")
    set_target_properties(${name} PROPERTIES INSTALL_RPATH "@loader_path" BUILD_WITH_INSTALL_RPATH ON
                          INSTALL_NAME_DIR "@rpath")
  else()
    list(JOIN lines ";\n    " body)
    file(WRITE "${exports}.map" "{\n  global:\n    ${body};\n  local: *;\n};\n")
    target_link_options(${name} PRIVATE "LINKER:--version-script=${exports}.map")
    # Find the libraries next to this one in the add-on's resource folder
    set_target_properties(${name} PROPERTIES INSTALL_RPATH "$ORIGIN" BUILD_WITH_INSTALL_RPATH ON)
  endif()

  install(TARGETS ${name}
          RUNTIME DESTINATION "${addon}/1/resource"
          LIBRARY DESTINATION "${addon}/1/resource")
endfunction()

lv_shim(FRC_NetworkTablesLV FRC_NetworkTablesLV wpilib
        FRC_NetworkTablesLV/NT4Shim.c
        FRC_NetworkTablesLV/MRCShims.cpp)
find_dep(NTCOREFFI ntcoreffi)
find_dep(MRCLIB MrcLib)
if(NOT NTCOREFFI OR NOT MRCLIB)
  message(FATAL_ERROR "ntcoreffi or MrcLib is missing from ${DEPS}/lib")
endif()
target_link_libraries(FRC_NetworkTablesLV PRIVATE "${NTCOREFFI}" "${MRCLIB}")
if(WIN32)
  target_link_libraries(FRC_NetworkTablesLV PRIVATE ws2_32)
endif()

lv_shim(FRC_REVLibLV FRC_REVLibLV REVlib
        FRC_REVLibLV/REVCanSparkPropertyWrappers.cpp)
target_include_directories(FRC_REVLibLV PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/FRC_REVLibLV/include")
find_dep(REVLIBDRIVER REVLibDriver)
if(REVLIBDRIVER)
  target_link_libraries(FRC_REVLibLV PRIVATE "${REVLIBDRIVER}")
elseif(NOT (MSVC AND CMAKE_CXX_COMPILER_ARCHITECTURE_ID STREQUAL "ARM64"))
  # Only Windows arm64 builds without REV, whose libraries don't exist there; the source
  # compiles to stubs that return kNotImplemented
  message(FATAL_ERROR "REVLibDriver is missing from ${DEPS}/lib")
endif()
