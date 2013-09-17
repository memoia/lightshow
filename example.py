#!env/bin/python -i
import pyaudio
import numpy as np
import onsetdetection
from scipy import signal, fftpack, stats
from beautifulhue.api import Bridge
from lightshow.registration import register, discover


(ip, user) = register(discover())

print "hue ip: {}, username: {}".format(ip, user)


bridge = Bridge(device={'ip': ip}, user={'name': user})

resource = {'which': 'all', 'verbose': False}
print bridge.light.get(resource)


def get_sample(seconds=2, sample_rate=44100):
    pa = pyaudio.PyAudio()
    pa_params = {
        'channels': 1,
        'format': pyaudio.paInt16,
        'rate': sample_rate,
        'frames_per_buffer': 1024,
        'input': True,
    }
    stream = pa.open(**pa_params)

    data = stream.read(sample_rate * seconds)

    stream.stop_stream()
    stream.close()
    pa.terminate()

    return np.frombuffer(data, dtype=np.int16)


def prob_percentiles(buckets=3):
    minpct = (1.0 / (buckets + 1))
    return np.linspace(minpct, 1.0 - minpct, num=buckets)


def refresh_time(sample_seconds, onsets):
    return int(round(60.0 / (len(onsets) / sample_seconds)))


def freq_parts(sample, onsets, buckets=3):
    amp = np.take(sample, onsets)
    frq = np.take(fftpack.fft(sample), onsets)
    amS = stats.mstats.mquantiles(amp, prob=prob_percentiles(buckets))
    frS = stats.mstats.mquantiles(frq, prob=prob_percentiles(buckets))
    return (amS, frS.real, frS.imag)


def shift_positive(vals):
    return (vals + (np.abs(vals.min()) * 2)) if vals.min() < 0 else vals


def scale_uint(vals, size=255):
    vals = shift_positive(vals)
    return (vals / ((vals.max() - vals.min()) / size)) * (size / vals.max())


refresh_seconds = 1

while True:
    sample = get_sample(refresh_seconds)

    #sample = signal.resample(sample, 1024)
    #foo = np.take(fftpack.fft(sample), signal.argrelmax(sample)[0])

    onsets = onsetdetection.detect_onsets(sample)

    (foo, bar, baz) = freq_parts(sample, onsets)
    print scale_uint(foo), scale_uint(bar), scale_uint(baz, 65535)

    refresh_seconds = refresh_time(refresh_seconds, onsets)
    print "Refresh after %s" % refresh_seconds
