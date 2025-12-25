#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ds::ds" for configuration "Release"
set_property(TARGET ds::ds APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ds::ds PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libds.a"
  )

list(APPEND _cmake_import_check_targets ds::ds )
list(APPEND _cmake_import_check_files_for_ds::ds "${_IMPORT_PREFIX}/lib/libds.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
