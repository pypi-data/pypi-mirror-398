from setuptools import setup, find_packages

# Read requirements.txt and remove any comments
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    requirements = [r.strip() for r in requirements if not r.startswith('#')]

setup(
    name='fudstop4',
    version='1.4.1',
    author='Chuck Dustin',
    author_email='chuckdustin12@gmail.com',
    description='Advanced market data API aggregator for analysis and real-time feeds.',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/your-username/fudstop2',  # Replace with the actual repository
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires='>=3.11',
    packages=find_packages(),
    install_requires=requirements,
    license="MIT",
)
