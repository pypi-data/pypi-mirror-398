###############################################################################
# Note:
# This file is named XxxConfig.cmake because once upon a time
# when it was named xxx-config.cmake, we found that CMake's exported
# targets script includes all "xxx*.cmake" files. This logic would
# cause this script to be included more than once, seeding instability
# that caused great harm to the kingdom.
###############################################################################

cmake_minimum_required(VERSION 3.0 FATAL_ERROR)


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was GentenConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################


if(NOT GENTEN_FOUND)

    set(GENTEN_VERSION "0.0.0")
    set(GENTEN_INSTALL_PREFIX "C:/Users/runneradmin/AppData/Local/Temp/tmpd_syrlcj/wheel/platlib/pygenten")

    set(GENTEN_KOKKOS_DIR  "")

    # advertise if mfem support is enabled
    set(GENTEN_LAPACK_FOUND TRUE)
    set(GENTEN_LAPACK_LIBS "D:/a/GenTen/GenTen/openblas/lib/libopenblas.lib")

    # pull in vars with details about configured paths
    get_filename_component(GENTEN_CMAKE_CONFIG_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)

    # setup dependent pkgs (i.e., kokkos)
    include(${GENTEN_CMAKE_CONFIG_DIR}/genten_setup_deps.cmake)

    # include the main exported targets
    include("${GENTEN_CMAKE_CONFIG_DIR}/genten.cmake")

    # finish setup
    include("${GENTEN_CMAKE_CONFIG_DIR}/genten_setup_targets.cmake")

    set(GENTEN_FOUND TRUE)

endif()
