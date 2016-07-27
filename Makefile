PYTHON=`which python`
PYTHON3=`which python3`

.PHONY: docs test

help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  deps        install dependencies using pip"
	@echo "  clean       remove unwanted files like .pyc's"
	@echo "  data        create database and sample data"
	@echo "  lint        check style with flake8"
	@echo "  test        run all your tests using py.test"

env:
	sudo easy_install pip && \
	pip install virtualenv && \
	virtualenv env && \
	. env/bin/activate && \
	make deps

deps:
	pip install -r requirements.txt

clean:
	python manage.py clean

clean:
	python manage.py upgrade

data:
	python manage.py dropdb
	python manage.py createdb
	python manage.py sample_data

lint:
	flake8 --exclude=env .

test:
	py.test tests

source:
	$(PYTHON) setup.py sdist

upload:
	$(PYTHON) setup.py register sdist upload

pypi:
	pandoc --from=markdown --to=rst --output=README.rst README.md
	make source
	make upload

delpyc:
	find . -name '*.pyc' -delete

install-libs:
	pip-2.7 install -U requirements.txt
	pip-3.2 install -U requirements.txt
