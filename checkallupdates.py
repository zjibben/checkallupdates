#!/usr/bin/env python3

# checkallupdates
# Returns a nice formatted list of available Arch updates similar to the one provided by yaourt,
# but without the need for admin rights.
#
# TODO: * netup size doesn't work without updating the repos with pacman -Sy. how to get the
#         size of the new version?
#
# dependencies: python-texttable, pacman, cower, grep
#
# Zechariah J Jibben <threeofsix@gmail.com> 03/2015

import subprocess, texttable

# return whether the update is for a new version
# by comparing the version numbers before the final '-'
def isNewVersion(update):
    return update[2][:update[2].rfind('-')] != update[3][:update[3].rfind('-')]

# return a table generated from the given header and data
def table (header, alignment, data):
    t = texttable.Texttable(max_width=1000) # let the terminal wrap lines, if necessary
    t.set_deco(texttable.Texttable.HEADER)
    t.set_cols_align(alignment)
    t.set_cols_dtype(['t' for h in header])
    t.header(header)
    t.add_rows(data,header=False)
    return t.draw()

# return a list with certain elements removed
def removeOccurances (the_list, forbidden): return [x for x in the_list if x not in forbidden]

def sizeToMiB (size):
    if   (size[1]==  "B"): sizeMiB = float(size[0])/1024**2
    elif (size[1]=="KiB"): sizeMiB = float(size[0])/1024
    elif (size[1]=="MiB"): sizeMiB = float(size[0])
    elif (size[1]=="GiB"): sizeMiB = float(size[0])*1024
    else:                  print("ERROR ",size)
    return sizeMiB

# find the repositories associated with a list of packages
def packageRepositories (pkg):
    # get all package info associated with every package
    pkg_info  = subprocess.Popen(["pacman", "-Si"] + pkg, stdout=subprocess.PIPE).stdout.read()
    pkg_Qinfo = subprocess.Popen(["pacman", "-Qi"] + pkg, stdout=subprocess.PIPE).stdout.read()

    # grep the package info for the "Repository" line
    # and remove the Repository and : from the subsequent list
    pkg_repo = removeOccurances(
        subprocess.Popen(["grep", "Repository"], stdin=subprocess.PIPE, stdout=subprocess.PIPE) \
        .communicate(pkg_info)[0].decode() \
        .split(),
        set(["Repository",":"]))

    # get download size
    pkg_down_size = []
    for line in subprocess.Popen(["grep", "Download"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE) \
                          .communicate(pkg_info)[0].decode().splitlines():
        pkg_down_info = removeOccurances(line.split(), set(["Download", "Size", ":"]))
        pkg_down_size.append(sizeToMiB(pkg_down_info))

    # get net upgrade size
    pkg_netup_size = []
    for line in subprocess.Popen(["grep", "Installed Size"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE) \
                          .communicate(pkg_info)[0].decode().splitlines():
        pkg_inst_info = removeOccurances(line.split(), set(["Installed", "Size", ":"]))
        pkg_netup_size.append(sizeToMiB(pkg_inst_info))

    for i,line in enumerate(subprocess.Popen(["grep", "Installed Size"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE) \
                          .communicate(pkg_Qinfo)[0].decode().splitlines()):
        pkg_inst_info = removeOccurances(line.split(), set(["Installed", "Size", ":"]))
        pkg_netup_size[i] -= sizeToMiB(pkg_inst_info)
    
    return pkg_repo, pkg_netup_size, pkg_down_size

# main body
package_update = []

# look for updates in the regular repos
repo_update_text = subprocess.Popen("checkupdates", stdout=subprocess.PIPE).stdout.read().decode()
for line in repo_update_text.splitlines():
    pkgname, pkgverold, _, pkgvernew = line.split()
    package_update.append([None, pkgname, pkgverold, pkgvernew, None, None])

# figure out which repo every package belongs to
# do this for all the packages at once, rather than in the loop above,
# because many calls to pacman ends up being much slower than one big
# call that grabs the info for all packages being updated
pkg_repo, pkg_netup_size, pkg_down_size = \
    packageRepositories([update[1] for update in package_update])
for i in range(len(package_update)):
    package_update[i][0] = pkg_repo[i]
    package_update[i][4] = str(round(pkg_netup_size[i], 2))
    package_update[i][5] = str(round(pkg_down_size[i],  2))

# look for updates in the AUR
aur_update_text = subprocess.Popen(["cower", "-u"], stdout=subprocess.PIPE).stdout.read().decode()
for line in aur_update_text.splitlines():
    _, pkgname, pkgverold, _, pkgvernew = line.split()
    # I don't know how to assess upgrade/download size for AUR packages
    # leaving as None for now
    package_update.append(["aur", pkgname, pkgverold, pkgvernew, None, None])
    
# sort the list first by repo (core, extra, community, multilib, aur), then by package name
sort_order = {"core": 0, "extra": 1, "community": 2, "multilib": 3, "aur": 4}
package_update.sort(key=lambda x: sort_order[x[0]])

# split the list into new version updates and new release updates
new_version = []; new_release = []
for update in package_update:
    if isNewVersion(update): new_version.append(update)
    else:                    new_release.append(update)

# print the data
print("Software upgrade (new version)\n",
      table(["Repository", "Package", "Old Version", "New Version",
             "Net Change (MiB)", "Download Size (MiB)"],
            ["l", "l", "l", "l", "r", "r"],
            new_version))
print()
print("Package upgrade only (new release)\n",
      table(["Repository", "Package", "Old Version", "New Version",
             "Net Change (MiB)", "Download Size (MiB)"],
            ["l", "l", "l", "l", "r", "r"],
            new_release))

print()
print("Net upgrade size:    ",round(sum(pkg_netup_size), 2), "MiB")
print("Total download size: ",round(sum(pkg_down_size),  2), "MiB")
