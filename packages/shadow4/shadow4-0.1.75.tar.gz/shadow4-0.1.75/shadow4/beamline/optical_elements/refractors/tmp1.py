from shadow4.beamline.s4_beamline import S4Beamline

import time
t0 = time.time()
beamline = S4Beamline()

#
#
#
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

light_source = SourceGeometrical(name='SourceGeometrical', nrays=20000, seed=5676561)
light_source.set_spatial_type_gaussian(sigma_h=4.82e-05, sigma_v=0.000010)
light_source.set_depth_distribution_off()
light_source.set_angular_distribution_gaussian(sigdix=0.000100, sigdiz=0.000004)
light_source.set_energy_distribution_singleline(35700.000000, unit='eV')
light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
boundary_shape = None
from syned.beamline.shape import Circle

boundary_shape = Circle(radius=0.0005, x_center=0, y_center=0)
from shadow4.beamline.optical_elements.refractors.s4_transfocator import S4Transfocator

optical_element = S4Transfocator(name='TF',
                                 n_lens=[16, 21],
                                 piling_thickness=[0.001, 0.001],  # syned stuff
                                 boundary_shape=boundary_shape,
                                 # syned stuff, replaces "diameter" in the shadow3 append_lens
                                 material=['Al', 'Al'],  # the material for ri_calculation_mode > 1
                                 density=[0.0, 0.0],  # the density for ri_calculation_mode > 1
                                 thickness=[4.9999999999999996e-05, 4.9999999999999996e-05],
                                 # syned stuff, lens thickness [m] (distance between the two interfaces at the center of the lenses)
                                 surface_shape=[2, 2],  # now: 0=plane, 1=sphere, 2=parabola, 3=conic coefficients
                                 # (in shadow3: 1=sphere 4=paraboloid, 5=plane)
                                 convex_to_the_beam=[0, 0],
                                 # for surface_shape: convexity of the first interface exposed to the beam 0=No, 1=Yes
                                 cylinder_angle=[0, 0],  # for surface_shape: 0=not cylindricaL, 1=meridional 2=sagittal
                                 ri_calculation_mode=[1, 1],  # source of refraction indices and absorption coefficients
                                 # 0=User, 1=prerefl file, 2=xraylib, 3=dabax
                                 prerefl_file=['/home/srio/Oasys/Be5_55a.dat', '/home/srio/Oasys/Al5_55a.dat'],
                                 # for ri_calculation_mode=0: file name (from prerefl) to get the refraction index.
                                 refraction_index=[1.0, 1.0],  # for ri_calculation_mode=1: n (real)
                                 attenuation_coefficient=[0.0, 0.0],  # for ri_calculation_mode=1: mu in cm^-1 (real)
                                 dabax=None,  # the pointer to dabax library
                                 radius=[0.00019999999999999998, 0.00019999999999999998],
                                 # for surface_shape=(1,2): lens radius [m] (for spherical, or radius at the tip for paraboloid)
                                 conic_coefficients1=[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
                                 # for surface_shape = 3: the conic coefficients of the single lens interface 1
                                 conic_coefficients2=[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
                                 # for surface_shape = 3: the conic coefficients of the single lens interface 2
                                 empty_space_after_last_interface=[0.0, 0.0],
                                 )

import numpy
from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=31.5, q=10, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
movements = None
from shadow4.beamline.optical_elements.refractors.s4_transfocator import S4TransfocatorElement

beamline_element = S4TransfocatorElement(optical_element=optical_element, coordinates=coordinates, movements=movements,
                                         input_beam=beam)

beam, mirr = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)
print(">>>> time: ", time.time()-t0)
# test plot
if True:
    from srxraylib.plot.gol import plot_scatter

    plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)',
                 plot_histograms=0)
    plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')