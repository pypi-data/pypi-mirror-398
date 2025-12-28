from setuptools import find_packages, setup
from os import path as osp, system as runcmd
import nestpython as nsp


def parse(filename):
    return osp.join(osp.dirname(__file__), filename)

def read(filename):
    return open(parse(filename), 'r').read()


param = eval(read('param.i'))

version = param['version']
test = param['test']

nsp.files.nbuild('geomatica-npy', 'geomatica', erase_dir=True, transfer_other_files=True)

with open(parse('..\README.md'), 'r') as f, open(parse('README.md'), 'w') as fn:
    readme = f.read()
    fn.write(readme)

    setup(
        name='geometrica' if test else 'geomatica',
        packages=find_packages(include=['geomatica']),
        version=version,
        description='Geometric Algebra in Python',
        author='slycedf',
        install_requires=[],
        license='MIT',
        long_description=readme,
        long_description_content_type='text/markdown',
        url='https://github.com/svntythsnd/geomatica',
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3.11",
            "License :: OSI Approved :: MIT License",
            "Intended Audience :: Science/Research",
            "Intended Audience :: Education",
            "Topic :: Scientific/Engineering :: Mathematics",
            "Topic :: Software Development :: Libraries"
        ],
        python_requires=">=3.11",
        keywords="geometric algebra GA Clifford multivector mathematics physics bivector wedge",
    )

token = open(f'D:/slycefolder/ins/gm/{"tt" if test else "tr"}', 'r').read()

runcmd(
    f'pause & python -m twine upload --repository { {True: "testpypi", False: "pypi"}[test]} dist/*{version}* -u __token__ -p {token} --verbose')
