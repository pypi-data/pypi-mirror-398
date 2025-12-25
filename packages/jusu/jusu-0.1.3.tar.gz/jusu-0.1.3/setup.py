from setuptools import setup, find_packages

setup(
	name="jusu",
	version="0.1.3",
	author="Francis Jusu",
	author_email="jusufrancis08@gmail.com",
	description="Python framework developed by Francis Jusu for building styled websites and web apps",
	long_description=open("README.md").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/Francis589-png/JUSU",  # Update if JUSU gets its own repo
	packages=find_packages(),
	python_requires=">=3.10",
	entry_points={
		"console_scripts": [
			"jusu=JUSU.cli:app",
		],
	},
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
)
