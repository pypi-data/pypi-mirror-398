"""Setup script for xnotify."""

from setuptools import setup, find_packages
from pathlib import Path
import traceback
import os
NAME = "xnotify"

def get_version():
    """
    Get the version of the ddf module.
    Version is taken from the __version__.py file if it exists.
    The content of __version__.py should be:
    version = "0.33"
    """
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if not version_file.is_file():
            version_file = Path(__file__).parent / NAME / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
    except Exception as e:
        if os.getenv('TRACEBACK') and os.getenv('TRACEBACK') in ['1', 'true', 'True']:
            print(traceback.format_exc())
        else:
            print(f"ERROR: {e}")

    return "3.0.0"

def update_metadata(version_number=None, author=None, email=None, license=None, url=None, description=None):
    """
    Update metadata in the __version__.py file.
    
    Args:
        version_number (str, optional): New version number
        author (str, optional): New author name
        email (str, optional): New email address
        license (str, optional): New license
        url (str, optional): New URL
        description (str, optional): New description
    """
    version_file = Path("xnotify/__version__.py")
    
    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")
    
    with open(version_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    updates = {
        '__version__': version_number,
        '__author__': author,
        '__email__': email,
        '__license__': license,
        '__url__': url,
        '__description__': description
    }
    
    for i, line in enumerate(lines):
        for key, value in updates.items():
            if value is not None and line.strip().startswith(key):
                # Determine quote character used in original
                if '"' in line:
                    quote_char = '"'
                elif "'" in line:
                    quote_char = "'"
                else:
                    continue
                
                # Update the value
                start_quote = line.find(quote_char)
                end_quote = line.rfind(quote_char)
                
                if start_quote != -1 and end_quote != -1 and start_quote != end_quote:
                    lines[i] = line[:start_quote+1] + value + line[end_quote:]
    
    with open(version_file, 'w', encoding='utf-8') as file:
        file.writelines(lines)
    
    # Print what was updated
    updated_fields = [k for k, v in updates.items() if v is not None]
    print(f"Updated {', '.join(updated_fields)} in {version_file}")

    return version_number

def update_version(version_number):
    """
    More robust version updater that preserves the original file formatting.
    
    Args:
        version_number (str): The new version number
    """
    version_file = Path("xnotify/__version__.py")
    
    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")
    
    with open(version_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    updated = False
    for i, line in enumerate(lines):
        # Look for the __version__ line
        if line.strip().startswith('__version__'):
            # Find where the version string starts and ends
            if '"' in line:
                quote_char = '"'
            elif "'" in line:
                quote_char = "'"
            else:
                continue  # Skip if no quotes found
            
            # Find the quoted version string
            start_quote = line.find(quote_char)
            end_quote = line.rfind(quote_char)
            
            if start_quote != -1 and end_quote != -1 and start_quote != end_quote:
                # Replace just the version number part
                lines[i] = line[:start_quote+1] + version_number + line[end_quote:]
                updated = True
                break
    
    if not updated:
        raise ValueError("Could not find __version__ line in the file")
    
    with open(version_file, 'w', encoding='utf-8') as file:
        file.writelines(lines)
    
    print(f"Updated __version__ to '{version_number}' in {version_file}")

VERSION = get_version()
print(f"VERSION: {VERSION}")
update_version(VERSION)
# update_metadata(VERSION)

version = {}
with open('xnotify/__version__.py') as f:
    exec(f.read(), version)

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='xnotify',
    version=version['__version__'],
    author=version['__author__'],
    author_email=version['__email__'],
    description=version['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=version['__url__'],
    license=version['__license__'],
    license_file="LICENSE",
    packages=find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: System :: Monitoring',
    ],
    python_requires='>=3.7',
    install_requires=[
        "progress_session>=0.30.2",
    ],
    extras_require={
        'full': [
            'pushbullet.py>=0.12.0',
            'pyyaml>=5.4.0',
            "progress_session>=0.30.2",
            "gntplib>=3.0.0",
        ],
        'ntfy': ['progress_session>=0.30.2'],
        'growl': ['gntplib>=3.0.0'],
        'yaml': ['pyyaml>=5.4.0'],
        'pushbullet': ['pushbullet.py>=0.12.0'],
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
            'isort>=5.10.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'xnotify=xnotify.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)