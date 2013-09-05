ENV := $(CURDIR)/env
PYTHON := $(shell which python2.7)
PA_SRC := pa_stable_v19_20111121.tgz
PORTAUDIO := $(ENV)/portaudio
CFLAGS := "-I$(ENV)/include -I$(PORTAUDIO)/include -L$(ENV)/lib -L$(PORTAUDIO)/lib"


$(ENV):
	virtualenv --python=$(PYTHON) $(ENV)
	$(ENV)/bin/pip install --upgrade setuptools pip

$(PORTAUDIO): | $(ENV)
	curl -L -O "http://www.portaudio.com/archives/$(PA_SRC)"
	tar -C $(ENV) -xvzf $(PA_SRC)
	cd $(PORTAUDIO) && CFLAGS=-mmacosx-version-min=10.4 ./configure --prefix=$(ENV) --disable-mac-universal && sed -e '49s/^\/\///' -i '' $(PORTAUDIO)/include/pa_mac_core.h && make && make install
	rm $(PA_SRC)

install: | $(ENV) $(PORTAUDIO)
	CFLAGS=$(CFLAGS) PORTAUDIO_PATH=$(PORTAUDIO) $(ENV)/bin/pip install pyaudio
