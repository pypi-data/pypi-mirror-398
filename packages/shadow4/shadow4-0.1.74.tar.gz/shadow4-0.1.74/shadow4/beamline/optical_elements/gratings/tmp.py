from shadow4.beamline.s4_beamline import S4Beamline

beamline = S4Beamline()

#
#
#
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

light_source = SourceGeometrical(name='SourceGeometrical', nrays=50000, seed=5676561)
light_source.set_spatial_type_gaussian(sigma_h=0.000279, sigma_v=0.000015)
light_source.set_depth_distribution_off()
light_source.set_angular_distribution_gaussian(sigdix=0.000021, sigdiz=0.000018)
light_source.set_energy_distribution_singleline(1000.000000, unit='eV')
light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=1)
beam = light_source.get_beam()

beamline.set_light_source(light_source)

# optical element number XX
from syned.beamline.shape import Rectangle

boundary_shape = Rectangle(x_left=-0.005, x_right=0.005, y_bottom=-0.075, y_top=0.075)

from shadow4.beamline.optical_elements.mirrors.s4_toroid_mirror import S4ToroidMirror

optical_element = S4ToroidMirror(name='Toroid Mirror', boundary_shape=boundary_shape,
                                 surface_calculation=1,
                                 min_radius=1.46591,  # min_radius = sagittal
                                 maj_radius=641.786,  # maj_radius = tangential
                                 f_torus=0,
                                 p_focus=28, q_focus=0, grazing_angle=0.0261799,
                                 f_reflec=0, f_refl=0, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                 coating_material='Si', coating_density=2.33, coating_roughness=0)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=28, q=0, angle_radial=1.544616388, angle_azimuthal=1.570796327,
                                 angle_radial_out=1.544616388)
movements = None
from shadow4.beamline.optical_elements.mirrors.s4_toroid_mirror import S4ToroidMirrorElement

beamline_element = S4ToroidMirrorElement(optical_element=optical_element, coordinates=coordinates, movements=movements,
                                         input_beam=beam)

beam, mirr = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# optical element number XX
boundary_shape = None

from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror

optical_element = S4PlaneMirror(name='Plane Mirror', boundary_shape=boundary_shape,
                                f_reflec=0, f_refl=0, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                coating_material='Si', coating_density=2.33, coating_roughness=0)

from syned.beamline.element_coordinates import ElementCoordinates

coordinates = ElementCoordinates(p=1.688671, q=0, angle_radial=1.543521194, angle_azimuthal=4.71238898,
                                 angle_radial_out=1.543521194)
movements = None
from shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirrorElement

beamline_element = S4PlaneMirrorElement(optical_element=optical_element, coordinates=coordinates, movements=movements,
                                        input_beam=beam)

beam, mirr = beamline_element.trace_beam()

beamline.append_beamline_element(beamline_element)

# optical element number XX
if 0:
    from syned.beamline.shape import Rectangle

    boundary_shape = Rectangle(x_left=-0.005, x_right=0.005, y_bottom=-0.2, y_top=0.2)
    from shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGrating

    optical_element = S4PlaneGrating(name='Plane Grating',
                                     boundary_shape=None, f_ruling=0, order=-1,
                                     ruling=800000.0, ruling_coeff_linear=0.0,
                                     ruling_coeff_quadratic=0.0, ruling_coeff_cubic=0.0,
                                     ruling_coeff_quartic=0.0,
                                     )
    ideal_grating = optical_element
    boundary_shape = None
    from shadow4.beamline.optical_elements.gratings.s4_numerical_mesh_grating import S4NumericalMeshGrating

    optical_element = S4NumericalMeshGrating(name='Sphere Grating',
                                             boundary_shape=None,
                                             xx=None, yy=None, zz=None, surface_data_file='/home/srio/Oasys/mirror1.hdf5',
                                             f_ruling=0, order=-1,
                                             ruling=800000.0, ruling_coeff_linear=0.0,
                                             ruling_coeff_quadratic=0.0, ruling_coeff_cubic=0.0,
                                             ruling_coeff_quartic=0.0,
                                             )
    numerical_mesh_grating = optical_element
    from syned.beamline.shape import Rectangle

    boundary_shape = Rectangle(x_left=-0.005, x_right=0.005, y_bottom=-0.2, y_top=0.2)

    from shadow4.beamline.optical_elements.gratings.s4_additional_numerical_mesh_grating import \
        S4AdditionalNumericalMeshGrating

    optical_element = S4AdditionalNumericalMeshGrating(name='ideal + error Grating', ideal_grating=ideal_grating,
                                                       numerical_mesh_grating=numerical_mesh_grating)

    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=0.3117932, q=1, angle_radial=1.561707176, angle_azimuthal=3.141592654,
                                     angle_radial_out=1.525335212)
    movements = None
    from shadow4.beamline.optical_elements.gratings.s4_additional_numerical_mesh_grating import \
        S4AdditionalNumericalMeshGratingElement

    beamline_element = S4AdditionalNumericalMeshGratingElement(optical_element=optical_element, coordinates=coordinates,
                                                               movements=movements, input_beam=beam)

    beam, mirr = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)
else:

    from syned.beamline.shape import Rectangle

    boundary_shape = Rectangle(x_left=-0.005, x_right=0.005, y_bottom=-0.2, y_top=0.2)
    from shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGrating

    optical_element = S4PlaneGrating(name='Plane Grating',
                                     boundary_shape=None, f_ruling=0, order=-1,
                                     ruling=800000.0, ruling_coeff_linear=0.0,
                                     ruling_coeff_quadratic=0.0, ruling_coeff_cubic=0.0,
                                     ruling_coeff_quartic=0.0,
                                     )
    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=0.3117932, q=1, angle_radial=1.561707176, angle_azimuthal=3.141592654,
                                     angle_radial_out=1.525335212)
    movements = None
    from shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGratingElement

    beamline_element = S4PlaneGratingElement(optical_element=optical_element, coordinates=coordinates,
                                             movements=movements, input_beam=beam)

    beam, footprint = beamline_element.trace_beam()

    beamline.append_beamline_element(beamline_element)

# test plot
if True:
    from srxraylib.plot.gol import plot_scatter

    # plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)',
    #              plot_histograms=0)

    x = beam.get_column(1, nolost=1)
    z = beam.get_column(3, nolost=1)
    xf = mirr.get_column(1, nolost=1)
    yf = mirr.get_column(2, nolost=1)
    xpf = mirr.get_column(4, nolost=1)
    ypf = mirr.get_column(5, nolost=1)
    print("star: ", x.min(), x.max(), x)
    print("star: ", z.min(), z.max(), z)
    print("footprint: ", xf.min(), xf.max(), xf)
    print("footprint: ", yf.min(), yf.max(), yf)
    print("footprint p: ", xpf.min(), xpf.max(), xpf)
    print("footprint p: ", ypf.min(), ypf.max(), ypf)
    # plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')


"""
>>>>>>>>>>>>>>>>>>>>> NumericalMesh -1 0
star:  -0.0014840828165936185 0.0014557798626787847 [-2.65652101e-04  1.25270391e-04 -2.86841725e-04 ... -6.77698794e-04
 -7.78567307e-04 -4.96531502e-05]
star:  -0.01025361830757682 0.01112891032743326 [ 0.00199698  0.00325749  0.00034133 ...  0.00327908  0.00236154
 -0.00415421]
footprint:  -0.001641717271586218 0.0016030667689687884 [-3.12687969e-04  1.52333090e-04 -3.21935862e-04 ... -7.73271347e-04
 -8.63899766e-04 -5.53244985e-05]
footprint:  -0.24488482297380315 0.22562606705536153 [-0.04394493 -0.07167617 -0.0075054  ... -0.07214977 -0.05196901
  0.091412  ]
footprint p:  -0.0001870018316655611 0.00019682077226969337 [ 4.50578494e-05 -2.52544288e-05  3.48329722e-05 ...  8.91472449e-05
  8.11210348e-05  6.24128743e-06]
footprint p:  0.9989667930726018 0.9989668398684161 [0.99896683 0.99896682 0.99896681 ... 0.99896681 0.99896683 0.99896682]



star:  -0.0014840828165927546 0.0014557798626786023 [-2.65652101e-04  1.25270391e-04 -2.86841725e-04 ... -6.77698794e-04
 -7.78567307e-04 -4.96531502e-05]
star:  -0.010253618332867004 0.011128910327012452 [ 0.00199698  0.00325749  0.00034133 ...  0.00327908  0.00236154
 -0.00415421]
footprint:  -0.0016561103803190095 0.0016920894109959757 [ 3.25416703e-04 -1.59000115e-04  3.32621803e-04 ...  7.96777290e-04
  8.86382581e-04  5.76509084e-05]
footprint:  -0.08161478532537303 0.0752004470180676 [-0.01465296 -0.02388319 -0.00248941 ... -0.02403801 -0.0173316
  0.03046761]
footprint p:  -0.000196820772269686 0.00018700183166555975 [-4.50578494e-05  2.52544288e-05 -3.48329722e-05 ... -8.91472449e-05
 -8.11210348e-05 -6.24128743e-06]
footprint p:  0.9996279937992607 0.9996281152560368 [0.99962807 0.99962804 0.99962803 ... 0.99962803 0.99962808 0.99962805]

"""