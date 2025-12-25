
# electron beam
from shadow4.sources.s4_electron_beam import S4ElectronBeam
electron_beam = S4ElectronBeam(energy_in_GeV=2,energy_spread=0,current=0.4)
electron_beam.set_sigmas_all(sigma_x=0,sigma_y=0,sigma_xp=0,sigma_yp=0)

#magnetic structure
from shadow4.sources.bending_magnet.s4_bending_magnet import S4BendingMagnet
source = S4BendingMagnet(
                 radius=2.0605639683602175, # from syned BM, can be obtained as S4BendingMagnet.calculate_magnetic_radius(3.2376, electron_beam.energy())
                 magnetic_field=3.2376, # from syned BM
                 length=0.004121127936720435, # from syned BM = abs(BM divergence * magnetic_radius)
                 emin=10000.0,     # Photon energy scan from energy (in eV)
                 emax=10000.1,     # Photon energy scan to energy (in eV)
                 ng_e=100,     # Photon energy scan number of points
                 flag_emittance=0, # when sampling rays: Use emittance (0=No, 1=Yes)
                 )

#light source
from shadow4.sources.bending_magnet.s4_bending_magnet_light_source import S4BendingMagnetLightSource
light_source = S4BendingMagnetLightSource(name='BendingMagnet', electron_beam=electron_beam, magnetic_structure=source, nrays=50000, seed=5676561)
beam = light_source.get_beam()

# test plot
from srxraylib.plot.gol import plot_scatter
rays = beam.get_rays()
plot_scatter(1e6 * rays[:, 0], 1e6 * rays[:, 3], title="(X,X')", show=0)
plot_scatter(1e6 * rays[:, 2], 1e6 * rays[:, 5], title="(Z,Z')")
