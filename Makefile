all: release

build: clean
	# lint + unit tests + build egg (available in host ./dist) + test egg on python 2 and 3
	dmake test test-egg-py2 test-egg-py3

clean:
	rm -rf dist

publish-test: build
	# For testing, note that once one version is uploaded, you have to increment the version number or make a post release to re-upload
	# https://www.python.org/dev/peps/pep-0440/#post-releases
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish: build
	# More info here https://packaging.python.org/tutorials/packaging-projects/
	twine upload dist/*
