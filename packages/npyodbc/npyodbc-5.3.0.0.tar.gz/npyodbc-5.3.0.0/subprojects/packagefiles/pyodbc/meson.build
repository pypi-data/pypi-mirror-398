project(
  'pyodbc',
  'cpp',
  version : '5.3.0',
)

python = import('python').find_installation()
python_dep = python.dependency()

compiler = meson.get_compiler('cpp')

pyodbc_sources = [
  'src/cnxninfo.cpp',
  'src/connection.cpp',
  'src/cursor.cpp',
  'src/decimal.cpp',
  'src/errors.cpp',
  'src/getdata.cpp',
  'src/params.cpp',
  'src/pyodbcdbg.cpp',
  'src/pyodbcmodule.cpp',
  'src/row.cpp',
  'src/textenc.cpp',
]
pyodbc_inc = include_directories(
  'src',
  is_system: true
)

deps = []
cflags = []
lflags = []

if host_machine.system() == 'windows'
  # Copy additional windows cflags from setup.py
  cflags += [
    '/Wall',
    '/wd4514',
    '/wd4820',
    '/wd4668',
    '/wd4711',
    '/wd4100',
    '/wd4127',
    '/wd4191',
    '/d2FH4-',
    '/Zc:strictStrings-',
  ]

  lflags = ['/d2:-FH4-']
  deps += [
    compiler.find_library('odbc32', required: true),
    compiler.find_library('advapi32', required: true),
  ]
else # Unix

  # First try to detect odbc via meson
  odbc = compiler.find_library('odbc', required: false)
  if odbc.found()
    # If we can find odbc via meson, no other action is needed
    deps += [odbc]

  else
    # Otherwise, we try to use odbc_config
    odbc_config = find_program('odbc_config', required: false)
    if odbc_config.found()
      cflags += run_command([odbc_config, '--cflags'], check: true).stdout().strip().split()
      lflags += run_command([odbc_config, '--libs'], check: true).stdout().strip().split()
    else
      error('Cannot find either the odbc library or the odbc_config binary. Aborting.')
    endif
  endif
endif

odbc_dep = declare_dependency(
  dependencies: deps,
  compile_args: cflags,
  link_args: lflags,
)

pyodbc_dep = declare_dependency(
  sources: pyodbc_sources,
  dependencies: [
    python_dep,
  ] + deps,
  include_directories: [pyodbc_inc],
  compile_args: cflags,
  link_args: lflags,
)

meson.override_dependency('pyodbc', pyodbc_dep)
meson.override_dependency('odbc', odbc_dep)
