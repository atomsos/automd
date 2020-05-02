.PHONY: all reqs build install test

pes_parent_dir:=$(shell pwd)/$(lastword $(MAKEFILE_LIST))
pes_parent_dir:=$(shell dirname $(pes_parent_dir))

Project=$(shell basename $(pes_parent_dir))
PythonVersion := $(shell python -V 2>&1 | awk '{print $$2}' | cut -d \. -f 1-2 | sed "s/\.//g" | sed 's/^/py/')
CPythonVersion := $(shell python -V 2>&1 | awk '{print $$2}' | cut -d \. -f 1-2 | sed "s/\.//g" | sed 's/^/cp/' | sed 's/$$/m/')
BUILD_DIR := build/$(PythonVersion)


version:
	echo python: $(PythonVersion)
	echo cython: $(CPythonVersion)

all:
	make reqs
	make build_base
	make install
	make test

reqs:
	pipreqs --help >/dev/null 2>&1 || pip3 install pipreqs || pip3 install pipreqs --user
	bash -c 'unset PYTHONPATH; pipreqs --force $(Project)'
	mv $(Project)/requirements.txt .
	bash -c '[ "$(shell uname)" == "Darwin" ] && sed -i "" "s/==/>=/g" requirements.txt || sed -i "s/==/>=/g" requirements.txt'
	bash -c '[ "$(shell uname)" == "Darwin" ] && sed -i "" "s/numpy.*/numpy/g" requirements.txt || sed -i "s/numpy.*/numpy/g" requirements.txt'
	bash -c '[ "$(shell uname)" == "Darwin" ] && sed -i "" "s/psutil.*/psutil/g" requirements.txt || sed -i "s/psutil.*/psutil/g" requirements.txt'
	sort requirements.txt -o requirements.txt
	cat requirements.txt 

build:
	pip install cython twine
	rm -rf build/ sdist/ dist/ $(Project)-*/ $(Project).egg-info/
	mkdir -p dist/
	python Encrypt.py -j4 --build-dir $(BUILD_DIR)
	cd $(BUILD_DIR) && make build_base && make test_build && cp -r dist/*.whl ../../dist

build_base:
	rm -rf build/ sdist/ dist/ $(Project)-*/ $(Project).egg-info/
	python setup.py bdist_wheel --python-tag=$(PythonVersion) --py-limited-api=$(CPythonVersion)
	twine check dist/*

install:
	cd /tmp; pip uninstall -yy $(Project); cd -; python setup.py install || python setup.py install --user

test:
	bash -c "export PYTHONPATH="$(PYTHONPATH):$(pes_parent_dir)"; coverage run --source $(Project) ./tests/test.py" 
	echo `which $(Project)`
	# coverage run --source $(Project) `which $(Project)` -h
	# coverage run --source $(Project) `which $(Project)` LISTSUBCOMMAND
	# coverage run --source $(Project) `which $(Project)` LISTSUBCOMMAND | xargs -n 1 -I [] bash -c '(coverage run --source $(Project) `which $(Project)` [] -h >/dev/null 2>&1 || echo ERROR: [])'
	# coverage report -m
	coverage report -m > coverage.log
	cat coverage.log

test_build:
	bash -c "export AUTOMD_LOGLEVEL=debug; export PYTHONPATH="$(PYTHONPATH):$(pes_parent_dir)"; python ./tests/test.py"

test_env:
	bash -c ' \
	rm -rf venv; \
	virtualenv venv; \
	source venv/bin/activate; \
	which python; \
	python --version; \
	pip install -r requirements.txt; \
	make build; \
	make travisinstall; \
	make test'
	
upload:
	twine upload --repository-url https://pypi.senrea.net dist/*.whl

clean:
	rm -rf venv build *.egg-info dist
