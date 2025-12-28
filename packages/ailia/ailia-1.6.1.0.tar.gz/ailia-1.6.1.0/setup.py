import glob
import os
import platform
import sys

from setuptools import Extension, find_packages, setup

with open("INSTALL.md", encoding="utf-8") as f:
    long_description = f.read()

scripts = []
for f in glob.glob("ailia/*.py"):
    scripts.append(f)
for f in glob.glob("ailia/audio/*.py"):
    scripts.append(f)


def find_libraries():
    dll_names = []
    platforms = ["win32", "darwin", "linux_armv7l", "linux_aarch64", "linux_x86_64"]

    for platform in platforms:
        if platform == "win32":
            dll_platform = "windows/x64"
            dll_type = ".dll"
        elif platform == "darwin":
            dll_platform = "mac"
            dll_type = ".dylib"
        else:
            if platform == "linux_armv7l":
                dll_platform = "linux/armeabi-v7a"
            elif platform == "linux_aarch64":
                dll_platform = "linux/arm64-v8a"
            else:
                dll_platform = "linux/x64"
            dll_type = ".so"

        dll_path = "./ailia/" + dll_platform + "/"

        for f in glob.glob(dll_path + "*" + dll_type):
            f = f.replace("\\", "/")
            f = f.replace("./ailia/", "./")
            dll_names.append(f)

    dll_names.append("./LICENSE_AILIA_EN.pdf")
    dll_names.append("./LICENSE_AILIA_JA.pdf")
    dll_names.append("./oss/LICENSE_GLSLANG.txt")
    dll_names.append("./oss/LICENSE_INTELMKL.txt")
    dll_names.append("./oss/LICENSE_VULKAN_HEADERS.txt")

    return dll_names


if __name__ == "__main__":
    setup(
        name="ailia",
        scripts=scripts,
        version="1.6.1.0",
        description="ailia SDK",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="ailia Inc.",
        author_email="contact@ailia.ai",
        url="https://ailia.ai/",
        license="https://ailia.ai/license/en/",
        packages=find_packages(),
        package_data={"ailia": find_libraries()},
        include_package_data=True,
        python_requires=">3.6",
    )
