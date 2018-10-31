all: release

release:
		rm -rf build dist *.egg-info
		python3 setup.py sdist bdist_wheel

test-publish: release
		# For testing, note that once one version is uploaded, you have to increment the version number or make a post release to re-upload
		# https://www.python.org/dev/peps/pep-0440/#post-releases
		twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish: release
		# More info here https://packaging.python.org/tutorials/packaging-projects/
		twine upload dist/*
