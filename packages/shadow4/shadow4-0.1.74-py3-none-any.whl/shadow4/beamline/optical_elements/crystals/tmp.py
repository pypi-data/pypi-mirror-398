
def parabola_with(beam):
    # optical element number XX
    from syned.beamline.shape import Rectangle
    boundary_shape = Rectangle(x_left=-0.03, x_right=0.03, y_bottom=-0.218, y_top=0.218)
    from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror
    optical_element = S4ParaboloidMirror(name='Paraboloid Mirror', boundary_shape=boundary_shape,
                                         at_infinity=1,
                                         surface_calculation=0,
                                         p_focus=4.973700, q_focus=0.000000, grazing_angle=0.016057,  # for internal
                                         parabola_parameter=1.000000, pole_to_focus=1.000000,  # for external
                                         is_cylinder=0, cylinder_direction=0, convexity=1,
                                         f_reflec=0, f_refl=0, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                         coating_material='Si', coating_density=2.33, coating_roughness=0)
    ideal_mirror = optical_element
    boundary_shape = None

    from shadow4.beamline.optical_elements.mirrors.s4_numerical_mesh_mirror import S4NumericalMeshMirror
    optical_element = S4NumericalMeshMirror(name='Numerical Mesh Mirror', boundary_shape=boundary_shape,
                                            xx=None, yy=None, zz=None,
                                            # surface_data_file='/nobackup/gurb1/srio/Oasys/paraboloidal_mirror_map.hdf5',
                                            surface_data_file='/nobackup/gurb1/srio/Oasys/plane_parabola.hdf5',
                                            f_reflec=0, f_refl=0, file_refl='', refraction_index=1,
                                            coating_material='', coating_density=1, coating_roughness=0)
    numerical_mesh_mirror = optical_element
    from syned.beamline.shape import Rectangle
    boundary_shape = Rectangle(x_left=-0.03, x_right=0.03, y_bottom=-0.218, y_top=0.218)

    from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import \
        S4AdditionalNumericalMeshMirror
    optical_element = S4AdditionalNumericalMeshMirror(name='ideal + error Mirror', ideal_mirror=ideal_mirror,
                                                      numerical_mesh_mirror=numerical_mesh_mirror)

    from syned.beamline.element_coordinates import ElementCoordinates
    coordinates = ElementCoordinates(p=4.9737, q=0.218, angle_radial=1.554739298, angle_azimuthal=0,
                                     angle_radial_out=1.554739298)
    movements = None
    from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import \
        S4AdditionalNumericalMeshMirrorElement
    beamline_element = S4AdditionalNumericalMeshMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                              movements=movements, input_beam=beam)

    beam, footprint = beamline_element.trace_beam()

    return beam, footprint, beamline_element

def parabola_without(beam):
    # optical element number XX
    from syned.beamline.shape import Rectangle
    boundary_shape = Rectangle(x_left=-0.03, x_right=0.03, y_bottom=-0.218, y_top=0.218)
    from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror
    optical_element = S4ParaboloidMirror(name='Paraboloid Mirror', boundary_shape=boundary_shape,
                                         at_infinity=1,
                                         surface_calculation=0,
                                         p_focus=4.973700, q_focus=0.000000, grazing_angle=0.016057,  # for internal
                                         parabola_parameter=1.000000, pole_to_focus=1.000000,  # for external
                                         is_cylinder=0, cylinder_direction=0, convexity=1,
                                         f_reflec=0, f_refl=0, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                         coating_material='Si', coating_density=2.33, coating_roughness=0)

    from syned.beamline.element_coordinates import ElementCoordinates
    coordinates = ElementCoordinates(p=4.9737, q=0.218, angle_radial=1.554739298, angle_azimuthal=0,
                                     angle_radial_out=1.554739298)
    movements = None
    from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirrorElement
    beamline_element = S4ParaboloidMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                 movements=movements, input_beam=beam)

    beam, footprint = beamline_element.trace_beam()

    return beam, footprint, beamline_element


def run2(use_parabola_error=True):
   from shadow4.beamline.s4_beamline import S4Beamline

   beamline = S4Beamline()

   #
   #
   #
   from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
   light_source = SourceGeometrical(name='SourceGeometrical', nrays=1000, seed=5676561)
   light_source.set_spatial_type_gaussian(sigma_h=1.489e-05, sigma_v=0.000015)
   light_source.set_depth_distribution_off()
   light_source.set_angular_distribution_uniform(hdiv1=-0.012100, hdiv2=0.012100, vdiv1=-0.001400, vdiv2=0.001400)
   light_source.set_energy_distribution_uniform(value_min=1489.800000, value_max=1490.200000, unit='eV')
   light_source.set_polarization(polarization_degree=0.500000, phase_diff=0.000000, coherent_beam=1)
   beam = light_source.get_beam()

   beamline.set_light_source(light_source)

   beam_with, footprint_with, beamline_element_with = parabola_with(beam)
   beam_without, footprint_without, beamline_element_without = parabola_without(beam)

   # for i in range(beam.N):
   #     print(i, (beam_with.rays[i,3:6]**2).sum() , (beam_without.rays[i,3:6]**2).sum())

   for i in [0,1,2,3,4,5]:
       print("MIN: ",i, numpy.abs(beam_with.rays[:, i]).min(), numpy.abs(beam_without.rays[:, i]).min())
       print("MAX: ",i, numpy.abs(beam_with.rays[:, i]).max(), numpy.abs(beam_without.rays[:, i]).max())

   if use_parabola_error:
       beam = beam_with
       # footprint = footprint_with
       beamline_element = beamline_element_with
   else:
       beam = beam_without
       # footprint = footprint_without
       beamline_element = beamline_element_without

   # for i in [3,4,5]:
   #     beam.rays[0:(beam.N+1),i] = beam_without.rays[0:(beam.N+1),i]




   beam.rays[:, 3] = beam_without.rays[:, 3]
   beam.rays[:, 4] = beam_with.rays[:, 4]
   beam.rays[:, 5] = beam_without.rays[:, 5]
   # for i in [3,4,5]:
   #     beam.rays[0:(beam.N+1),i] = beam_with.rays[0:(beam.N+1),i]
   beamline.append_beamline_element(beamline_element)




   # optical element number XX
   from syned.beamline.shape import Rectangle
   boundary_shape = Rectangle(x_left=-0.04, x_right=0.04, y_bottom=-0.02, y_top=0.02)

   from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
   optical_element = S4PlaneCrystal(name='Plane Crystal',
                                    boundary_shape=boundary_shape, material='AlphaQuartz',
                                    miller_index_h=1, miller_index_k=0, miller_index_l=0,
                                    f_bragg_a=True, asymmetry_angle=1.3439035240356338,
                                    is_thick=1, thickness=0.001,
                                    f_central=1, f_phot_cent=0, phot_cent=1490.0,
                                    file_refl='bragg.dat',
                                    f_ext=0,
                                    material_constants_library_flag=0,
                                    # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
                                    method_efields_management=0,  # 0=new in S4; 1=like in S3
                                    )
   ideal_crystal = optical_element
   boundary_shape = None

   from shadow4.beamline.optical_elements.crystals.s4_numerical_mesh_crystal import S4NumericalMeshCrystal
   optical_element = S4NumericalMeshCrystal(name='Sphere Crystal', boundary_shape=boundary_shape,
                                            xx=None, yy=None, zz=None,
                                            surface_data_file='/nobackup/gurb1/srio/Oasys/Quartz1_notilt.hdf5',
                                            material='AlphaQuartz',
                                            miller_index_h=1, miller_index_k=0, miller_index_l=0,
                                            f_bragg_a=True, asymmetry_angle=1.3439035240356338,
                                            is_thick=1, thickness=0.001,
                                            f_central=1, f_phot_cent=0, phot_cent=1490.0,
                                            file_refl='bragg.dat',
                                            f_ext=0,
                                            material_constants_library_flag=0,
                                            # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
                                            )
   numerical_mesh_crystal = optical_element
   from syned.beamline.shape import Rectangle
   boundary_shape = Rectangle(x_left=-0.04, x_right=0.04, y_bottom=-0.02, y_top=0.02)

   from shadow4.beamline.optical_elements.crystals.s4_additional_numerical_mesh_crystal import \
      S4AdditionalNumericalMeshCrystal
   optical_element = S4AdditionalNumericalMeshCrystal(name='ideal + error Mirror', ideal_crystal=ideal_crystal,
                                                      numerical_mesh_crystal=numerical_mesh_crystal)

   from syned.beamline.element_coordinates import ElementCoordinates
   coordinates = ElementCoordinates(p=0.218, q=0.0265, angle_radial=-1.133607015, angle_azimuthal=0,
                                    angle_radial_out=1.54310934)
   movements = None
   from shadow4.beamline.optical_elements.crystals.s4_additional_numerical_mesh_crystal import \
      S4AdditionalNumericalMeshCrystalElement
   beamline_element = S4AdditionalNumericalMeshCrystalElement(optical_element=optical_element, coordinates=coordinates,
                                                              movements=movements, input_beam=beam)

   beam, footprint = beamline_element.trace_beam()

   beamline.append_beamline_element(beamline_element)

   # optical element number XX
   from syned.beamline.shape import Rectangle
   boundary_shape = Rectangle(x_left=-0.04, x_right=0.04, y_bottom=-0.02, y_top=0.02)

   from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
   optical_element = S4PlaneCrystal(name='Plane Crystal',
                                    boundary_shape=boundary_shape, material='AlphaQuartz',
                                    miller_index_h=1, miller_index_k=0, miller_index_l=0,
                                    f_bragg_a=True, asymmetry_angle=-1.3439035240356338,
                                    is_thick=1, thickness=0.001,
                                    f_central=0, f_phot_cent=0, phot_cent=1490.0,
                                    file_refl='bragg.dat',
                                    f_ext=0,
                                    material_constants_library_flag=0,
                                    # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
                                    method_efields_management=0,  # 0=new in S4; 1=like in S3
                                    )
   ideal_crystal = optical_element
   boundary_shape = None

   from shadow4.beamline.optical_elements.crystals.s4_numerical_mesh_crystal import S4NumericalMeshCrystal
   optical_element = S4NumericalMeshCrystal(name='Sphere Crystal', boundary_shape=boundary_shape,
                                            xx=None, yy=None, zz=None,
                                            surface_data_file='/nobackup/gurb1/srio/Oasys/plane.hdf5',
                                            material='AlphaQuartz',
                                            miller_index_h=1, miller_index_k=0, miller_index_l=0,
                                            f_bragg_a=True, asymmetry_angle=-1.3439035240356338,
                                            is_thick=1, thickness=0.001,
                                            f_central=0, f_phot_cent=0, phot_cent=1490.0,
                                            file_refl='bragg.dat',
                                            f_ext=0,
                                            material_constants_library_flag=0,
                                            # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
                                            )
   numerical_mesh_crystal = optical_element
   from syned.beamline.shape import Rectangle
   boundary_shape = Rectangle(x_left=-0.04, x_right=0.04, y_bottom=-0.02, y_top=0.02)

   from shadow4.beamline.optical_elements.crystals.s4_additional_numerical_mesh_crystal import \
      S4AdditionalNumericalMeshCrystal
   optical_element = S4AdditionalNumericalMeshCrystal(name='ideal + error Mirror', ideal_crystal=ideal_crystal,
                                                      numerical_mesh_crystal=numerical_mesh_crystal)

   from syned.beamline.element_coordinates import ElementCoordinates
   coordinates = ElementCoordinates(p=0.0265, q=0.215, angle_radial=1.544854625, angle_azimuthal=3.141592654,
                                    angle_radial_out=-1.133494483)
   movements = None
   from shadow4.beamline.optical_elements.crystals.s4_additional_numerical_mesh_crystal import \
      S4AdditionalNumericalMeshCrystalElement
   beamline_element = S4AdditionalNumericalMeshCrystalElement(optical_element=optical_element, coordinates=coordinates,
                                                              movements=movements, input_beam=beam)

   beam, footprint = beamline_element.trace_beam()

   beamline.append_beamline_element(beamline_element)

   return beam, footprint


if __name__ == "__main__":
   import numpy
   beam1, footprint1 = run2(use_parabola_error=1)
   # beam2, footprint2 = run2()
   #
   # N = beam1.N
   # intens1 = beam1.get_column(23)
   # intens2 = beam2.get_column(23)
   # flag1 = footprint1.get_column(10)
   # flag2 = footprint2.get_column(10)
   # z1 = footprint1.get_column(3)
   # z2 = footprint2.get_column(3)
   # for i in range(90):
   #    print(i, intens1[i], intens2[i], flag1[i], flag2[i], z1[i], z2[i])
   # beam.rays[10,0] = numpy.nan
   # print(numpy.isnan(beam.rays.sum()))



