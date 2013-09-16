#!env/bin/python
from lightshow.registration import register, discover

(ip, user) = register(discover())

print "hue ip: {}, username: {}".format(ip, user)
