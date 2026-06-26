"""Leviton API."""


def version_tuple(version):
    "Version tuple."
    version = version.split(";")[0]
    return tuple(map(int, (version.split("."))))
