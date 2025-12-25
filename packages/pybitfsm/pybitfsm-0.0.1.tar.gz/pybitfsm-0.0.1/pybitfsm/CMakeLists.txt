find_package(Python COMPONENTS Interpreter REQUIRED)

file(GENERATE OUTPUT "$<CONFIG>.env"
     CONTENT "export PYBITFSM_LIBRARY_PATH=$<TARGET_FILE:bitfsmopt>\n")

function(add_python_test PACKAGE NAME)
  add_test(
    NAME "${PACKAGE}.${NAME}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
    COMMAND ${CMAKE_COMMAND} -E env
            "PYBITFSM_LIBRARY_PATH=$<TARGET_FILE:bitfsmopt>"
            --
            ${Python_EXECUTABLE} -m unittest "${PACKAGE}.${NAME}")
endfunction()

add_python_test(pybitfsm bits_test)
add_python_test(pybitfsm formatters_test)
add_python_test(pybitfsm optimizer_test)
add_python_test(pybitfsm types_test)

if(DEFINED SKBUILD_PROJECT_NAME)
  file(GENERATE OUTPUT "libname_$<CONFIG>.py"
       CONTENT "NAME = '$<PATH:GET_FILENAME,$<TARGET_FILE:bitfsmopt>>'\n")
  install(TARGETS bitfsmopt
          DESTINATION "${SKBUILD_PROJECT_NAME}"
          COMPONENT pybitfsm)
  install(FILES __init__.py
                bits.py
                c_api.py
                formatters.py
                optimizer.py
                types.py
          DESTINATION "${SKBUILD_PROJECT_NAME}"
          COMPONENT pybitfsm)
  install(FILES "${CMAKE_CURRENT_BINARY_DIR}/libname_$<CONFIG>.py"
          RENAME "libname.py"
          DESTINATION "${SKBUILD_PROJECT_NAME}"
          COMPONENT pybitfsm)
endif()
