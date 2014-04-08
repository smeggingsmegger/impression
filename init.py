#!/usr/bin/env python
import shlex
import subprocess

# from impression import app
from impression.mixin import safe_commit
from impression.models import *

def main():
    """@todo: Docstring for main.
    :returns: @todo

    """
    print("Initializing DB...")
    db.drop_all(bind=[None])
    db.create_all(bind=[None])
    print("Getting latest alembic revision since we are generating this DB")
    args = shlex.split("alembic history")
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, error = p.communicate()
    data = output.split('\n')
    latest_alembic = None
    for row in data:
        if "(head)" in row:
            cols = row.split(" ")
            latest_alembic = cols[2].strip()

    if latest_alembic:
        print("Stamping with latest Alembic revision: %s" % latest_alembic)
        args = shlex.split("alembic stamp %s" % latest_alembic)
        subprocess.Popen(args, stdout=subprocess.PIPE)

    safe_commit()

if __name__ == '__main__':
    main()
