#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "genten_lbfgsb_c" for configuration "Release"
set_property(TARGET genten_lbfgsb_c APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten_lbfgsb_c PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/genten_lbfgsb_c.lib"
  )

list(APPEND _cmake_import_check_targets genten_lbfgsb_c )
list(APPEND _cmake_import_check_files_for_genten_lbfgsb_c "${_IMPORT_PREFIX}/lib/genten_lbfgsb_c.lib" )

# Import target "gentenlib" for configuration "Release"
set_property(TARGET gentenlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gentenlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/gentenlib.lib"
  )

list(APPEND _cmake_import_check_targets gentenlib )
list(APPEND _cmake_import_check_files_for_gentenlib "${_IMPORT_PREFIX}/lib/gentenlib.lib" )

# Import target "gt_higher_moments" for configuration "Release"
set_property(TARGET gt_higher_moments APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gt_higher_moments PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/gt_higher_moments.lib"
  )

list(APPEND _cmake_import_check_targets gt_higher_moments )
list(APPEND _cmake_import_check_files_for_gt_higher_moments "${_IMPORT_PREFIX}/lib/gt_higher_moments.lib" )

# Import target "genten" for configuration "Release"
set_property(TARGET genten APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(genten PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/genten.exe"
  )

list(APPEND _cmake_import_check_targets genten )
list(APPEND _cmake_import_check_files_for_genten "${_IMPORT_PREFIX}/bin/genten.exe" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
