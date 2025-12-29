from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstall(install):
    def run(self):
        install.run(self)
        from pygen_modules.installer import generate_files

        generate_files()


setup(
    name="pygen-modules",
    version="1.0.0",
    packages=find_packages(),
    description="Generate CRUD and FormData boilerplate files",
    author="Manikandan",
    python_requires=">=3.8",
    cmdclass={"install": PostInstall},
)
