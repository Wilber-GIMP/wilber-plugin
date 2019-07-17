# coding: utf-8

from __future__ import print_function, unicode_literals, division

from setuptools import setup

from setuptools.command.install import install
import shutil, os



class PostInstallCommand(install):
    """Real install

    Puts the plug-in files and frozen dependencies in GIMP's writable plug-ins folder
    """
    def run(self):
        print("Copying Wilber Social plugin and dependencies to GIMP plug-ins folder")
        plugin_folder = self.wilber_find_gimp()
        plugin_folder = os.path.join(plugin_folder, "wilber")

        os.mkdir(plugin_folder)

        try:
            shutil.copytree("wilber", os.path.join(plugin_folder, "wilber"))
            shutil.copytree("gui", os.path.join(plugin_folder, "gui"))
            shutil.copy("wilber.py", os.path.join(plugin_folder, "wilber.py"))
        except OSError:
            print("""It was not possible to copy the plugin and its dependencied to the GIMP folder -
                most likely due to a previous install or install attempt.
                Please, do remove <gimp-plugins>/wilber folder before attempting to install again
                """
            )

        os.chmod(os.path.join(plugin_folder, "wilber.py"), 0o755)

        if not 'requests' in os.listdir(os.path.join("wilber", "libs")):
            print("""Could not find a version of 'requests' packaged with the Wilber Social folder,
                you are likely installing it from source or otherwise -
                just place manually a Python 2.7 compatible copy of Python requests and requests_cache (and their dependencies)
                in the folder %s/wilber/libs in order for Wilber Social to work
                """ % plugin_folder
            )

        install.run(self)

    def wilber_find_gimp(self):
        gimp_210_folder = os.path.expanduser("~/.config/GIMP/2.10")
        if not os.path.exists(gimp_210_folder):
            exit("No GIMP 2.10 configuration files found for the current user. Install and run GIMP, before installing Wilber Social")

        plugin_folder = os.path.join(gimp_210_folder, "plug-ins")
        if not os.path.exists(plugin_folder):
             os.mkdir(plugin_folder)
        return plugin_folder





setup(
    name = 'wilber__social',
    version = "0.9.0",
    license = "LGPLv3+",
    author = "João S. O. Bueno, Darpan Deva, Robson",
    author_email = "gwidion@gmail.com",
    description = "GIMP 2.10 plug-in to manage online assets, allowing publishing and fecthing itens from the cloud",
    keywords = "gimp brushes assets",
    py_modules = ['wilber_social'],
    url = 'https://github.com/wilber-GIMP/wilber-plugin',
    long_description = open('README.md').read(),
    cmdclass={
        'install': PostInstallCommand,
    },

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ]
)
