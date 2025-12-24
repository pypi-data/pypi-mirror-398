import os
import sys
from setuptools import find_packages, setup
from mypyc.build import mypycify

from typed_envs import description, description_addon

if sys.implementation.name == "cpython":

    MYPYC_DEBUG_LEVEL = os.environ.get("MYPYC_DEBUG_LEVEL", "0")

    paths_to_compile = [
        "typed_envs/__init__.py",
        # TODO: implement a proxy wrapper instead of hacky subclasses "typed_envs/_env_var.py",
        "typed_envs/_typed.py",
        "typed_envs/ENVIRONMENT_VARIABLES.py",
        # TODO: fix mypyc IR error "typed_envs/factory.py",
        "typed_envs/registry.py",
        "typed_envs/typing.py",
        "--pretty",
        "--install-types",
        "--disable-error-code=assignment",
        "--disable-error-code=attr-defined",
    ]

    ext_modules = mypycify(paths=paths_to_compile, debug_level=MYPYC_DEBUG_LEVEL)
else:
    ext_modules = []

setup(
    name="typed_envs",
    url="https://github.com/BobTheBuidler/typed-envs",
    author="BobTheBuidler",
    author_email="bobthebuidlerdefi@gmail.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
    ],
    description=description,
    long_description=description + description_addon,
    python_requires=">=3.9,<4",
    packages=find_packages(),
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "local_scheme": "no-local-version",
        "version_scheme": "python-simplified-semver",
    },
    setup_requires=["setuptools_scm"],
    package_data={"typed_envs": ["py.typed"]},
    include_package_data=True,
    ext_modules=ext_modules,
)
