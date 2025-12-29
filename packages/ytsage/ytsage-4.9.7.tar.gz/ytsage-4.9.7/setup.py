from setuptools import setup, find_packages
from pathlib import Path

setup(
    name='ytsage', 
    version='4.9.7',
    author='oop7',
    author_email='oop7_support@proton.me', 
    description='Modern YouTube downloader with a clean PySide6 interface.', 
    long_description=Path('README.md').read_text(encoding='utf-8'),
    long_description_content_type='text/markdown',
    url='https://github.com/oop7/YTSage',
    packages=find_packages(),
    keywords=['youtube', 'downloader', 'video', 'audio', 'PySide6', 'yt-dlp', 'GUI'],
    install_requires=[
        'PySide6>=6.10.1',
        'requests>=2.32.5',
        'pillow>=12.0.0',
        'packaging>=25.0',
        'markdown>=3.10',
        'pyglet>=2.1.11',
        'loguru>=0.7.3',
        'setuptools>=80.9.0',
    ],
    include_package_data=True,
    package_data={
        'ytsage': [
            'assets/Icon/icon.png',  # Include the application icon
            'assets/sound/notification.mp3',  # Include the notification sound file
            'languages/*.json',  # Include all language translation files
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Desktop Environment',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
    ],
    python_requires='>=3.10,<3.15',
    entry_points={
        'console_scripts': [
            'ytsage=ytsage.main:main',
        ],
    },
    project_urls={
        'Homepage': 'https://github.com/oop7/YTSage',
        'Bug Tracker': 'https://github.com/oop7/YTSage/issues',
        'Reddit': 'https://www.reddit.com/r/NO-N_A_M_E/',
    },
)