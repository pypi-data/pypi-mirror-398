#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "nlohmann_json_schema_validator::validator" for configuration "RELEASE"
set_property(TARGET nlohmann_json_schema_validator::validator APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(nlohmann_json_schema_validator::validator PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libnlohmann_json_schema_validator.2.3.0.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libnlohmann_json_schema_validator.2.dylib"
  )

list(APPEND _cmake_import_check_targets nlohmann_json_schema_validator::validator )
list(APPEND _cmake_import_check_files_for_nlohmann_json_schema_validator::validator "${_IMPORT_PREFIX}/lib/libnlohmann_json_schema_validator.2.3.0.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
