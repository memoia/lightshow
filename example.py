#!env/bin/python -i
import pyaudio
import numpy as np
import onsetdetection
from scipy import signal, fftpack, stats
from beautifulhue.api import Bridge
from lightshow.registration import register, discover


def find_bridge():
    (ip, user) = register(discover())
    bridge = Bridge(device={'ip': ip}, user={'name': user})
    return bridge


def find_lights(bridge):
    resource = {'which': 'all', 'verbose': False}
    return bridge.light.get(resource)


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


def scale_uint(vals, size=8):
    maxval = (2 ** size) - 1.0
    vals = shift_positive(vals)
    adjusted = ((vals * maxval) / vals.max()) - np.log10(vals.max())
    adjusted[adjusted<0] += adjusted.min()
    return np.rint(adjusted).astype(np.uint)


def light_params(sample, onsets, buckets=3):
    (foo, bar, baz) = freq_parts(sample, onsets, buckets)
    return np.column_stack((
        scale_uint(foo, 8),     # brightness
        scale_uint(bar, 16),    # hue
        scale_uint(baz, 8),     # saturation
    ))


bridge = find_bridge()
lights = find_lights(bridge)
light_ids = sorted([k.get('id') for k in lights.get('resource')])
buckets = len(light_ids)

refresh_seconds = 1

while True:
    sample = get_sample(refresh_seconds)

    #sample = signal.resample(sample, 1024)
    #foo = np.take(fftpack.fft(sample), signal.argrelmax(sample)[0])

    onsets = onsetdetection.detect_onsets(sample)

    params = light_params(sample, onsets, buckets)
    for (lightnum, values) in zip(light_ids, params.tolist()):
        resource = {
            'which': lightnum,
            'data': {
                'state': {
                    'on': True,
                    'bri': values[0],
                    'hue': values[1],
                    'sat': values[2],
                },
            },
        }
        bridge.light.update(resource)

    refresh_seconds = refresh_time(refresh_seconds, onsets)
    print "Setting\n%s" % params
    print "Refresh after %s" % refresh_seconds
