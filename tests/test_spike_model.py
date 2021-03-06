# -*- coding: utf-8 -*-
# This file is part of the hdnet package
# Copyright 2014 the authors, see file AUTHORS.
# Licensed under the GPLv3, see file LICENSE for details

import os
from test_tmppath import TestTmpPath
import numpy as np

from hdnet.spikes import Spikes
from hdnet.spikes_model import SpikeModel, Shuffled, BernoulliHomogeneous, BernoulliInhomogeneous, \
    DichotomizedGaussian, DichotomizedGaussianPoisson
from hdnet.sampling import poisson_marginals, find_dg_any_marginal, sample_dg_any_marginal


class TestSpikeModel(TestTmpPath):

    def setUp(self):
        super(TestSpikeModel, self).setUp()
        import logging
        logging.disable(level=logging.WARNING)

    def tearDown(self):
        super(TestSpikeModel, self).tearDown()

    def test_basic_patterns(self):
        np.random.seed(42)
        spikes = (np.random.random((2, 10, 200)) < .05).astype(int)
        spikes[0, [1, 5], ::5] = 1
        spikes[1, [2, 3, 6], ::11] = 1
        spikes = Spikes(spikes=spikes)
        spikes_model = SpikeModel(spikes=spikes)
        spikes_model.fit()
        spikes_model.chomp()
        self.assertEqual(len(spikes_model.hopfield_patterns.sequence), 400)
        self.assertEqual(len(spikes_model.hopfield_patterns), 3)
        self.assertEqual(len(spikes_model.raw_patterns.sequence), 400)
        self.assertEqual(len(spikes_model.raw_patterns), 51)

    def test_basic(self):
        np.random.seed(42)

        file_contents = np.load(os.path.join(os.path.dirname(__file__), 'test_data/spikes_trials.npz'))
        spikes = Spikes(file_contents[file_contents.keys()[0]])
        spikes_model = SpikeModel(spikes=spikes)
        spikes_model.fit(remove_zeros=True)
        spikes_model.chomp()

        spikes_model.save(os.path.join(self.TMP_PATH, 'spikes_model'))
        spikes_model2 = SpikeModel.load(os.path.join(self.TMP_PATH, 'spikes_model'))
        self.assertEqual(len(spikes_model.hopfield_patterns), len(spikes_model2.hopfield_patterns))

        spikes_model.fit(remove_zeros=False)
        spikes_model.chomp()

        wss = [1, 2]
        counts, entropies = spikes_model.distinct_patterns_over_windows(wss, remove_zeros=False)

        bernoulli_model = BernoulliHomogeneous(spikes=spikes)
        bernoulli_model.fit()
        bernoulli_model.chomp()
        
        shuffle_model = Shuffled(spikes=spikes)
        shuffle_model.fit()
        shuffle_model.chomp()

        bernoulli_model = BernoulliHomogeneous(spikes=spikes)
        bernoulli_model.fit()
        bernoulli_model.chomp()
        
        wss = [1, 2, 3]
        counts, entropies = bernoulli_model.distinct_patterns_over_windows(wss)
        
        # sanity check on large Bernoulli example
        spikes_arr = np.random.randn(4, 10000)
        spikes = Spikes(spikes=spikes_arr)
        
        bernoulli_model = BernoulliHomogeneous(spikes=spikes)
        
        wss = [1, 2, 3]
        counts, entropies = bernoulli_model.distinct_patterns_over_windows(wss)
        
        # self.assertTrue(np.abs((entropies[0, 0] / np.array(wss)).mean() - spikes.N) < .1)

        bernoulli_inhom_model = BernoulliInhomogeneous(spikes=spikes)
        bernoulli_inhom_model.fit()
        bernoulli_inhom_model.chomp()

        dichotomized_gaussian = DichotomizedGaussian(spikes=spikes)
        #dichotomized_gaussian.sample_from_model()

        dichotomized_gaussian_poiss = DichotomizedGaussianPoisson(spikes=spikes)
        #spikes = dichotomized_gaussian_poiss.sample_from_model()

        #from hdnet.visualization import raster_plot_psth
        #import matplotlib.pyplot as plt
        #raster_plot_psth(spikes.spikes)

    def test_dichotomized_gaussian(self):
        bin_means = np.array([7, 9])
        bin_cov = np.array([[7, 3], [3, 9]])
        num_samples = 10000

        np.random.seed(42)

        # calculate marginal distribution of Poisson
        pmfs, cmfs, supports = poisson_marginals(bin_means)

        self.assertEqual(len(pmfs), 2)
        self.assertTrue(sum(map(sum, pmfs)) - 2. < 1e-4)
        self.assertEqual(len(pmfs[0]), len(supports[0]))
        self.assertEqual(len(pmfs[1]), len(supports[1]))
        self.assertEqual(len(pmfs[0]), len(cmfs[0]))
        self.assertEqual(len(pmfs[1]), len(cmfs[1]))

        # find paramters of DG
        gauss_means, gauss_covs, joints = find_dg_any_marginal(pmfs, bin_cov, supports)

        # generate samples
        np.random.seed(0)
        samples, hists = sample_dg_any_marginal(gauss_means, gauss_covs, num_samples, supports)

        self.assertTrue(samples[:, 0].mean() - 7, 1e-2)
        self.assertTrue(samples[:, 1].mean() - 9, 1e-2)


# end of source
