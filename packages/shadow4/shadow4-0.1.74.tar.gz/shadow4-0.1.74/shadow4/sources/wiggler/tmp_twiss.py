import numpy
sigma_delta = 0.001

e_h = 134e-12
b_h = 1.814
a_h = -2.018
g_h = (1 + a_h**2) / b_h
eta_h = 0.012

e_v = 5e-12
b_v = 2.569
a_v = 1.933
g_v = (1 + a_v**2) / b_v
eta_v = 0

# test gamma
gg_h = 2.797
gg_v = 1.844
print("g (check)", g_h, gg_h)


# center

xx = b_h * e_h + (eta_h * sigma_delta)**2
xpxp = g_h * e_h
xxp = -a_h * e_h

print("center xx xpxp xxp: ", xx, xpxp, xxp)
print("center e_h", e_h, numpy.sqrt(xx * xpxp - xxp**2))
print("center s_h, sp_h:",  numpy.sqrt(xx), numpy.sqrt(xpxp))


# #upstream h
# b_h = 0.491
# a_h = 0
# g_h = (1 + a_h**2) / b_h
# xx = b_h * e_h + (eta_h * sigma_delta)**2
# xpxp = g_h * e_h
# xxp = -a_h * e_h
# print("e_h", e_h, numpy.sqrt(xx * xpxp - xxp**2))
# print("s_h, sp_h:",  numpy.sqrt(xx), numpy.sqrt(xpxp))

