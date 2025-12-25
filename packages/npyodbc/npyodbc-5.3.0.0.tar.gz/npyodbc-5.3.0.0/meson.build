project(
  'npyodbc',
  'cpp',
  version: run_command(['python', '-m', 'setuptools_scm'], check: true).stdout().strip(),
  default_options: ['cpp_std=c++17']
)

python = import('python').find_installation(pure: false)
python_dep = python.dependency()

# ODBC driver needs to be installed by the OS.
compiler = meson.get_compiler('cpp')

numpy_inc = include_directories(
  run_command(
    python,
    ['-c', 'import numpy; print(numpy.get_include())'],
    check : true,
  ).stdout().strip()
)
numpy_dep = declare_dependency(include_directories: numpy_inc)

# Patch pyodbc and declare it (and odbc itself) as dependencies
subproject('pyodbc')
pyodbc_dep = dependency('pyodbc')
odbc_dep = dependency('odbc')
icu_dep = dependency('icu-uc')

npyodbc_inc = include_directories('include')
npyodbc_sources = [
  'src/npcontainer.cpp',
  'src/npyodbcmodule.cpp'
]

add_project_arguments(
  [
    '-DPYODBC_VERSION=' + meson.project_version(),
  ],
  language: 'cpp'
)

deps = []
cflags = []
lflags = []


# Build the npyodbc module
python.extension_module(
  'npyodbc',
  npyodbc_sources,
  dependencies : [
    python_dep,
    numpy_dep,
    pyodbc_dep,
    icu_dep,
  ] + deps,
  include_directories : [npyodbc_inc],
  install : true,
  cpp_args : cflags,
  link_args : lflags,
)
