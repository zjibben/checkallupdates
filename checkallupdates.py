#!/usr/bin/env python3

# checkallupdates
#
# Returns a nice formatted list of available Arch updates similar to the one provided by yaourt,
# but without the need for admin rights.
#
# TODO: * netup size doesn't work without updating the repos with pacman -Sy. how to get the
#         size of the new version?
#
# dependencies: python-texttable, pacman, yay, grep

import subprocess, texttable


def isNewVersion(update):
    """Return whether the update is for a new version
    by comparing the version numbers before the final '-'."""
    return update[2][:update[2].rfind('-')] != update[3][:update[3].rfind('-')]


def table(header, alignment, data):
    """Return a table generated from the given header and data."""
    t = texttable.Texttable(max_width=1000) # let the terminal wrap lines, if necessary
    t.set_deco(texttable.Texttable.HEADER)
    t.set_cols_align(alignment)
    t.set_cols_dtype(['t' for h in header])
    t.header(header)
    t.add_rows(data,header=False)
    return t.draw()


def packageRepositories(pkg):
    """Find the repositories associated with a list of packages."""
    # get all package info associated with every package
    pkg_info  = subprocess.Popen(["pacman", "-Si"] + pkg, stdout=subprocess.PIPE).stdout.read()
    pkg_Qinfo = subprocess.Popen(["pacman", "-Qi"] + pkg, stdout=subprocess.PIPE).stdout.read()

    # grep the package info for the "Repository" line
    # and remove the Repository and : from the subsequent list
    pkg_repo = subprocess.Popen(["grep", "Repository"], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE) \
                         .communicate(pkg_info)[0].decode().split()
    pkg_repo = [x for x in pkg_repo if x not in ["Repository", ":"]]
    return pkg_repo


def listOfUpdates(command, repo):
    repo_update_text = subprocess.Popen(command, stdout=subprocess.PIPE).stdout.read().decode()
    package_update = []
    for line in repo_update_text.splitlines():
        pkgname, pkgverold, _, pkgvernew = line.split()
        package_update.append([repo, pkgname, pkgverold, pkgvernew])
    return package_update


if __name__=="__main__":
    # Look for updates in the regular repos
    package_update = listOfUpdates(["checkupdates", "--nocolor"], None)

    # Figure out which repo every package belongs to. Do this for all the packages at once because
    # many calls to pacman ends up being much slower than one big call.
    pkg_repo = packageRepositories([update[1] for update in package_update])
    for i in range(len(package_update)):
        package_update[i][0] = pkg_repo[i]

    # Look for updates in the AUR
    package_update += listOfUpdates(["yay", "-Qmu"], "aur")

    # sort the list first by repo (core, extra, community, multilib, aur), then by package name
    sort_order = {"core": 0, "extra": 1, "community": 2, "multilib": 3, "aur": 4}
    package_update.sort(key=lambda x: sort_order[x[0]])

    # split the list into new version updates and new release updates
    new_version = []; new_release = []
    for update in package_update:
        new_version.append(update) if isNewVersion(update) else new_release.append(update)

    # print the data
    print("Software upgrade (new version)\n",
          table(["Repository", "Package", "Old Version", "New Version"],
                ["l", "l", "l", "l"],
                new_version))
    print()
    print("Package upgrade only (new release)\n",
          table(["Repository", "Package", "Old Version", "New Version"],
                ["l", "l", "l", "l"],
                new_release))
