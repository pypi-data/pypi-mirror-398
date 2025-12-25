from shadow4.beamline.s4_beamline import S4Beamline
import numpy
method_efields_management = 0

beamline = S4Beamline()

#
#
#
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
light_source = SourceGeometrical(name='SourceGeometrical', nrays=1000, seed=5676563)
light_source.set_spatial_type_point()
light_source.set_depth_distribution_off()
light_source.set_angular_distribution_flat(hdiv1=0.000000,hdiv2=0.000000,vdiv1=0.000000,vdiv2=0.000000)
light_source.set_energy_distribution_singleline(12914.000000, unit='eV')
light_source.set_polarization(polarization_degree=0.500000, phase_diff=0.000000, coherent_beam=1)
beam = light_source.get_beam()
BEAMS=[beam]
beamline.set_light_source(light_source)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=0, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=numpy.pi, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=numpy.pi, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=3, angle_radial=0.7853354735, angle_azimuthal=numpy.pi, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=numpy.pi/2, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=numpy.pi, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=0.005657, angle_radial=0.7853354735, angle_azimuthal=numpy.pi, angle_radial_out=0.7853354735)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)

# optical element number XX
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystal
optical_element = S4PlaneCrystal(name='Plane Crystal',
    boundary_shape=None, material='Si',
    miller_index_h=8, miller_index_k=0, miller_index_l=0,
    f_bragg_a=False, asymmetry_angle=0.0,
    is_thick=1, thickness=0.001,
    f_central=1, f_phot_cent=0, phot_cent=12914.0,
    file_refl='Si(800)_12890_12940.dat',
    f_ext=0,
    material_constants_library_flag=0, # 0=xraylib,1=dabax,2=preprocessor v1,3=preprocessor v2
    method_efields_management=method_efields_management, # 0=new in S4; 1=like in S3
    )
from syned.beamline.element_coordinates import ElementCoordinates
coordinates = ElementCoordinates(p=0, q=3, angle_radial=0.7853355061, angle_azimuthal=numpy.pi, angle_radial_out=0.7853355061)
movements = None
from shadow4.beamline.optical_elements.crystals.s4_plane_crystal import S4PlaneCrystalElement
beamline_element = S4PlaneCrystalElement(optical_element=optical_element,coordinates=coordinates, movements=movements, input_beam=beam)

beam, mirr = beamline_element.trace_beam()
BEAMS.append(beam)
beamline.append_beamline_element(beamline_element)


# test plot
if 0:
   from srxraylib.plot.gol import plot_scatter
   plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)
   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')


# print('########################################################\n')
# print(f'{BEAMS[0].get_intensity():.6g} {BEAMS[0].get_intensity(polarization=1):.6g} {BEAMS[0].get_intensity(polarization=2):.6g}')
# print('\n')
# print(f'{BEAMS[1].get_intensity():.6g} {BEAMS[1].get_intensity(polarization=1):.6g} {BEAMS[1].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[2].get_intensity():.6g} {BEAMS[2].get_intensity(polarization=1):.6g} {BEAMS[2].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[3].get_intensity():.6g} {BEAMS[3].get_intensity(polarization=1):.6g} {BEAMS[3].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[4].get_intensity():.6g} {BEAMS[4].get_intensity(polarization=1):.6g} {BEAMS[4].get_intensity(polarization=2):.6g}')
# print('\n')
# print(f'{BEAMS[5].get_intensity():.6g} {BEAMS[5].get_intensity(polarization=1):.6g} {BEAMS[5].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[6].get_intensity():.6g} {BEAMS[6].get_intensity(polarization=1):.6g} {BEAMS[6].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[7].get_intensity():.6g} {BEAMS[7].get_intensity(polarization=1):.6g} {BEAMS[7].get_intensity(polarization=2):.6g}')
# print(f'{BEAMS[8].get_intensity():.6g} {BEAMS[8].get_intensity(polarization=1):.6g} {BEAMS[8].get_intensity(polarization=2):.6g}')
# print('\n')


#
# analysis
#

import numpy

print("##################################  beam intensities ################################")
for i in range(len(BEAMS)):
    print(
        f'tot: {BEAMS[i].get_intensity():.6g} s: {BEAMS[i].get_intensity(polarization=1):.6g} p: {BEAMS[i].get_intensity(polarization=2):.6g}')
print('\n')

r_s_ampl = -0.024724229926740865-0.9700768156818347j
r_p_ampl = 0.0009332843711563077+0.0011002464391183318j

r_s_mod = numpy.abs(r_s_ampl)
r_p_mod = numpy.abs(r_p_ampl)

r_s = r_s_mod ** 2 # 0.94166032
r_p = r_p_mod ** 2 # 2.08156194e-06

R_S = [r_s, r_s, r_s, r_s, r_p, r_s, r_s, r_s]
R_P = [r_p, r_p, r_p, r_p, r_s, r_p, r_p, r_p]


I_s = 1000/2
I_p = 1000/2


for i in range(len(R_S)):
    I_s *= R_S[i]
    I_p *= R_P[i]
    print("Analytical s,p (after %d crystals: ) " % (1+i), I_s, I_p )


print('\n')

print("##################################  Jones vectors ################################")
print("Jones vector at source: ",   BEAMS[0].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2),1/numpy.sqrt(2)],)
print("Jones vector after xtal1: ", BEAMS[1].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**1              , 1/numpy.sqrt(2) * r_p_ampl**1])
print("Jones vector after xtal2: ", BEAMS[2].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**2              , 1/numpy.sqrt(2) * r_p_ampl**2])
print("Jones vector after xtal3: ", BEAMS[3].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**3              , 1/numpy.sqrt(2) * r_p_ampl**3])
print("Jones vector after xtal4: ", BEAMS[4].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**4              , 1/numpy.sqrt(2) * r_p_ampl**4])
print("Jones vector after xtal5: ", BEAMS[5].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**4 * r_p_ampl   , 1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**4])
print("Jones vector after xtal6: ", BEAMS[6].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**5 * r_p_ampl   , 1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**5])
print("Jones vector after xtal7: ", BEAMS[7].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**6 * r_p_ampl   , 1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**6])
print("Jones vector after xtal8: ", BEAMS[8].get_jones()[0], "analytical_exact", [1/numpy.sqrt(2) * r_s_ampl**7 * r_p_ampl   , 1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**7])

print("##################################  Jones vectors modulus ################################")
print("Jones vector modulus at source: ",   numpy.abs(BEAMS[0].get_jones()[0]), "analytical", [1/numpy.sqrt(2),1/numpy.sqrt(2)],)
print("Jones vector modulus after xtal1: ", numpy.abs(BEAMS[1].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**1             , 1/numpy.sqrt(2) * r_p_mod**1])
print("Jones vector modulus after xtal2: ", numpy.abs(BEAMS[2].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**2             , 1/numpy.sqrt(2) * r_p_mod**2])
print("Jones vector modulus after xtal3: ", numpy.abs(BEAMS[3].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**3             , 1/numpy.sqrt(2) * r_p_mod**3])
print("Jones vector modulus after xtal4: ", numpy.abs(BEAMS[4].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**4             , 1/numpy.sqrt(2) * r_p_mod**4])
print("Jones vector modulus after xtal5: ", numpy.abs(BEAMS[5].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**4 * r_p_mod   , 1/numpy.sqrt(2) * r_s_mod    * r_p_mod**4])
print("Jones vector modulus after xtal6: ", numpy.abs(BEAMS[6].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**5 * r_p_mod   , 1/numpy.sqrt(2) * r_s_mod    * r_p_mod**5])
print("Jones vector modulus after xtal7: ", numpy.abs(BEAMS[7].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**6 * r_p_mod   , 1/numpy.sqrt(2) * r_s_mod    * r_p_mod**6])
print("Jones vector modulus after xtal8: ", numpy.abs(BEAMS[8].get_jones()[0]), "analytical", [1/numpy.sqrt(2) * r_s_mod**7 * r_p_mod   , 1/numpy.sqrt(2) * r_s_mod    * r_p_mod**7])

print("Intensity at source: ",   BEAMS[0].get_column(24)[0], BEAMS[0].get_column(25)[0], "analytical", 0.5, 0.5)
print("Intensity after xtal1: ", BEAMS[1].get_column(24)[0], BEAMS[1].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**1           )**2  , numpy.abs(1/numpy.sqrt(2) * r_p_ampl**1)**2)
print("Intensity after xtal2: ", BEAMS[2].get_column(24)[0], BEAMS[2].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**2           )**2  , numpy.abs(1/numpy.sqrt(2) * r_p_ampl**2)**2)
print("Intensity after xtal3: ", BEAMS[3].get_column(24)[0], BEAMS[3].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**3           )**2  , numpy.abs(1/numpy.sqrt(2) * r_p_ampl**3)**2)
print("Intensity after xtal4: ", BEAMS[4].get_column(24)[0], BEAMS[4].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**4           )**2  , numpy.abs(1/numpy.sqrt(2) * r_p_ampl**4)**2)
print("Intensity after xtal5: ", BEAMS[5].get_column(24)[0], BEAMS[5].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**4 * r_p_ampl)**2  , numpy.abs(1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**4)**2)
print("Intensity after xtal6: ", BEAMS[6].get_column(24)[0], BEAMS[6].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**5 * r_p_ampl)**2  , numpy.abs(1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**5)**2)
print("Intensity after xtal7: ", BEAMS[7].get_column(24)[0], BEAMS[7].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**6 * r_p_ampl)**2  , numpy.abs(1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**6)**2)
print("Intensity after xtal8: ", BEAMS[8].get_column(24)[0], BEAMS[8].get_column(25)[0], "analytical", numpy.abs(1/numpy.sqrt(2) * r_s_ampl**7 * r_p_ampl)**2  , numpy.abs(1/numpy.sqrt(2) * r_s_ampl    * r_p_ampl**7)**2)


print('\n')

