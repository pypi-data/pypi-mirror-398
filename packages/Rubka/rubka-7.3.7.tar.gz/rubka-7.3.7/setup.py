from setuptools import setup, find_packages

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ''

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='Rubka',
    version='7.3.7',
    description=(
    "Rubika: A Python library for interacting with the Rubika Bot API. "
    "This library provides an easy-to-use interface to send messages, polls, "
    "stickers, media files, manage groups and channels, handle inline keyboards, "
    "and implement advanced bot features like subscription management, "
    "user authentication, and message handling. "
    "Ideal for developers looking to automate and extend their Rubika bots with Python."
),

    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Mahdi Ahmadi',
    author_email='mahdiahmadi.1208@gmail.com',
    maintainer='Mahdi Ahmadi',
    maintainer_email='mahdiahmadi.1208@gmail.com',
    url='https://github.com/Mahdy-Ahmadi/Rubka',
    download_url='https://github.com/Mahdy-Ahmadi/rubka/archive/refs/tags/v6.6.4.zip',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
        'Natural Language :: Persian',
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests",
        "websocket-client",
        'pycryptodome',
        'aiohttp',
        'httpx',
        'tqdm',
        'mutagen',
        'markdownify',
        'filetype',
        'aiofiles',
        'deep-translator'
    ],
    entry_points={
        "console_scripts": [
            "rubka=rubka.__main__:main",
        ],
    },
    keywords="rubika bot api library chat messaging rubpy pyrubi rubigram rubika_bot rubika_api fast_rub",
    project_urls={
        "Bug Tracker": "https://t.me/Bprogrammer",
        "Documentation": "https://github.com/Mahdy-Ahmadi/rubka/blob/main/README.md",
        "Source Code": "https://github.com/Mahdy-Ahmadi/Rubka",
    },
    license="MIT",
    zip_safe=False
)