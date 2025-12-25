


def run_beamline():
    #
    #
    #
    from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
    light_source = SourceGeometrical(name='SourceGeometrical', nrays=500000, seed=5676561)
    light_source.set_spatial_type_point()
    light_source.set_depth_distribution_off()
    light_source.set_angular_distribution_gaussian(sigdix=0.000001, sigdiz=0.000001)
    light_source.set_energy_distribution_singleline(1000.000000, unit='eV')
    light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
    beam = light_source.get_beam()
    return beam


# test plot
from srxraylib.plot.gol import plot, plot_scatter
import numpy

beam = run_beamline()

tkt = beam.histo1(6, xrange=[-10e-6, 10e-6], nbins=2000, ref=23, calculate_hew=1)
# plot(tkt["bin_path"], tkt["histogram_path"])
print("FWHM, FWHM*0.573, HEW, Theory: ", 1e6*tkt["fwhm"], 1e6*0.573*tkt["fwhm"], 1e6*tkt["hew"], 1.349)

# tkt = beam.histo1(42, xrange=[0, 10e-6], nbins=1000, ref=23, calculate_hew=1)
# print("FWHM, HEW: ", 1e6*tkt["fwhm"], 1e6*tkt["hew"])

print(beam.calculate_hew_x(nolost=1))
print(beam.calculate_hew_z(nolost=1))
print(beam.calculate_hew(nolost=1))

