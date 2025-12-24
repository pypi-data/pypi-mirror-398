# -*- coding: utf-8; -*-
"""
Tasks for WuttaSync
"""

import os
import shutil

from invoke import task


@task
def release(c, skip_tests=False):
    """
    Release a new version of WuttaSync
    """
    if not skip_tests:
        c.run("pytest")

    if os.path.exists("dist"):
        shutil.rmtree("dist")

    c.run("python -m build --sdist")
    c.run("twine upload dist/*")
