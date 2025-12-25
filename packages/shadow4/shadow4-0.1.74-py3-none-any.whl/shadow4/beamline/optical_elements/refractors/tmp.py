import numpy

x = numpy.linspace(0, 2*numpy.pi, 200)
den = (numpy.cos(x) + numpy.sin(x))
P = numpy.cos(x) / den

print(numpy.degrees(numpy.arccos(1/numpy.sqrt(2))))
from srxraylib.plot.gol import plot
plot(numpy.degrees(x), P,)
plot(numpy.degrees(x), den)