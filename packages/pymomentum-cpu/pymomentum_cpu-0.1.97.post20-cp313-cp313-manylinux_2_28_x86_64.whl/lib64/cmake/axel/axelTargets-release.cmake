#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "axel::axel" for configuration "Release"
set_property(TARGET axel::axel APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(axel::axel PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libaxel.a"
  )

list(APPEND _cmake_import_check_targets axel::axel )
list(APPEND _cmake_import_check_files_for_axel::axel "${_IMPORT_PREFIX}/lib64/libaxel.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
