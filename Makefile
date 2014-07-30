VERSION=1.3-4
NAME=cpopen
FULL_NAME=${NAME}-${VERSION}
TAR_FILE=${FULL_NAME}.tar.gz

SOURCESDIR=$(shell rpm --eval "%{_sourcedir}")

SPECFILE=python-cpopen.spec

DIST=dist

TAR_DIST_LOCATION=${DIST}/${TAR_FILE}
TAR_RPM_LOCATION=${SOURCESDIR}/${TAR_FILE}

all: build

.PHONY: build rpm srpm ${TAR_DIST_LOCATION} check-local dist

build:
	python setup.py build

check-local: build
	cd tests && nosetests tests.py

dist: $(TAR_DIST_LOCATION)

$(TAR_DIST_LOCATION):
	mkdir -p dist
	python setup.py sdist

${TAR_RPM_LOCATION}: ${TAR_DIST_LOCATION}
	cp "$<" "$@"

srpm: ${SPECFILE} $(TAR_RPM_LOCATION)
	rpmbuild -bs python-cpopen.spec

rpm: ${SPECFILE} ${TAR_RPM_LOCATION}
	rpmbuild -ba python-cpopen.spec

clean:
	python setup.py clean
	rm -rf $(DIST)
	rm -rf build
