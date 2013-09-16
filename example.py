#!env/bin/python -i
import pyaudio
import numpy as np
from beautifulhue.api import Bridge
from lightshow.registration import register, discover


(ip, user) = register(discover())

print "hue ip: {}, username: {}".format(ip, user)


bridge = Bridge(device={'ip': ip}, user={'name': user})

resource = {'which': 'all', 'verbose': False}
print bridge.light.get(resource)


pa = pyaudio.PyAudio()
pa_params = {
    'channels': 1,
    'format': pyaudio.paInt16,
    'rate': 44100,
    'frames_per_buffer': 1024,
    'input': True,
}

stream = pa.open(**pa_params)
data = stream.read(1024)

stream.stop_stream()
stream.close()
pa.terminate()

as_array = np.frombuffer(data, dtype=np.int16)
print as_array

#import onsetdetection
#print onsetdetection.detect_onsets(as_array)
