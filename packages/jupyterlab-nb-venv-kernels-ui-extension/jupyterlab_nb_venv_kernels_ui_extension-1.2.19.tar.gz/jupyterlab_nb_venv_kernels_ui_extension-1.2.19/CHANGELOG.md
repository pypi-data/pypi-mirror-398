# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 1.2.11

- Added 6 new tests for schema/plugin.json menu configuration validation
- Tests verify Kernel menu scan command and all context menu commands
- Total test count increased from 47 to 53

## 1.2.9

- **Package renamed** from `jupyterlab_launcher_navigate_to_kernel_extension` to `jupyterlab_nb_venv_kernels_ui_extension`
- Added comprehensive test suite with 47 unit tests
- Added `test` target to Makefile
- Added "Scan for Virtual Environments" to Kernel menu (invokes `nb_venv_kernels:scan`)
- Added package rename warning to README

## 1.2.6

- Auto-refresh kernel list after unregister and remove operations
- Calls `nb_venv_kernels:refresh` command for immediate UI update

## 1.2.5

- Fixed path conversion for relative paths from nb_venv_kernels
- Added fallback for absolute paths when serverRoot is empty
- Fixed confirmation dialog wording for remove environment

## 1.2.0

- Added "Remove Environment" context menu item
- Permanently deletes local `.venv` folders with confirmation dialog
- Unregisters kernel before removing directory
- Only available for local environments containing `.venv`

## 1.1.15

- Removed Node.js version restriction from Makefile
- Builds work with Node.js 25.x thanks to chalk resolution fix

## 1.1.8

- Fixed Node.js 24/25 compatibility with yarn resolution for chalk
- Forced `duplicate-package-checker-webpack-plugin/chalk` to version 4.1.2

## 1.1.4

- Added "Unregister Kernel" context menu item for nb_venv_kernels environments
- Uses nb_venv_kernels REST API directly
- Only appears for venv/uv environments, not conda

## 1.0.14

- Fixed conda local environments where `argv[0]` is relative `python` instead of absolute path - now checks `resource_dir` for `.venv` pattern first
- Added GitHub CI/CD workflows for build, test, release automation
- Updated CI to use Python 3.10 to match package requirements
- Added screenshot and reference to sister extension in README

## 1.0.13

- Fixed navigation for local conda environments stored in `.venv` subdirectories
- Extended `.venv` detection to validate segment boundaries

## 1.0.12

- Fixed terminal opening in wrong location (now uses relative path)
- Improved `.venv` detection for conda local environments

## 1.0.11

- Added dynamic kernel provider support (`nb_conda_kernels`, `nb_venv_kernels`)
- Project-aware path resolution - navigates to project root for `.venv` environments
- Pinned Node.js to `>=22,<25` to avoid chalk incompatibility
- Added `skipLibCheck` to fix TypeScript build issues

## 1.0.0

- Initial release
- Right-click context menu on kernel launcher cards
- "Show in File Browser" command
- "Open Terminal at Location" command
- Support for conda and virtualenv environments

<!-- <END NEW CHANGELOG ENTRY> -->
