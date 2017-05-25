"""National neonatal demand and capacity model
*** Requires Python 3.6 or greater***

Class to describe patient attributes

Version 170501

(c)2017 Michael Allen 
This code is distributed under GNU GPL2
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
For info contact michael.allen1966@gmail.com
"""

import numpy as np
import random


class Patient:
    """
     Attributes;
     'birth_hospital',
     'category',
     'category_without_surgery',
     'closest_appropriate_hospital',
     'complete',
     'current_hospital'
     'current_network',
     'delivery_id',
     'distance_from_home',
     'entry',
     'fetuses',
     'home_network',
     'ho
     'id',
     'in_closest_appropriate_hospital',
     'in_home_network',
     'last_hopsital',
     'los_ln_mu',
     'los_ln_stdev',
     'lsoa',
     'previous_hospital',
     'required_care_level_current',
     'set_care_requirements',
     'spells',
     'total_transfer_distance',
     'transfers',
     'time_in',
     'time_out,
     'year',
     'use_levels

    """

    def __init__(self, data, id, delivery, time_in, year):

        self.id = id
        self.delivery_id = delivery
        self.time_in = time_in
        self.year = year
        self.spells = 0
        self.current_hospital = 'None'
        self.current_network = 0
        self.home_network = 0
        self.in_closest_appropriate_hospital = False
        self.in_home_network = False
        self.closest_appropriate_hospital = 'None'
        # Set LSOA (by reading weights and selection)
        weights = data.lsoa_demand['all_neonatal']
        selection = data.lsoa_demand.index
        self.lsoa = random.choices(selection, weights=weights)
        self.lsoa = self.lsoa[0]
        self.birth_hospital = 'None'
        self.last_hopsital = 'None'
        self.complete = False
        self.distance_from_home = 0
        self.transfers = 0
        self.total_transfer_distance = 0

        # Set infant category
        weights = data.deliveries['percent_all_deliveries']
        selection = np.arange(len(weights))
        self.category = random.choices(selection, weights=weights)

        # Add multiple pregnancies (twins etc)
        self.fetuses = 1
        weights = data.fetuses_matrix[self.category, :]
        weights = weights[0]
        selection = np.arange(len(weights)) + 1
        self.fetuses = random.choices(selection, weights=weights)[0]

    def set_care_requirements(self, data):
        # set surgical category        # Set twins
        self.category_without_surgery = self.category
        prob_surgery_array = data.deliveries['percent_infants_surgical'].values
        prob_surgery = prob_surgery_array[self.category] / 100
        if np.random.binomial(1, prob_surgery) == 1:
            self.category = [6]
        # Initially set all use to False. Set LoS by category
        self.use_levels = [False, False, False, False, False]
        self.los_ln_mu = data.los_ln_mu.values[self.category, :]
        self.los_ln_stdev = data.los_ln_stdev.values[self.category, :]

        # Identify entry point
        weights = data.entry_matrix[self.category, :]
        weights = weights[0]
        selection = np.arange(len(weights))
        self.entry = random.choices(selection, weights=weights)[0]
        self.use_levels[self.entry] = True
        self.required_care_level_current = self.entry
        last_assigned_level = self.entry

        # Add further use levels
        while last_assigned_level < 5:
            weights = data.transition_matrix[last_assigned_level, self.category, :]
            weights = weights[0]
            selection = np.arange(len(weights))
            next_assigned_level = random.choices(selection, weights=weights)[0]
            if next_assigned_level < 5:
                self.use_levels[next_assigned_level] = True
            last_assigned_level = next_assigned_level

            # Add lengths of stay
            # loop through care levels
            self.los = []
            for care_level in range(5):
                _los_mu = self.los_ln_mu[0][care_level]
                _los_stdev = self.los_ln_stdev[0][care_level]
                _los = np.random.lognormal(_los_mu, _los_stdev)
                self.los.append(_los)
