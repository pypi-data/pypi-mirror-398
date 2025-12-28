cmake_minimum_required(VERSION 3.15)
project(mi-amore LANGUAGES C)

# Python Extension
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

# Espresso-Quelle sammeln
file(GLOB ESPRESSO_SOURCES "espresso/*.c")
list(APPEND ESPRESSO_SOURCES "espresso/lib.c")

# Python-Extension bauen
Python3_add_library(_espresso MODULE 
    ${ESPRESSO_SOURCES}
)

target_include_directories(_espresso PRIVATE 
    "${Python3_INCLUDE_DIRS}"
    "espresso"
)

# Optimierung
target_compile_options(_espresso PRIVATE -Wno-register -Wno-implicit-function-declaration)

# Installation
install(TARGETS _espresso 
    LIBRARY DESTINATION mi-amore
)
