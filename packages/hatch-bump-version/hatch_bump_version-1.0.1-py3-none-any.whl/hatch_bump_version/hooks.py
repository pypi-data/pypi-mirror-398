from hatchling.plugin import hookimpl
from hatch_bump_version.bump_version_build_hook import BumpVersionBuildHook

@hookimpl
def hatch_register_build_hook():
    return BumpVersionBuildHook
