from setuptools import setup, find_packages

setup(
    name='PersonaCipher',
    version='5.1.1',
    license = 'MIT',
    packages=find_packages(), # Automatically find all packages
    include_package_data=True, # This is crucial for including non-code files like assets/datasets
    install_requires=[
        # List your dependencies here
        'opencv-python',
	    'pillow',
        'numpy',
        'dlib',
        'requests',
        'beautifulsoup4',
        'pyfiglet',
        'colorama',
        'yt_dlp',
        'face-recognition-models',
        'face-recognition',
        'setuptools<81.0', # Pinned to avoid pkg_resources deprecation warning
    ],
    entry_points={
        'console_scripts': [
            'persona_cipher=persona_cipher.persona_cipher:main_menu',
            'create_dataset=persona_cipher.create_dataset:create_dataset',
            'mp4_downloader=persona_cipher.mp4_downloader:main',
        ],
    },
    author='cyb2rS2c',
    description='Your face recognizer in images & videos.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/cyb2rS2c/PersonaCipher',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
