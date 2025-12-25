#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Kokkos::kokkoskernels" for configuration "RELEASE"
set_property(TARGET Kokkos::kokkoskernels APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Kokkos::kokkoskernels PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/libkokkoskernels.so"
  IMPORTED_SONAME_RELEASE "libkokkoskernels.so"
  )

list(APPEND _cmake_import_check_targets Kokkos::kokkoskernels )
list(APPEND _cmake_import_check_files_for_Kokkos::kokkoskernels "${_IMPORT_PREFIX}/lib64/libkokkoskernels.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
