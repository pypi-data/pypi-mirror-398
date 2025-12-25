from setuptools import setup, find_packages
setup(
    name="fusionx",
    version="0.9.8",
    author="Suman Khan",
    author_email="suman.khan@weizmann.ac.il",
    description="Segmentation and counting nuclei of fused cells",
    long_description=open("README.md").read(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fusionx=FusionX.FusionX:main',
        ],
    },
    python_requires='>=3.10',
    install_requires=[
    'opencv-python==4.10.0.84',
    'numba==0.60.0',
    'numpy==1.26.4',
    'pandas==2.2.2',
    'pycocotools==2.0.8',
    'scipy==1.14.0',
    'tifffile==2024.8.10',
    'torch==2.6.0',
    'torchvision==0.21.0',
    'tqdm==4.66.5',
    'requests==2.32.5',
    'cellpose==3.0.11',
    'pyarrow==17.0.0'
    ]

)