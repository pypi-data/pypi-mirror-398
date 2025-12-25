from shadow4.beamline.s4_beamline import S4Beamline

beamline = S4Beamline()

# electron beam
from shadow4.sources.s4_electron_beam import S4ElectronBeam

electron_beam = S4ElectronBeam(energy_in_GeV=1.9, energy_spread=0.001, current=0.4)
electron_beam.set_sigmas_all(sigma_x=3.9e-05, sigma_y=3.1e-05, sigma_xp=3.92e-05, sigma_yp=3.92e-05)

# magnetic structure
from shadow4.sources.undulator.s4_undulator_gaussian import S4UndulatorGaussian

source = S4UndulatorGaussian(
    period_length=0.02,  # syned Undulator parameter (length in m)
    number_of_periods=200.0,  # syned Undulator parameter
    photon_energy=15000.0,  # Photon energy (in eV)
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

light_source = S4UndulatorGaussianLightSource(name='GaussianUndulator', electron_beam=electron_beam,
                                              magnetic_structure=source, nrays=5000, seed=5676561)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
from syned.beamline.shape import Circle

boundary_shape = Circle(radius=0.000316, x_center=0, y_center=0)
from shadow4.beamline.optical_elements.refractors.s4_crl import S4CRL

optical_element = S4CRL(name='Compound Refractive Lens',
                        n_lens=20,
                        piling_thickness=0.0025,  # syned stuff
                        boundary_shape=boundary_shape,  # syned stuff, replaces "diameter" in the shadow3 append_lens
                        material="",  # syned stuff, not (yet) used
                        thickness=2.9999999999999997e-05,
                        # syned stuff, lens thickness [m] (distance between the two interfaces at the center of the lenses)
                        surface_shape=2,  # now: 0=plane, 1=sphere, 2=parabola, 3=conic coefficients
                        # (in shadow3: 1=sphere 4=paraboloid, 5=plane)
                        convex_to_the_beam=0,
                        # for surface_shape: convexity of the first interface exposed to the beam 0=No, 1=Yes
                        cylinder_angle=0,  # for surface_shape: 0=not cylindricaL, 1=meridional 2=sagittal
                        ri_calculation_mode=1,  # source of refraction indices and absorption coefficients
                        # 0=User, 1=prerefl file, 2=xraylib, 3=dabax
                        prerefl_file='/users/srio/Oasys/Be.dat',
                        # for ri_calculation_mode=0: file name (from prerefl) to get the refraction index.
                        refraction_index=1,  # for ri_calculation_mode=1: n (real)
                        attenuation_coefficient=0,  # for ri_calculation_mode=1: mu in cm^-1 (real)
                        radius=0.0001,
                        # for surface_shape=(1,2): lens radius [m] (for spherical, or radius at the tip for paraboloid)
                        conic_coefficients=None,
                        # for surface_shape = 3: the conic coefficients [todo: noy yet implemented]
                        )

from syned.beamline.element_coordinates import ElementCoordinates
import numpy

coordinates = ElementCoordinates(p=10, q=1, angle_radial=0, angle_azimuthal=0, angle_radial_out=numpy.pi)
from shadow4.beamline.optical_elements.refractors.s4_crl import S4CRLElement

beamline_element = S4CRLElement(optical_element=optical_element, coordinates=coordinates, input_beam=beam)

beam, mirr = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# test plot
if 0:
    from srxraylib.plot.gol import plot_scatter

    plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)',
                 plot_histograms=0)
    plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')

print(beamline.oeinfo())