"""Leviton API."""


def version_tuple(version):
    "Version tuple."
    return tuple(map(int, (version.split("."))))
