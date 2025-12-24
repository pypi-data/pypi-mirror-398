# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

cmake_minimum_required(VERSION 3.16.3)


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was momentum-config.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

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

include(CMakeFindDependencyMacro)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

find_dependency(axel CONFIG)
find_dependency(Ceres CONFIG)
find_dependency(CLI11 CONFIG)
find_dependency(Dispenso CONFIG)
find_dependency(drjit CONFIG)
find_dependency(Eigen3 3.4.0 CONFIG)
find_dependency(ezc3d CONFIG)
find_dependency(Microsoft.GSL CONFIG)
find_dependency(fmt CONFIG)
find_dependency(fx-gltf CONFIG)
find_dependency(indicators 2.3 CONFIG)
find_dependency(nlohmann_json CONFIG)
find_dependency(openfbx CONFIG)
find_dependency(re2 MODULE)
find_dependency(spdlog CONFIG)
find_dependency(urdfdom CONFIG)

if(OFF)
  find_dependency(Kokkos CONFIG) # For mdspan headers (vendored in Kokkos)
endif()

if(OFF)
  find_dependency(Tracy CONFIG)
endif()

list(REMOVE_AT CMAKE_MODULE_PATH -1)

include("${CMAKE_CURRENT_LIST_DIR}/momentumTargets.cmake")

check_required_components("momentum")
