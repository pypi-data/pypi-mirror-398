import os
from setuptools import setup, find_packages

path = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(path, 'README.md')) as f:
        long_description = f.read()
except Exception as e:
    long_description = 'customize okta cli'

# 查询cuda,torch版本，拼接链接，安装mmcv


def parse_requirements(fname='requirements.txt', with_version=True):
    import re
    import sys
    from os.path import exists
    require_fpath = fname

    def parse_line(line):
        """Parse information from a line in a requirements text file."""
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        else:
            info = {'line': line}
            if line.startswith('-e '):
                info['package'] = line.split('#egg=')[1]
            elif '@git+' in line:
                info['package'] = line
            else:
                # Remove versioning from the package
                pat = '(' + '|'.join(['>=', '==', '>']) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

                info['package'] = parts[0]
                if len(parts) > 1:
                    op, rest = parts[1:]
                    if ';' in rest:
                        # Handle platform specific dependencies
                        # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                        version, platform_deps = map(str.strip,
                                                     rest.split(';'))
                        info['platform_deps'] = platform_deps
                    else:
                        version = rest  # NOQA
                    info['version'] = (op, version)
            yield info
        print("info",info)

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    def gen_packages_items():
        if exists(require_fpath):
            for info in parse_require_file(require_fpath):
                parts = [info['package']]
                if with_version and 'version' in info:
                    parts.extend(info['version'])
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    return packages
# import sys
# print("___________________________________________________________________________")
# if "win" in sys.platform:
#     if "3.8" in  sys.version:
#         print(3.8)
#         os.system("pip install whl/pycocotools-2.0.4-cp38-cp38-win_amd64.whl")
#     elif "3.7" in  sys.version:
#         print(3.7)
#         os.system("pip install whl/pycocotools-2.0.4-cp37-cp37-win_amd64.whl")
#     elif "3.6" in  sys.version:
#         print(3.6)
#         os.system("pip install whl/pycocotools-2.0.4-cp36-cp36-win_amd64.whl")

setup(
    name='BaseML',
    version='0.2.0',
    description='BaseML provides numerous machine learning methods to quickly train and apply algorithms.',
    license='MIT License',
    author='XEduPro',
    author_email='easonqys@foxmail.com',
    url='https://github.com/XEduPro/OpenBaseLab-Edu',
    packages=find_packages(),
    include_package_data=True,
    install_requires= ['scikit-learn', 'pandas','numpy','seaborn', 'scikit-image','matplotlib','opencv-python>=4.1.2.30','yellowbrick'],
    python_requires='>=3.6',
    zip_safe=True,
    entry_points= {'console_scripts': ['BaseML = BaseML.version:hello',]}
)
