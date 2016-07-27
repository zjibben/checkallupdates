About
=====
Checkallupdates is a program analogous to Arch Linux's `checkupdates`; it just produces a list of available updates for your Arch system. However, unlike `checkupdates` it includes AUR packages, puts everything in nice tables, separates software upgrades from package upgrades similar to Yaourt, and is significantly slower. It depends on `python-texttable` and `cower`.

Why would I make this when `pacaur -Qu` provides almost the same information? To recreate the only thing I missed after switching to pacaur from yaourt due to its [many flaws](https://wiki.archlinux.org/index.php/AUR_helpers#Comparison_table): a list of available updates which distinguishes between software and package-only updates.

It may be possible to speed up execution by depending solely on the output of `pacaur -Qu` instead of the output of both `checkupdates` and `cower -u`. Some testing seems to indicate `pacaur -Qu` alone runs faster than `cower -u`.
