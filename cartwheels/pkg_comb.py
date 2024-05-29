# Cartwheels  Copyright (C) 2024  Alwyn Aswin

from itertools import groupby
from typing import List, cast, Set

from cartwheels.pkg_nfo import PkgNfo


class PkgComb:
    """
    Package Combinatorials
    Recombine packages into different working sets
    """

    def __init__(self, requires: List[PkgNfo], roots: Set[str], use_latest_when_not_requires: bool = True):
        """
        The initialization for class `PackageComb`
        :param requires: The packages that are part of the requirement.
        :param roots: The known roots
        :param use_latest_when_not_requires: The `requires` are assumed to be the independent variables,
                                            limiting the degrees of freedom will help speed up processing for the more
                                            gnarly dependency trees
        """
        self._use_latest_when_not_requires = use_latest_when_not_requires
        self._roots = roots
        self._requires = requires
        self._root_choosables = [PkgNfo(pkg_name, "", [*{*versions}]) for pkg_name, versions in
                                 groupby(sorted(requires,
                                                key=lambda d: cast(PkgNfo, d).get_key()),
                                         key=lambda d: cast(PkgNfo, d).name)]
        print('')

    @property
    def compatibility_sets(self) -> List[Set[PkgNfo]]:
        """
        Get a list of all the compatibility sets that can be linked from the roots
        :return: The list of compatibility sets.
        """
        compatibility_sets: List[Set[PkgNfo]] = []
        self._get_combinations(self._root_choosables, set(), compatibility_sets)
        return compatibility_sets

    def _get_combinations(self, choosables: List[PkgNfo], choices_chosen: Set[PkgNfo],
                          compat_sets: List[Set[PkgNfo]]) -> bool:
        """
        List of choices already chosen
        :param choosables: The packages that are left unchosen.
        :param choices_chosen: The choices already chosen
        :return: True if path is valid, False if there's any dependency (or sub dependency) that conflicts with choices made.
        """
        # NOTE: Yes I could do this with more graph theory, but the code would have been longer.

        # Base case, we've got to the bottom of the recursion and chosen everything that could be chosen
        if not choosables:
            compat_sets.append(choices_chosen)  # Save the compatibility set.
            return True

        choice = choosables[0]
        choosables = choosables[1:]
        group_deps = {pkg_name: [*{*versions}] for pkg_name, versions in
                      groupby(sorted(choice.dependencies, key=lambda d: cast(PkgNfo, d).get_key()),
                              key=lambda d: cast(PkgNfo, d).name)}

        for pkg_name, versions in group_deps.items():
            has_compatible_version = False
            a_version_of_package_was_chosen = any(filter(lambda p: cast(PkgNfo, p).name == pkg_name, choices_chosen))
            for arbitrarily_chosen_choice in sorted(versions, key=lambda v: cast(PkgNfo, v).version)[
                                             -1 if self._use_latest_when_not_requires and pkg_name not in {
                                                 *map(lambda r: r.name, self._requires)} else 0:]:
                if a_version_of_package_was_chosen and arbitrarily_chosen_choice in choices_chosen:
                    # There's compatible arbitrarily_chosen_choice, but is already chosen
                    has_compatible_version = True
                    break
                elif not a_version_of_package_was_chosen:
                    # Setup recursion with other dependencies not chosen by the inner loop.
                    inner_deps = [PkgNfo(name=pkg_name, version='', dependencies=[*{*versions}]) for pkg_name, versions
                                  in
                                  groupby(sorted(arbitrarily_chosen_choice.dependencies,
                                                 key=lambda d: cast(PkgNfo, d).get_key()),
                                          key=lambda d: cast(PkgNfo, d).name)]

                    # If we still have choices to be made (ie. degrees of freedom)
                    has_compatible_subs = self._get_combinations([*inner_deps, *choosables],
                                                                 {arbitrarily_chosen_choice, *choices_chosen},
                                                                 compat_sets)
                    if has_compatible_subs:
                        has_compatible_version = True
                    else:
                        continue

            # If one of the many dependencies has no compatibility across all versions, this current choice cannot work
            if not has_compatible_version:
                return False

        return True
