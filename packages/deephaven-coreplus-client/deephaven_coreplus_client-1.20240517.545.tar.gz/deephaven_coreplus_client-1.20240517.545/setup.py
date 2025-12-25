#
#  Copyright (c) 2016-2021 Deephaven Data Labs and Patent Pending
#
import pathlib
from setuptools import setup

import os, re

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

if "DH_FROM_BUILD_DIR" in os.environ and os.environ["DH_FROM_BUILD_DIR"]:
    gradle_properties = (HERE / "../../../../gradle.properties")
else:
    # These work from the source directory
    gradle_properties = (HERE / "../../../../../../gradle.properties")

props = dict()
for line in open(gradle_properties, "r").readlines():
    line = line.strip().split("#", 2)[0].strip()
    if line == "":
        continue
    kv = line.split("=")
    if kv[0] in ["dhcVersion", "versionSource"]:
        props[kv[0]] = kv[1]

if "versionSource" not in props:
    raise Exception("Could not determine versionSource from %s" % gradle_properties)
versionSource = props["versionSource"]

if os.environ["DH_FROM_BUILD_DIR"]:
    versionFile = (HERE / ("../../../../gradle/versions/%s" % versionSource))
else:
    # These work from the source directory
    versionFile = (HERE / ("../../../../../../gradle/versions/%s" % versionSource))

client_dir = "deephaven_enterprise/client"
proto_dir = "deephaven_enterprise/proto"

VERSION = versionFile.read_text().strip()

VERSION_BITS = VERSION.split('.')
if len(VERSION_BITS[2]) > 3:
    VERSION_BITS[2] = VERSION_BITS[2][0:12] + '+' + VERSION_BITS[2][12:]

VERSION = '.'.join(VERSION_BITS)

dhcVersion = os.environ["DHC_VERSION"] if "DHC_VERSION" in os.environ else None

if dhcVersion is None:
    dhcVersion = props['dhcVersion']
if dhcVersion is None:
    raise Exception("Could not determine dhcVersion from %s" % gradle_properties)

setup(
    name='deephaven-coreplus-client',
    version=VERSION,
    description='The Deephaven Enterprise Core+ Python Client',
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["deephaven_enterprise.client", "deephaven_enterprise.proto"],
    package_dir={"deephaven_enterprise.client" : client_dir, "deephaven_enterprise.proto" : proto_dir},
    url='https://deephaven.io/',
    license='Deephaven Enterprise License Agreement',
    author='Deephaven Data Labs',
    author_email='python@deephaven.io',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    install_requires=['pydeephaven==' + dhcVersion, 'pycryptodomex>=3.19.0', 'pycryptodome>=3.19.0', 'grpcio>=1.63.0', 'urllib3', 'requests']
)
