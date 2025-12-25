---
sidebar_position: 1
---

# Developing

How to develop for npyodbc.

## Developing

npyodbc uses the [meson](https://mesonbuild.com/) build system in order to both
**overlay** existing files found in pyodbc (basically to overwrite them or create new
ones), as well as to **patch** files in pyodbc (to update them using diffs). The
meson documentation uses the word patch to mean an overlay, and the word diff to mean
a patch. This is for historical reasons that you can read more about
[here](https://mesonbuild.com/Wrap-dependency-system-manual.html#accepted-configuration-properties-for-wraps).

The [Summary](#summary) section below gives recipes for creating patches or diffs in
case the following sections are tl;dr.

### Patches (overlays)

From a development standpoint, if you want to completely rewrite a file in pyodbc, you
will want to include it in `subprojects/packagefiles/pyodbc`. If it is supposed to
overwrite a file in the `src` or `test` directory, then you need to make sure those
directories exist in the subproject directory, _e.g._
`subprojects/packagefiles/pyodbc/src/textenc.cpp` will completely rewrite the file in
pyodbc named `pyodbc/src/textenc.cpp`. As an example of overwriting a file, the file
in `subprojects/packagefiles/pyodbc/setup.py` is completely empty. When meson is used
to build the project, it will download pyodbc and use the setup.py file in the patch
(read overlay) directory and rewrite the setup.py file in the downloaded pyodbc source
code so it is also empty.

Overlays can also be used to add new files. meson needs subprojects to have their own
`meson.build` file in order for it to be used in the parent project npyodbc. There
exists `subprojects/packagefiles/pyodbc/meson.build` in the patch (read overlay)
directory that does not exist in the upstream pyodbc repo. When meson builds
npyodbc it now contains a `meson.build` file that is used in the parent project.

### Diffs (patches)

On the other hand, if you want to modify a file in order to keep most if not all of the
original functionality, then you can create a diff (read patch) file. The folder
`subprojects/packagefiles/patches` contains a `.clang-format` file that will not format
any files you copy there from pyodbc. Git will also ignore any `*.h`, `*.cpp` or
`*.toml` files that are in this folder. We do this so original files from pyodbc are
not uploaded to the npyodbc project, and instead only patch files are committed to
source control.

To create a diff (read patch) file, copy the original file from pyodbc to the patch
directory. Make your changes to the file and then run the `diff` command. As an example,
we will walk through how we modified the pyproject.toml file in pyodbc to use the
meson build system. This is assuming you have pyodbc already downloaded. If not,
then you can use meson to do it for you with the command `meson subprojects download`.

```bash showLineNumbers
cp subprojects/pyodbc/pyproject.toml subprojects/packagefiles/patches/pyproject.toml
```

Open the pyproject.toml file in your favorite editor, and replace the build system with
a meson build system.

```toml showLineNumbers
# Original
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

# Replace the above with
[build-system]
build-backend = "mesonpy"
requires = ["meson-python", "numpy <2"]
```

Save and quit your editor. Next we use the `diff` command to create a patch file.

```bash showLineNumbers
diff -u subprojects/pyodbc/pyproject.toml \
    subprojects/packagefiles/patches/pyproject.toml \
    > subprojects/packagefiles/patches/pyproject.patch
```

Next open the patch file in your editor. You will see something like this at the top of
the file.

```patch showLineNumbers
--- subprojects/pyodbc/pyproject.toml	2024-06-13 15:43:19.682449229 -0500
+++ subprojects/packagefiles/patches/pyproject.toml	2024-06-13 15:55:46.617433621 -0500
```

We need to completely remove the path and date from the line starting with `+++` as well
as removing the first path level from the line starting with `---`. We must remove
`subprojects/` from the first line due to how meson applies patches. The lines will
now look like below.

```patch showLineNumbers
--- pyodbc/pyproject.toml	2024-06-13 15:43:19.682449229 -0500
+++
```

meson does not automatically apply diff (read patch) files to the subproject. You must
include a comma separated list of files that patches are supposed to be applied to. This
is done in the `subprojects/pyodbc.wrap` file.

```toml showLineNumbers
[wrap-git]
directory = pyodbc
url = https://github.com/mkleehammer/pyodbc.git
revision = 5.1.0
depth = 1
patch_directory = pyodbc
diff_files = patches/textenc.patch, patches/pyproject.patch

[provide]
pyodbc = pyodbc_dep
```

As can be seen in the wrap file, **overlays** go in the **patch_directory** and
**patch** files go in the **diff_files** as a comma separated list.

### Summary

**Patches** (overlays)

1. Create a new file in `subprojects/packagefiles/pyodbc`. This will overwrite existing
   files in pyodbc or create new ones. If you name a file with the same hierarchy in
   pyodbc in this folder, then the file in pyodbc will be completely overwritten
   with what is in this file. 
1. Commit the new file, or same named (but modified) file to source control.

**Diffs** (patches)

1. Copy the original file from pyodbc to `subprojects/packagefiles/patches`.
1. Make your changes to this file. Do not disturb the original file in pyodbc.
1. Create a patch file using the original pyodbc file and your new modified one. Use
   the command
   `diff -u {pyodbc-original} {npyodbc-modified} > subprojects/packagefiles/patches/{pyodbc-original}.patch`
1. Modify the top lines in the patch file as outlined above.
1. Commit the patch file to source control.
