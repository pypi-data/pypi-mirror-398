from setuptools import setup, find_packages
from setuptools.command.install import install
import sys


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # Display fun message after installation
        print("\n" + "="*60)
        print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║          🌟  Thank you for installing empathy! 🌟     ║
    ║                                                       ║
    ║     You just made the world a little bit better!     ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝

         ♥♥♥    ♥♥♥
       ♥♥   ♥♥♥♥   ♥♥
      ♥♥     ♥♥♥     ♥♥
      ♥♥             ♥♥
       ♥♥           ♥♥
         ♥♥       ♥♥
           ♥♥   ♥♥
             ♥♥♥
              ♥

    Remember: Every person you meet is fighting a battle
              you know nothing about. Be kind. Always.

    💙 Spreading empathy, one install at a time 💙
        """)
        print("="*60 + "\n")


setup(
    name="empathy",
    version="1.1",
    author="Eric",
    description="A package that spreads kindness and empathy",
    long_description=open("README.md").read() if sys.path[0] else "Spreading empathy, one install at a time",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
    cmdclass={
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'empathy=empathy.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
