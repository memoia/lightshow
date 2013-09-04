ENV := $(CURDIR)/env
PYTHON := $(shell which python2.7)
PA := pa_stable_v19_20111121.tgz


$(ENV):
	virtualenv --python=$(PYTHON) $(ENV)
	$(ENV)/bin/pip install --upgrade setuptools pip

$(PA): | $(ENV)
	curl -L -O "http://www.portaudio.com/archives/$(PA)"
	tar -C $(ENV) -xvzf $(PA)
	cd $(ENV)/portaudio && CFLAGS=-mmacosx-version-min=10.4 ./configure --prefix=$(ENV) --disable-mac-universal && sed -e '49s/^\/\///' -i '' $(ENV)/portaudio/include/pa_mac_core.h && make && make install
	rm $(PA)

install: $(ENV) $(PA)
