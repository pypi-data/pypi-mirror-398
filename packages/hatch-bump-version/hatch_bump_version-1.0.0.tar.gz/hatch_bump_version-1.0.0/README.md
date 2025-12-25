# hatch-bump-version

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-bump-version.svg)](https://pypi.org/project/hatch-bump-version)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-bump-version.svg)](https://pypi.org/project/hatch-bump-version)


This package provides the bump version build hook for hatch. It builds on the git plumbing script to increment the version number in a project's git tag (download from https://github.com/krokoreit/git-bump-version).

It purpose is to check the project version number and to automatically increment it in case the current version has already been published. This avoids the annoying 'already published' message when trying to publish a project to PyPI.

Use the pre-index-publisher to track the version published and provide the information for this build hook.

Add "hatch-bump-version" to the build-system requirements in your project's pyproject.toml
```py
  [build-system]
  requires = [
    "hatchling",
    "hatch-bump-version",
    "hatch-vcs"
  ]

```
Also include a settings section for [tool.hatch.build.hooks.bump_version] (with 'bump_version' being the name of the plugin). No entries for the plugin are required, but the section must be included for the plugin to be activated.
```py
  [tool.hatch.build.hooks.bump_version]
  #nothing for this plugin 
```

The pluging will then run as a hook before the build process.


</br>




Enjoy

&emsp;krokoreit  
&emsp;&emsp;&emsp;<img src="https://github.com/krokoreit/hatch-bump-version/blob/main/assets/krokoreit-01.svg?raw=true" width="140"/>


## Installation
The plugin will be installed by hatch when creating the build environment. There no need to install it manually.


## Usage
When your project's pyproject.toml contains "hatch-bump-version" in the build-system requirements and a [tool.hatch.build.hooks.bump_version] section, the plugin is automatically started before the actual build process triggered by
```py
  hatch build
```
It will then display in the console either
```py
  [BumpVersionBuildHook] No version bump needed.
```
or
```py
  [BumpVersionBuildHook] Version already published → bumping version...
```
followed by the information given by the bump version script.


</br>

## License
MIT license  
Copyright &copy; 2025 by krokoreit
