from setuptools import setup

setup(
    name='TibblingAI',
    version='1.1.0',
    author='Taha',
    author_email='taharazzaq091@gmail.com',
    description='TibblingAI Codebase',
    packages=['TibblingAI'],
    include_package_data=True,
    long_description_content_type='text/markdown',
    install_requires=[
        'numpy',
        'pynrrd',
        'opencv-python',
        'pandas',
        'patsy',
        'pillow',
        'plotly',
        'natsort',
        'matplotlib',
        'antspyx',
        # List any other dependencies your module requires
    ],
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
