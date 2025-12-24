print("")
print("Welcome in JBioSeqTools v.2.1.1 library")
print("")
print("Loading required packages...")


import os

import pkg_resources


def get_package_directory():
    return pkg_resources.resource_filename(__name__, "")


_libd = get_package_directory()


if "installation.dec" not in os.listdir(_libd):
    print(
        "The first run of the JBioSeqTools library requires additional requirements to be installed, so it may take some time..."
    )
    import subprocess

    from jbst.install import *

    jseq_install()


if "installation.dec" in os.listdir(_libd):
    print("")
    print("JBioSeqTools is ready to use")
    print("")
