import numpy
energy = numpy.linspace(70900,71100,100)
spectral_power = numpy.ones(100)


#
# script to make the calculations (created by XOPPY:xpower)
#

import numpy
from xoppylib.power.xoppy_calc_power_monochromator import xoppy_calc_power_monochromator
try: import xraylib
except: print("xraylib not available")
from dabax.dabax_xraylib import DabaxXraylib

out_dictionary = xoppy_calc_power_monochromator(
        energy, # array with energies in eV
        spectral_power, # array with source spectral density
        TYPE                       = 2, # 0=None, 1=Crystal Bragg, 2=Crystal Laue, 3=Multilayer, 4=External file
        crystal_descriptor         = "Si", # crystal descriptor (for xraylib/dabax) in crystal monochromator
        ENER_SELECTED              = 71000.0, # Energy to set crystal monochromator
        METHOD                     = 1, # For crystals, in crystalpy, 0=Zachariasem, 1=Guigay
        THICK                      = 15, # crystal thicknes Laur crystal in um
        ML_H5_FILE                 = "/users/srio/Oasys/multilayerTiC.h5", # File with inputs from multilaters (from xoppy/Multilayer)
        ML_GRAZING_ANGLE_DEG       = 0.4, # for multilayers the grazing angle in degrees
        N_REFLECTIONS              = 2, # number of reflections (crystals or multilayers)
        FILE_DUMP                  = 0, # 0=No, 1=yes
        polarization               = 0, # 0=sigma, 1=pi, 2=unpolarized
        external_reflectivity_file = "<none>", # file with external reflectivity
        output_file                = "monochromator.spec", # filename if FILE_DUMP=1
        material_constants_library = DabaxXraylib(file_f1f2="f1f2_Windt.dat",file_CrossSec="CrossSec_EPDL97.dat"),
        )


# data to pass
energy = out_dictionary["data"][0,:]
spectral_power = out_dictionary["data"][-1,:]

#
# example plots
#
if True:
    from srxraylib.plot.gol import plot
    plot(out_dictionary["data"][0,:], out_dictionary["data"][1,:],
        out_dictionary["data"][0,:], out_dictionary["data"][-1,:],
        xtitle=out_dictionary["labels"][0],
        legend=[out_dictionary["labels"][1],out_dictionary["labels"][-1]],
        title='Spectral Power [W/eV]')

#
# end script
#
