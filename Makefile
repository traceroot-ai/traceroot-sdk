.PHONY: build upload clean

build:
	rm -rf dist traceroot.egg-info/
	python -m build

upload:
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf dist traceroot.egg-info/
