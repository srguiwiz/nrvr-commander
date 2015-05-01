# NrvrCommander - Repository README

NrvrCommander is a Python package for devops and QA automation around
virtual machines, VMware, CentOS 6.x, Ubuntu 14.04 LTS, also 12.04,
Windows 7, Scientific Linux 6.x,
enabling work with Firefox, Chrome, Internet Explorer, Selenium, and more.
Runs on Linux and Mac OS X.

If you got this from the source repository
(at [github](https://github.com/srguiwiz/nrvr-commander))
and just want to use it, run **sudo ./installlocally.py**.

For what is provided in the package, see **src/README.txt**.

Other than src/, files in dev/ are NOT going into the Python package.

Details for hosting on different operating systems are kept in **docs/**.

Good example uses (demonstrating utility) are

- **dev/examples/make-an-el-vm-001.py** (guest command line Enterprise Linux),

- **dev/examples/make-an-ub-vm-002.py** (guest command line Ubuntu), and

- the grand **dev/examples/qa/selenium/make-testing-vms-w-snaps-001.py**
(guest GUI Linux and Windows running Selenium, this example as implemented
uses VM snapshots and hence needs VMware Workstation or Fusion, but one
could use most of its techniques without snapshots in VMware Player).

Initially made with some brand Linux distributions, and
with VMware "personal desktop" machine virtualization,
this code is useful for automation with other operating systems,
physical machines, etc.

This project is about getting stuff done reproducibly.

There is an API reference
[online here](http://srguiwiz.github.io/nrvr-commander/docs/api/).

There is a
[dedicated category in a blog](http://leosbog.nrvr.com/category/nrvrcommander/).

Documentation is too conservative regarding VMware compatibility.
So far has been working OK with new versions VMware Workstation and Fusion.

New version operating systems, that's another cup of tea.

Can this project be integrated with something popular?
