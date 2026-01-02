from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
    'Topic :: Software Development :: Embedded Systems',
]

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='lerpnet',
    version='1.0.2',
    description='Lightweight learnable interpolation using compact MLPs (edge & ESP32 ready)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    author='Somendra Seth',
    author_email='akhilresearch07@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords=[
        'machine-learning',
        'interpolation',
        'mlp',
        'edge-ai',
        'embedded',
        'esp32',
        'tinyml'
    ],
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    include_package_data=True,
)
