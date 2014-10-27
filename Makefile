VERSION=1.3
RELEASE=4
NAME=cpopen
FULL_NAME=${NAME}-${VERSION}
TAR_FILE=${FULL_NAME}.tar.gz

SPECFILE=python-cpopen.spec

DIST=dist

TAR_DIST_LOCATION=${DIST}/${TAR_FILE}

all: build

.PHONY: build rpm srpm ${TAR_DIST_LOCATION} check-local dist check

${SPECFILE}: ${SPECFILE}.in
	sed \
		-e s/@VERSION@/${VERSION}/g \
		-e s/@RELEASE@/${RELEASE}/g \
		$< > $@

build:
	CPOPEN_VERSION=${VERSION} python setup.py build

check: check-local

check-local: build
	cd tests && nosetests tests.py

dist: $(TAR_DIST_LOCATION)

$(TAR_DIST_LOCATION):
	mkdir -p dist
	CPOPEN_VERSION=${VERSION} python setup.py sdist

srpm: ${SPECFILE} $(TAR_DIST_LOCATION) dist
	rpmbuild --define "_sourcedir `pwd`/${DIST}" -bs python-cpopen.spec

rpm: ${SPECFILE} ${TAR_DIST_LOCATION} dist
	rpmbuild --define "_sourcedir `pwd`/${DIST}" -ba python-cpopen.spec

clean:
	CPOPEN_VERSION=${VERSION} python setup.py clean
	rm -rf $(DIST)
	rm -rf build
