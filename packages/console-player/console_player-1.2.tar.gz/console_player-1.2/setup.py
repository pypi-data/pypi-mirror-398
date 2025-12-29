#!/usr/bin/env python3
import setuptools
from consoleplay import version
import sys,shutil
shutil.rmtree("build",ignore_errors=True)
shutil.rmtree("console_player.egg-info",ignore_errors=True)
shutil.rmtree("console_player_noffmpeg.egg-info",ignore_errors=True)

# 处理自定义参数前先复制原始参数
original_argv = sys.argv.copy()
sys.argv = [arg for arg in sys.argv if not (arg.startswith("--have-ffmpeg") or arg.startswith("--others"))]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

name="console-player-noffmpeg"
package_data={}
options={
        'bdist_wheel': {
            'plat_name': 'any',  # 显式指定平台名称
        }
    }
platforms=["Windows"]

# 使用原始参数列表进行判断
packages=["cpvgen","consoleplay","consolepic"]
if "--have-ffmpeg" in original_argv:
    packages.append("console_player_tools")
    package_data={'console_player_tools': ['ffmpeg.exe']}
    name="console-player"
    options["bdist_wheel"]["plat_name"]="win_amd64"
if "--others" in original_argv:
    platforms=["Windows","Linux","macOS"]
    options["bdist_wheel"]["plat_name"]="any"
    name="console-player"

if "sdist" in original_argv:
    name="console-player"

setuptools.setup(
    name=name,
    version=version,
    author="SystemFileB",
    description="让终端可以播放视频！",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SystemFileB/console-player",
    packages=packages,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)", 
    ],
    install_requires=[
        "py7zr",
        "tqdm",
        "Pillow",
        "colorama",
        "pygame"
    ],
    platforms=platforms,
    options=options,
    entry_points={
    "console_scripts": [
        "cpvgen = cpvgen.__main__:run",
        "consoleplay = consoleplay.__main__:main",
        "consolepic = consolepic.__main__:main"
    ]
    },
    license="LGPLv3",
    include_package_data=True,
    package_data=package_data
)