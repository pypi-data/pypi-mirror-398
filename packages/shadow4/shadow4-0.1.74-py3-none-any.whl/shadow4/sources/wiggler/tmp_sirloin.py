
# electron beam
from shadow4.sources.s4_electron_beam import S4ElectronBeam
electron_beam = S4ElectronBeam(energy_in_GeV=0.8 ,energy_spread=0 ,current=0.1)
electron_beam.set_sigmas_all(sigma_x=0, sigma_y=0, sigma_xp=0, sigma_yp=0)

# magnetic structure
from shadow4.sources.wiggler.s4_wiggler import S4Wiggler
source = S4Wiggler(
    magnetic_field_periodic  = 1,  # 0=external, 1=periodic
    file_with_magnetic_field = "",  # used only if magnetic_field_periodic=0
    K_vertical         = 5.38,  # syned Wiggler pars: used only if magnetic_field_periodic=1
    period_length      = 0.129, # syned Wiggler pars: used only if magnetic_field_periodic=1
    number_of_periods  = 22,  # syned Wiggler pars: used only if magnetic_field_periodic=1
    emin               = 0.012398, # 0.0001,  # Photon energy scan from energy (in eV)
    emax               = 0.012398, # 1.0,  # Photon energy scan to energy (in eV)
    ng_e               = 101,  # Photon energy scan number of points for spectrum and internal calculation
    ng_j               = 501 , # Number of points in electron trajectory (per period) for internal calculation only
    epsi_dx            = 0.0,  # position y of waist X [m]
    epsi_dz            = 0.0,  # position y of waist Z [m]
    psi_interval_number_of_points = 101 , # the number psi (vertical angle) points for internal calculation only
    flag_interpolation = 2, # Use interpolation to sample psi (0=No, 1=Yes)
    flag_emittance     = 0, # Use emittance (0=No, 1=Yes)
    shift_x_flag       = 1, # 0="No shift", 1="Half excursion", 2="Minimum", 3="Maximum", 4="Value at zero", 5="User value"
    shift_x_value      = 0.0, # used only if shift_x_flag=5
    shift_betax_flag   = 0, # 0="No shift", 1="Half excursion", 2="Minimum", 3="Maximum", 4="Value at zero", 5="User value"
    shift_betax_value  = 0.0  ,  # used only if shift_betax_flag=5
)

# light source
from shadow4.sources.wiggler.s4_wiggler_light_source import S4WigglerLightSource
light_source = S4WigglerLightSource(name='wiggler' ,electron_beam=electron_beam ,magnetic_structure=source ,nrays=15000
                                    ,seed=5676561)

from shadow4.tools.logger import set_verbose
set_verbose()
beam = light_source.get_beam(psi_interval_in_units_one_over_gamma=None)




# test plot
from srxraylib.plot.gol import plot_scatter, plot

rays = beam.get_rays()
plot_scatter(1e6 * rays[:, 3], 1e6 * rays[:, 5], title='(Xp,Zp) in urad')
plot_scatter(rays[:, 1], 1e6 * rays[:, 0], title='X(Y)')

delta = 0.01
tkt = beam.histo1(-11, xrange=[0.012398-delta,0.012398+delta])
for key in tkt.keys():
    print(key)
plot(tkt["bin_path"], tkt["histogram_path"])