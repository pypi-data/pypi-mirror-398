from shadow4.tools.logger import set_verbose
set_verbose()

from shadow4.beamline.s4_beamline import S4Beamline

beamline = S4Beamline()

#
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

light_source = SourceGeometrical(name='SourceGeometrical', nrays=1000, seed=5676561)
light_source.set_spatial_type_point()
light_source.set_depth_distribution_off()
light_source.set_angular_distribution_uniform(hdiv1=-0.000000, hdiv2=0.000000, vdiv1=-0.350000, vdiv2=0.350000)
light_source.set_energy_distribution_singleline(5000.000000, unit='A')
light_source.set_polarization(polarization_degree=0.500000, phase_diff=0.000000, coherent_beam=1)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
boundary_shape = None

from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror

optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                f_reflec=1, f_refl=0, file_refl='/home/srio/Oasys/reflec_refractiveindexinfo.dat',
                                refraction_index=0.662252 + 0j,
                                coating_material='Si', coating_density=2.33, coating_roughness=0)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=1, q=0.1, angle_radial=1.047197551, angle_azimuthal=0, angle_radial_out=1.047197551)
movements = None
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement

beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates, movements=movements,
                                        input_beam=beam)

beam, footprint = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)



#
#
#



import numpy
from shadow4.tools.arrayofvectors import vector_dot
from srxraylib.plot.gol import plot_scatter, plot
from matplotlib import pylab as plt


#
# extract input data
#


x = footprint.get_columns([1,2,3])
v = footprint.get_columns([4,5,6])
beamline_elements_list = beamline.get_beamline_elements()

Is = footprint.get_column(24)
Ip = footprint.get_column(25)
phases = footprint.get_column(14)
phasep = footprint.get_column(15)
P3 = footprint.get_column(33)

#
#
#
normal = beamline_elements_list[-1].get_optical_element().get_optical_surface_instance().get_normal(x)
normal *= -1.0 # conoc surfaces return downwards normal
print(x.shape, v.shape, normal.shape)

#
# calculate angle between normal and output direction
#

# note vector_dot accepts array(npoints,3) and x, v and normal are array(3,npoints).

cos_angles = vector_dot(v.T, normal.T)
angles_deg = numpy.degrees(numpy.arccos(cos_angles))

#
#
# derived variables
#


P = numpy.abs((Ip - Is) / (Is + Ip))
deltadiff = phases - phasep
#
# make the plot
#


# plot(angles_deg, Is, angles_deg, Ip, legend=["s-pol","p-pol"],  xtitle="Incidence angle (to normal) [deg]", ytitle="Intensity", linestyle=["",""], marker=["+","+"])

#plot(angles_deg, P,  xtitle="Incidence angle (to normal) [deg]", ytitle="Polarization Degree", linestyle="", marker="+")

#plot(angles_deg, numpy.degrees(deltadiff), [0,90], [90, 90], xtitle="Incidence angle (to normal) [deg]", ytitle="Phase difference (s - p) [deg]", linestyle=["",None], marker=["+",None])

plot(angles_deg, P3,
xtitle="Incidence angle (to normal) [deg]", ytitle="Circular polarization degree (Stokes P3)", linestyle="", marker="+")
plt.grid()



