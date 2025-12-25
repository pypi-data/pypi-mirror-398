from setuptools import setup, find_packages

setup(
    name="outfitai",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.61.0",
        "pillow",
        "pydantic-settings>=2.7.0",
        "click>=8.1.0",
        "asyncio>=3.4.0",
        "google-genai>=1.2.0",
        "pydantic>=2.10.0",
    ],
    entry_points={
        'console_scripts': [
            'outfitai=outfitai.__main__:main',
        ],
    },
    description="AI-powered clothing image classification tool.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "Source": "https://github.com/23tae/outfitai",
    },
    author="23tae",
    author_email="taehoonkim.dev@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
