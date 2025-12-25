#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "genten_lbfgsb_c" for configuration "RELEASE"
set_property(TARGET genten_lbfgsb_c APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten_lbfgsb_c PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libgenten_lbfgsb_c.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libgenten_lbfgsb_c.dylib"
  )

list(APPEND _cmake_import_check_targets genten_lbfgsb_c )
list(APPEND _cmake_import_check_files_for_genten_lbfgsb_c "${_IMPORT_PREFIX}/lib/libgenten_lbfgsb_c.dylib" )

# Import target "gentenlib" for configuration "RELEASE"
set_property(TARGET gentenlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gentenlib PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libgentenlib.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libgentenlib.dylib"
  )

list(APPEND _cmake_import_check_targets gentenlib )
list(APPEND _cmake_import_check_files_for_gentenlib "${_IMPORT_PREFIX}/lib/libgentenlib.dylib" )

# Import target "gt_higher_moments" for configuration "RELEASE"
set_property(TARGET gt_higher_moments APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gt_higher_moments PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libgt_higher_moments.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libgt_higher_moments.dylib"
  )

list(APPEND _cmake_import_check_targets gt_higher_moments )
list(APPEND _cmake_import_check_files_for_gt_higher_moments "${_IMPORT_PREFIX}/lib/libgt_higher_moments.dylib" )

# Import target "genten" for configuration "RELEASE"
set_property(TARGET genten APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/genten"
  )

list(APPEND _cmake_import_check_targets genten )
list(APPEND _cmake_import_check_files_for_genten "${_IMPORT_PREFIX}/bin/genten" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
