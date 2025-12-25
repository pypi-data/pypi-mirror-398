from shadow4.beamline.s4_beamline import S4Beamline

beamline = S4Beamline()

#
#
#
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

light_source = SourceGeometrical(name='SourceGeometrical', nrays=5000, seed=5676561)
light_source.set_spatial_type_point()
light_source.set_depth_distribution_off()
light_source.set_angular_distribution_uniform(hdiv1=-0.000000, hdiv2=0.000000, vdiv1=-0.000000, vdiv2=0.000000)
light_source.set_energy_distribution_uniform(value_min=12000.000000, value_max=13000.000000, unit='eV')
light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
boundary_shape = None

from shadow4.beamline.optical_elements.multilayers.s4_plane_multilayer import S4PlaneMultilayer

optical_element = S4PlaneMultilayer(name='Plane Multilayer', boundary_shape=boundary_shape,
                                    f_refl=5, file_refl='/home/srio/Oasys/mlayer.dat', structure='[B,W]x50+Si',
                                    period=25.000000, Gamma=0.500000)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=1, q=1, angle_radial=1.549852376, angle_azimuthal=0, angle_radial_out=1.549852376)
movements = None
from shadow4.beamline.optical_elements.multilayers.s4_plane_multilayer import S4PlaneMultilayerElement

beamline_element = S4PlaneMultilayerElement(optical_element=optical_element, coordinates=coordinates,
                                            movements=movements, input_beam=beam)

beam, footprint = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# test plot
if True:
    from srxraylib.plot.gol import plot_scatter

    plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)',
                 plot_histograms=0)
    # plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')