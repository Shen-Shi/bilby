#!/bin/python
"""
Tutorial to demonstrate running parameter estimation on a reduced parameter space
for an injected eccentric binary black hole signal with masses & distnace similar
to GW150914.

This uses the same binary parameters that were used to make Figures 1, 2 & 5 in
Lower et al. (2018) -> arXiv:1806.05350.

For a more comprehensive look at what goes on in each step, refer to the
"basic_tutorial.py" example.
"""
from __future__ import division, print_function

import numpy as np

import tupak

import matplotlib.pyplot as plt

duration = 64.
sampling_frequency = 256.

outdir = 'outdir'
label = 'eccentric_GW140914'
tupak.core.utils.setup_logger(outdir=outdir, label=label)

# Set up a random seed for result reproducibility.
np.random.seed(150914)

injection_parameters = dict(mass_1=35., mass_2=30., eccentricity=0.1,
                        luminosity_distance=440., iota=0.4, psi=0.1, phase=1.2,
                        geocent_time=1180002601.0, ra=45, dec=5.73)

waveform_arguments = dict(waveform_approximant='EccentricFD', reference_frequency=10., minimum_frequency=10.)

# Create the waveform_generator using the LAL eccentric black hole no spins source function
waveform_generator = tupak.gw.WaveformGenerator(
    duration=duration, sampling_frequency=sampling_frequency,
    frequency_domain_source_model=tupak.gw.source.lal_eccentric_binary_black_hole_no_spins,
    parameters=injection_parameters, waveform_arguments=waveform_arguments)

hf_signal = waveform_generator.frequency_domain_strain()

# Setting up three interferometers (LIGO-Hanford (H1), LIGO-Livingston (L1), and
# Virgo (V1)) at their design sensitivities. The maximum frequency is set just
# prior to the point at which the waveform model terminates. This is to avoid any
# biases introduced from using a sharply terminating waveform model.
minimum_frequency = 10.
maximum_frequency = 128.

IFOs = tupak.gw.detector.InterferometerList(['H1', 'L1', 'V1'])
for IFO in IFOs:
    IFO.minimum_frequency = minimum_frequency
    IFO.maximum_frequency = maximum_frequency

IFOs.set_strain_data_from_power_spectral_densities(sampling_frequency, duration)
IFOs.inject_signal(waveform_generator=waveform_generator, parameters=injection_parameters)

# Now we set up the priors on each of the binary parameters.
priors = dict()
priors["mass_1"] = tupak.core.prior.Uniform(name='mass_1', minimum=5, maximum=60)
priors["mass_2"] = tupak.core.prior.Uniform(name='mass_2', minimum=5, maximum=60)
priors["eccentricity"] = tupak.core.prior.PowerLaw(name='eccentricity', latex_label='$e$', alpha=-1, minimum=1e-4, maximum=0.4)
priors["luminosity_distance"] =  tupak.gw.prior.UniformComovingVolume(name='luminosity_distance', minimum=1e2, maximum=2e3)
priors["dec"] =  tupak.core.prior.Cosine(name='dec')
priors["ra"] =  tupak.core.prior.Uniform(name='ra', minimum=0, maximum=2 * np.pi)
priors["iota"] =  tupak.core.prior.Sine(name='iota')
priors["psi"] =  tupak.core.prior.Uniform(name='psi', minimum=0, maximum=np.pi)
priors["phase"] =  tupak.core.prior.Uniform(name='phase', minimum=0, maximum=2 * np.pi)
priors["geocent_time"] = tupak.core.prior.Uniform(1180002600.9, 1180002601.1, name='geocent_time')

# Initialising the likelihood function.
likelihood = tupak.gw.likelihood.GravitationalWaveTransient(interferometers=IFOs,
                      waveform_generator=waveform_generator, time_marginalization=False,
                      phase_marginalization=False, distance_marginalization=False,
                      prior=priors)

# Now we run sampler (PyMultiNest in our case).
result = tupak.run_sampler(likelihood=likelihood, priors=priors, sampler='pymultinest',
                           npoints=1000, injection_parameters=injection_parameters,
                           outdir=outdir, label=label)

# And finally we make some plots of the output posteriors.
result.plot_corner()
