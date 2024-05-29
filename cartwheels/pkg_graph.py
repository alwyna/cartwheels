# Cartwheels  Copyright (C) 2024  Alwyn Aswin

import os
import dill
from datetime import datetime

from packaging.version import parse as parse_version, InvalidVersion
import json
from typing import List, Dict, Set, Any, Tuple, cast

import hashlib
from aiohttp import ClientSession

from cartwheels.pkg_nfo import PkgNfo

import re

PKG_PARSING_RE = re.compile(
    r"(?P<pkg>\w+)\s*\(?(?P<operator>[=\<\>]{1,2})\s*(?P<ver>\d+(\.\d+)?(\.\d+)?),?\s*((?P<operator2>[=\<\>]{1,2})(?P<upver>\d+(\.\d+)?(\.\d+)?))?\)?")

PKG_RELEASED = re.compile(r"^(\d+\.?)+$")


class PkgGraph:
    """
    A class to explore package versions and their dependency chains
    """

    def __init__(self, requirements: List[str], session: ClientSession, top: int = 10, skip_non_releases=True):
        """
        Initialize the graph pkg
        :param requirements: The packages being referenced, this should not have any version info, just the names.
        :param session: The aiohttp connection pool to use.
        :param top: Limits how many dependencies, to prevent graph complexity explosion.
        """
        self._top = top
        self._session = session
        self._requirements = requirements
        self._pkgs: Dict[str, PkgNfo] = {}
        self._pkg_ptr: Dict[str, Set[str]] = {}

        # We need this so we can use it as a pre-check when some module is co-dependent (aka. cyclical)
        self._explored_reqs: Set[str] = set()

    @property
    def pkgs(self) -> Dict[str, PkgNfo]:
        """
        Get the relationship of the packages and their versions
        :return:
        """
        return self._pkgs

    def __hash__(self):
        """
        Create a time bound hash for absolutely expiring cache
        :return: The hash of the requires and the current month
        """
        now = datetime.utcnow()
        return hashlib.md5((
                                   str(now.year) + ';' + str(now.month) + ';' + ";".join(
                               sorted(self._requirements))).encode('utf-8')).hexdigest()

    # use_cache -> not os.path.exists()
    async def resolve(self, use_cache: bool = True) -> 'PkgGraph':
        """
        Check if we have the hashed cache, if so and use_cache is set to True, and use it.
        :param use_cache: To use or not to use cache, that's the question.
        :return:
        """
        if not use_cache or not os.path.exists(f"{self.__hash__()}.pkl"):
            for requirement in self._requirements:
                await self._get_requirement(requirement)
            await self.dill(use_cache)
        else:
            with open(f"{self.__hash__()}.pkl", 'rb') as f:
                pkl = dill.load(f)
                self._requirements = pkl._requirements
                self._pkgs = pkl._pkgs
                self._pkg_ptr = pkl._pkg_ptr
                self._explored_reqs = pkl._explored_reqs
        return self

    async def dill(self, use_cache: bool = True) -> 'PkgGraph':
        """
        dill a cache if one did not already exist
        :return: Nothing
        """
        if not use_cache or not os.path.exists(f"{self.__hash__()}.pkl"):
            self._session = None
            ser = dill.dumps(self)
            with open(f"{self.__hash__()}.pkl", "wb+") as f:
                f.write(ser)
        return self

    async def _get_requirement(self, requirement) -> None:
        if requirement not in self._pkg_ptr and requirement not in self._explored_reqs:
            self._explored_reqs.add(requirement)
            pkg = await self.get_latest_nfo(requirement)
            if 'releases' in pkg:
                for key in [*sorted(filter(lambda k: PKG_RELEASED.match(k), pkg['releases'].keys()))][-self._top:]:
                    pkg_ver_nfo = await self.get_release_nfo(requirement, key)
                    parsed_sub_dependency: List[Dict[str, str]] = []
                    if 'requires_dist' in pkg_ver_nfo['info'] and pkg_ver_nfo['info']['requires_dist']:
                        for required in pkg_ver_nfo['info']['requires_dist']:
                            # We are not looking into the alpha/beta tag of the semver, as that's a little too much
                            if re_search := PKG_PARSING_RE.search(required):
                                parsed_sub_dependency.append(re_search.groupdict())
                    dependencies = []
                    for parsed_pkg in parsed_sub_dependency:
                        dep_key = PkgNfo.static_get_key(parsed_pkg["pkg"],
                                                        PkgGraph.standardize_semver(parsed_pkg["ver"]))
                        if dep_key not in self._pkgs:
                            await self._get_requirement(parsed_pkg["pkg"])
                        # If package is found in pypi, the pkg_ptr should be updated, if not it was skipped because package is no longer there (maybe removed, but still pointed to)
                        for pkg_ver_key in self._pkg_ptr[parsed_pkg["pkg"]] if parsed_pkg[
                                                                                   "pkg"] in self._pkg_ptr else []:
                            # Only include dependencies that's within range.
                            version = None
                            try:
                                version = parse_version(pkg_ver_key)
                            except InvalidVersion as ive:
                                print(f'Invalid version {pkg_ver_key}, skipping')
                            if version is not None and ((parse_version(parsed_pkg["ver"]) <= version and (
                                    version < parse_version(
                                parsed_pkg["upver"])) if "upver" in parsed_pkg and parsed_pkg[
                                "upver"] is not None else True) and dep_key in self._pkgs):
                                dependencies.append(self._pkgs[PkgNfo.static_get_key(parsed_pkg["pkg"], pkg_ver_key)])
                    pkgnfo = PkgNfo(name=requirement, version=key,
                                    dependencies=tuple(sorted(dependencies, key=lambda d: cast(PkgNfo, d).get_key())))

                    # Populate lookup index
                    if requirement not in self._pkg_ptr:
                        self._pkg_ptr[requirement] = {pkgnfo.version}
                    else:
                        self._pkg_ptr[requirement].add(pkgnfo.version)

                    # Populate global packages
                    if (pkg_ver_key := PkgNfo.static_get_key(pkgnfo.name, pkgnfo.version)) not in self._pkgs:
                        self._pkgs[pkg_ver_key] = pkgnfo
                        print(f'Added {pkgnfo.get_key()}')

    async def get_latest_nfo(self, requirement: str) -> Dict[str, Any]:
        async with self._session.get(f"https://pypi.python.org/pypi/{requirement}/json") as res:
            return json.loads(await res.text())

    async def get_release_nfo(self, requirement: str, key: str) -> Dict[str, Any]:
        async with self._session.get(f"https://pypi.python.org/pypi/{requirement}/{key}/json") as res:
            return json.loads(await res.text())

    @staticmethod
    def standardize_semver(semver: str):
        """
        Make standard broken semantic versions so semver module doesn't complain
        :param semver: The original probably non-compliant semantic version
        :return: The standardized sematic version
        """
        vers = semver.split('.')
        return ".".join(map(lambda i: vers[i] if i < len(vers) else "0", range(0, 3)))
