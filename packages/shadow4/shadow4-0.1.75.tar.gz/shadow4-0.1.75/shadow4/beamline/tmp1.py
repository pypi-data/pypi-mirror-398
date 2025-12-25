from shadow4.beamline.s4_beamline import S4Beamline

beamline = S4Beamline()

# electron beam
from shadow4.sources.s4_electron_beam import S4ElectronBeam

electron_beam = S4ElectronBeam(energy_in_GeV=6, energy_spread=0.001, current=0.2)
electron_beam.set_sigmas_all(sigma_x=3.01836e-05, sigma_y=3.63641e-06, sigma_xp=4.36821e-06, sigma_yp=1.37498e-06)

# magnetic structure
from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian

source = S4UndulatorGaussian(
    period_length=0.042,  # syned Undulator parameter (length in m)
    number_of_periods=38.571,  # syned Undulator parameter
    photon_energy=5000,  # Photon energy (in eV)
    delta_e=0.0,  # Photon energy width (in eV)
    ng_e=100,  # Photon energy scan number of points
    flag_emittance=1,  # when sampling rays: Use emittance (0=No, 1=Yes)
    flag_energy_spread=0,  # when sampling rays: Use e- energy spread (0=No, 1=Yes)
    harmonic_number=1,  # harmonic number
    flag_autoset_flux_central_cone=0,  # value to set the flux peak
    flux_central_cone=10000000000.0,  # value to set the flux peak
)

# light source
from shadow4.sources.undulator.s4_undulator_gaussian_light_source import S4UndulatorGaussianLightSource

light_source = S4UndulatorGaussianLightSource(name='Undulator Gaussian', electron_beam=electron_beam,
                                              magnetic_structure=source, nrays=50000, seed=5676561)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
from syned.beamline.shape import Rectangle

boundary_shape = Rectangle(x_left=-0.001, x_right=0.001, y_bottom=-0.001, y_top=0.001)

from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen

optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                           i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                           i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=27.2, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement

beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

beam, footprint = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# optical element number XX
from syned.beamline.shape import Rectangle

boundary_shape = Rectangle(x_left=-0.0005, x_right=0.0005, y_bottom=-0.0005, y_top=0.0005)

from shadow4.beamline.optical_elements.absorbers.s4_screen import S4Screen

optical_element = S4Screen(name='Generic Beam Screen/Slit/Stopper/Attenuator', boundary_shape=boundary_shape,
                           i_abs=0,  # 0=No, 1=prerefl file_abs, 2=xraylib, 3=dabax
                           i_stop=0, thick=0, file_abs='<specify file name>', material='Au', density=19.3)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=23.8, q=0, angle_radial=0, angle_azimuthal=0, angle_radial_out=3.141592654)
from shadow4.beamline.optical_elements.absorbers.s4_screen import S4ScreenElement

beamline_element = S4ScreenElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

beam, footprint = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# optical element number XX
boundary_shape = None

from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirror

optical_element = S4SphereMirror(name='Generic Mirror', boundary_shape=boundary_shape,
                                 surface_calculation=0, is_cylinder=1, cylinder_direction=0,
                                 convexity=1, radius=1.000000, p_focus=51.500000, q_focus=0.150000,
                                 grazing_angle=0.006000,
                                 f_reflec=0, f_refl=0, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                 coating_material='Si', coating_density=2.33, coating_roughness=0)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=0.5, q=0.0575, angle_radial=1.564796327, angle_azimuthal=0,
                                 angle_radial_out=1.564796327)
movements = None
from shadow4.beamline.optical_elements.mirrors.s4_sphere_mirror import S4SphereMirrorElement

beamline_element = S4SphereMirrorElement(optical_element=optical_element, coordinates=coordinates, movements=movements,
                                         input_beam=beam)

beam, footprint = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# test plot
if 0:
    from srxraylib.plot.gol import plot_scatter

    plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)',
                 plot_histograms=0)
    plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')

print(beamline.distances_summary())
