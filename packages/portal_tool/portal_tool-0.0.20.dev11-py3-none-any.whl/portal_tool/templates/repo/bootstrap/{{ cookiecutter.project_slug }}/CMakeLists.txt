cmake_minimum_required(VERSION 3.30)
project({{ cookiecutter.project_name }} LANGUAGES C CXX))

find_package(portal-engine CONFIG REQUIRED)

set(CMAKE_CXX_STANDARD 20)

file(GLOB_RECURSE SOURCES source/*.cpp)

portal_add_game({{ cookiecutter.project_slug }}
        SOURCES ${SOURCES}
)