"""National neonatal demand and capacity model
*** Requires Python 3.6 or greater***

Class to describe data loading

Version 170501

(c)2017 Michael Allen 
This code is distributed under Apache Licence 2.0
https://www.apache.org/licenses/LICENSE-2.0
For info contact michael.allen1966@gmail.com
"""

import numpy as np
import pandas as pd
import time


class Data:
    def __init__(self, truncate):
        start = time.time()
        self.truncate = truncate
        self.load_data()
        self.filter_input_data_to_only_used_neonatal_units()
        self.travel_tuples = self.create_travel_distance_tuple_array(self.time_df)
        self.interhospital_distance_tuples = self.create_travel_distance_tuple_array(
            self.interhospital_distance_df)
        self.interhospital_time_tuples = self.create_travel_distance_tuple_array(
            self.interhospital_time_df)
        self.find_order_of_hospitals_by_closeness()
        self.order_with_home_network_first()
        self.set_up_transition_probability_matrix()
        self.set_up_entry_matrix()
        self.set_up_fetus_number_matrix()

        del self.time_df

        # End of data load and munging
        end = time.time()
        print('\nData loaded and munged in %d seconds' % (end - start))


    def create_travel_distance_tuple_array(self, matrix):
        print('Creating travel time table...')
        index_tuple_list = []
        distance_list = []

        for row_index, row in matrix.iterrows():  # iteraate through rows
            for column_index, data in row.iteritems():  # iterate through 'columns' (items in selected row)
                index_tuple = (row_index, column_index)  # create index tuple
                index_tuple_list.append(index_tuple)  # add index tuple to list
                distance_list.append(data)  # add distance data to list

        multi_index = pd.MultiIndex.from_tuples(index_tuple_list,
                                                names=['from',
                                                       'to'])  # set up a tuple multi-level index
        output = pd.Series(distance_list, index=multi_index, name='Distance')
        return output

    def filter_input_data_to_only_used_neonatal_units(self):
        print('\nTruncated to listed neonatal units...')
        self.hospital_info_df = self.hospital_info_df.loc[
            self.hospital_info_df['neonatal_current'] == 1]
        self.hospitals = list(self.hospital_info_df['hospital_postcode'])
        self.time_df = self.time_df[self.hospitals]
        print('Truncated distance matrix size: ', self.time_df.shape)
        print('Truncated hospital info size: ', self.hospital_info_df.shape)

    def load_data(self):
        # Load data with munging
        print('\nLoading data...')
        self.deliveries = pd.read_csv('data/deliveries.csv')
        self.fetuses_table = pd.read_csv('data/fetuses.csv')
        self.entry_point = pd.read_csv('data/entry_point.csv')
        self.exit_surgery = pd.read_csv('data/exit_surgery.csv')
        self.exit_level_1 = pd.read_csv('data/exit_level_1.csv')
        self.exit_level_2 = pd.read_csv('data/exit_level_2.csv')
        self.exit_level_3 = pd.read_csv('data/exit_level_3.csv')
        self.exit_level_4 = pd.read_csv('data/exit_level_4.csv')
        self.los_ln_mu = pd.read_csv('data/los_ln_mu.csv')
        self.los_ln_stdev = pd.read_csv('data/los_ln_stdev.csv')
        self.los_ln_mu.set_index('Category', inplace=True)
        self.los_ln_stdev.set_index('Category', inplace=True)
        self.time_df = pd.read_csv('data/travel_matrix_minutes.csv', low_memory=False)
        self.time_df.set_index('LSOA', inplace=True)
        self.time_df = self.time_df.apply(pd.to_numeric, errors='coerce')

        self.interhospital_distance_df = pd.read_csv('data/inter_hospital_d.csv')
        self.interhospital_distance_df.set_index('Hospital', inplace=True)
        self.interhospital_distance_df = self.interhospital_distance_df.apply(pd.to_numeric,
                                                                              errors='coerce')

        self.interhospital_time_df = pd.read_csv('data/inter_hospital_t.csv')
        self.interhospital_time_df.set_index('Hospital', inplace=True)
        self.interhospital_time_df = self.interhospital_time_df.apply(pd.to_numeric,
                                                                      errors='coerce')

        print('Loaded distance matrix size: ', self.time_df.shape)
        self.hospital_info_df = pd.read_csv('data/hospital_info.csv')
        print('Loaded hospital info size: ', self.hospital_info_df.shape)
        self.lsoa_demand = pd.read_csv('data/predicted_neonatal_demand_by_lsoa.csv')
        self.lsoa_demand.set_index('LSOA', inplace=True)
        print('Loaded LSOA demand size: ', self.lsoa_demand.shape)
        self.hospitals = list(self.hospital_info_df['hospital_postcode'])

        # Shorten for testing code
        if self.truncate:
            self.time_df = self.time_df.head(1000)
            self.lsoa_demand = self.lsoa_demand.head(1000)

    def find_order_of_hospitals_by_closeness(self):
        print('\nRanking hospitals by closeness to each LSOA...')
        closest_hospital_order_list = []
        closest_hospital_distance_list = []
        LSOA = list(self.time_df.index)

        for row_index, row in self.time_df.iterrows():
            row.sort_values(inplace=True)
            hospital_order = list(row.index)
            hospital_distance = row.values
            closest_hospital_order_list.append(hospital_order)
            closest_hospital_distance_list.append(hospital_distance)

        self.closest_hospital_order = pd.DataFrame(closest_hospital_order_list, index=LSOA)
        self.closest_hospital_distance = pd.DataFrame(closest_hospital_distance_list, index=LSOA)
        print('Closest hospital list size: ', self.closest_hospital_order.shape)
        print('Closest hospital distances/times size: ', self.closest_hospital_distance.shape)

    def order_with_home_network_first(self):
        """
        This matrix is based on the closest_hospital_order_matrix.
        It creates a dataframe of hospital and network (from full hospital details).
        It identifies the closest hospital and looks up the network for that hospital.
        It creates two lists: one of hospitals in the home network and one of other hospitals.
        It then takes the home network hospitals from the closest_hospital_order_matrix,
        maintaining the order in closest_hospital_order_matrix. It repeats the same for the non-home
        network hospitals and then combines the two together.
        It generates a new dataframe for ordered hospitals with home network hospitals first
        """
        lsoa_list = []
        closest_hospital_list = []
        print('\nCreating hospital search order list with home network first...')
        self.network_lookup = self.hospital_info_df[['hospital_postcode', 'network']]
        self.network_lookup.set_index(['hospital_postcode'], inplace=True)
        for row_index, row in self.closest_hospital_order.iterrows():
            home_network = self.network_lookup.loc[row[0]].item()
            hospitals_in_same_network = self.network_lookup.loc[
                self.network_lookup['network'] == home_network]
            list_hospitals_in_same_network = list(hospitals_in_same_network.index)
            hospitals_in_other_network = self.network_lookup.loc[
                self.network_lookup['network'] != home_network]
            list_hospitals_in_other_network = list(hospitals_in_other_network.index)
            ordered_hospitals_in_same_network = row.loc[row.isin(list_hospitals_in_same_network)]
            ordered_hospitals_in_other_network = row.loc[row.isin(list_hospitals_in_other_network)]
            ordered_hospitals_by_network = ordered_hospitals_in_same_network.append(
                ordered_hospitals_in_other_network)
            lsoa_list += [row_index]
            closest_hospital_list += [list(ordered_hospitals_by_network.values)]
        self.ordered_hospital_by_network = pd.DataFrame(closest_hospital_list, index=lsoa_list)

    def set_up_entry_matrix(self):
        self.entry_point.set_index('Category', inplace=True)
        self.entry_matrix = np.zeros((7, 6))
        self.entry_matrix[:, :] = self.entry_point.values / 100  # convert % to fraction
        # del self.entry_point

    def set_up_fetus_number_matrix(self):
        self.fetuses_table.set_index('Category', inplace=True)
        self.fetuses_matrix = np.zeros((6, 5))
        self.fetuses_matrix[:, :] = self.fetuses_table.values / 100  # convert % to fraction
        del self.fetuses_table

    def set_up_transition_probability_matrix(self):
        """3D array. Dimensions:
        1. Level moving from
        2. Infant category
        3. Level moving to
        Scalar value is probability (0-1) of transition
        Levels are from 0 (surgery) to 5 (exit)"""

        self.transition_matrix = np.zeros((5, 7, 6))

        self.exit_surgery = pd.read_csv('data/exit_surgery.csv')
        self.exit_level_1 = pd.read_csv('data/exit_level_1.csv')
        self.exit_level_2 = pd.read_csv('data/exit_level_2.csv')
        self.exit_level_3 = pd.read_csv('data/exit_level_3.csv')
        self.exit_level_4 = pd.read_csv('data/exit_level_4.csv')

        # Set index column, so that all remaining data is numerical
        self.exit_surgery.set_index('Category', inplace=True)
        self.exit_level_1.set_index('Category', inplace=True)
        self.exit_level_2.set_index('Category', inplace=True)
        self.exit_level_3.set_index('Category', inplace=True)
        self.exit_level_4.set_index('Category', inplace=True)

        # Set transition matrix values as fractional probability
        self.transition_matrix[0, :, :] = self.exit_surgery.values / 100
        self.transition_matrix[1, :, :] = self.exit_level_1.values / 100
        self.transition_matrix[2, :, :] = self.exit_level_2.values / 100
        self.transition_matrix[3, :, :] = self.exit_level_3.values / 100
        self.transition_matrix[4, :, :] = self.exit_level_4.values / 100

        # Remove loaded data
        del self.exit_surgery
        del self.exit_level_1
        del self.exit_level_2
        del self.exit_level_3
        del self.exit_level_4
