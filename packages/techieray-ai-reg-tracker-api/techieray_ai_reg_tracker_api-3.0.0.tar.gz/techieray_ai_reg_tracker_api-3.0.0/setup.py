from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

setup(
	name = "techieray_ai_reg_tracker_api",
	version = "3.0.0",
	packages = find_packages(),
	install_requires = [
		'requests',
	],
    long_description = description,
    long_description_content_type= "text/markdown"
)