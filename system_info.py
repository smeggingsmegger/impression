#!/usr/bin/env python
import platform

def main():
    print '```'
    print 'Python:'
    print '=============================================================='
    print 'Version      :', platform.python_version()
    print 'Compiler     :', platform.python_compiler()
    print 'Build        :', platform.python_build()

    print 'System:'
    print '=============================================================='
    print 'uname:', platform.uname()
    print 'system   :', platform.system()
    print 'node     :', platform.node()
    print 'release  :', platform.release()
    print 'version  :', platform.version()
    print 'machine  :', platform.machine()
    print 'processor:', platform.processor()
    print '```'

if __name__ == '__main__':
    main()
