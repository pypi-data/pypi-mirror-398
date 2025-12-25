#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "genten_lbfgsb_c" for configuration "RELEASE"
set_property(TARGET genten_lbfgsb_c APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten_lbfgsb_c PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libgenten_lbfgsb_c.so"
  IMPORTED_SONAME_RELEASE "libgenten_lbfgsb_c.so"
  )

list(APPEND _cmake_import_check_targets genten_lbfgsb_c )
list(APPEND _cmake_import_check_files_for_genten_lbfgsb_c "${_IMPORT_PREFIX}/lib64/libgenten_lbfgsb_c.so" )

# Import target "gentenlib" for configuration "RELEASE"
set_property(TARGET gentenlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gentenlib PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libgentenlib.so"
  IMPORTED_SONAME_RELEASE "libgentenlib.so"
  )

list(APPEND _cmake_import_check_targets gentenlib )
list(APPEND _cmake_import_check_files_for_gentenlib "${_IMPORT_PREFIX}/lib64/libgentenlib.so" )

# Import target "gt_higher_moments" for configuration "RELEASE"
set_property(TARGET gt_higher_moments APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gt_higher_moments PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libgt_higher_moments.so"
  IMPORTED_SONAME_RELEASE "libgt_higher_moments.so"
  )

list(APPEND _cmake_import_check_targets gt_higher_moments )
list(APPEND _cmake_import_check_files_for_gt_higher_moments "${_IMPORT_PREFIX}/lib64/libgt_higher_moments.so" )

# Import target "genten" for configuration "RELEASE"
set_property(TARGET genten APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/genten"
  )

list(APPEND _cmake_import_check_targets genten )
list(APPEND _cmake_import_check_files_for_genten "${_IMPORT_PREFIX}/bin/genten" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
