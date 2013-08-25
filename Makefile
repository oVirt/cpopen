VERSION=1.2.3
TAR_FILE=cpopen-$(VERSION).tar.gz

DIST=cpopen.c \
     __init__.py \
     setup.py \
     python-cpopen.spec
     $(NULL)

all: build

.PHONY: build rpm srpm

build: $(DIST)
	python setup.py build

$(TAR_FILE): $(DIST)
	tar --transform 's,^,python-cpopen-${VERSION}/,S' -cvf $@ $(DIST)

srpm: python-cpopen.spec $(TAR_FILE)
	rpmbuild -ts $(TAR_FILE)

rpm: python-cpopen.spec $(TAR_FILE)
	rpmbuild -ta $(TAR_FILE)

clean:
	python setup.py clean
	rm -rf $(TAR_FILE)
