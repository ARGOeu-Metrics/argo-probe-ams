from distutils.core import setup
import glob
import sys

NAME = 'argo-probe-ams'
NAGIOSPLUGINS = '/usr/libexec/argo/probes/ams'


def get_ver():
    try:
        for line in open(NAME+'.spec'):
            if "Version:" in line:
                return line.split()[1]
    except IOError:
        print "Make sure that %s is in directory"  % (NAME+'.spec')
        sys.exit(1)


setup(name=NAME,
      version=get_ver(),
      license='ASL 2.0',
      author='SRCE, GRNET',
      author_email='dvrcic@srce.hr, themis@grnet.gr',
      description='Package include probes for ARGO AMS component',
      platforms='noarch',
      url='http://argoeu.github.io/',
      data_files=[(NAGIOSPLUGINS, glob.glob('src/*'))],
      packages=['argo_probe_ams'],
      package_dir={'argo_probe_ams': 'modules/'},
      )
