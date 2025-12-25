from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='trinity-agent-monitoring',
    version='0.2.0.dev1',
    author='Team Trinity',
    author_email='support@giggso.com',
    description='A Python SDK for Trinity Agent Monitoring API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/roosterhr/gg-trinity-agent-monitoring-sdk',
    install_requires=["langfuse==3.2.1","mcp-use==1.3.7"],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
