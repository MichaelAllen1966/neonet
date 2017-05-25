"""National neonatal demand and capacity model
*** Requires Python 3.6 or greater***

Version 170501

(c)2017 Michael Allen 
This code is distributed under GNU GPL2
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
For info contact michael.allen1966@gmail.com
"""

# todo add in some __str__ to classes to return summary info
# todo fix patient log number of transfers not being recorded (done - to be checked)

import simpy
import random
import time
import numpy as np
import copy

# Import classes from modules
from neonet_modules.patient import Patient
from neonet_modules.data import Data
from neonet_modules.network import Network
from neonet_modules.audit import Audit
from neonet_modules.summary import Summarise

class Glob_vars:  # misc global data
    truncate_data = False  # use True for code testing only: results will not be correct
    warm_up = 366
    sim_duration = 365  # sim duration after warm-up
    sim_duration += warm_up
    arrivals_per_day = 165
    interarrival_time = 1 / (arrivals_per_day)  # 1 /arrivals per day
    nurse_for_care_level = [1, 1, 0.5, 0.25, 0.125]  # Nurse requirements for surgery --> TC
    allowed_overload_fraction = 1.5  # allowed fraction of BAPM guidelines allowed
    day = 0
    year = 1
    output_folder = 'output/test3'
    network_count_columns = ['current_surgery',
                             'current_level_1',
                             'current_level_2',
                             'current_level_3',
                             'current_level_4']


class Model:
    def __init__(self):
        """ Set up simulation environment"""
        self.env = simpy.Environment()

    def day_audit_process(self):
        """Trigger audits each day. Starts after warm up period."""
        # Delay of woarm up period before first audit
        yield self.env.timeout(Glob_vars.warm_up)

        # Daily audits
        while True:
            self.audit.perform_daily_audit(Glob_vars.day, Glob_vars.year, self.network,
                                           Glob_vars.output_folder)
            # Trigger next audit in 1 day
            yield self.env.timeout(1)

    def day_count_process(self):
        """Day count. Increment each day. Also calculate year"""
        while True:
            yield self.env.timeout(1)
            Glob_vars.day += 1
            Glob_vars.year = int(Glob_vars.day / 365) + 1
            print('Day: %d' % Glob_vars.day)

    def find_hospital_bed(self, p):
        # set required care level and nurses
        _required_care_level = p.required_care_level_current
        _required_nurse_resources = Glob_vars.nurse_for_care_level[_required_care_level]

        # set required unit type
        # default to care level (0=surg --> 4 = TC), 
        # but amend for short Los at a particular care level
        p.required_unit_type = _required_care_level

        # If level of care = IC but LoS <2 days then allow a HDU unit to care for infant
        if _required_care_level == 1:
            if p.los[1] < 2:
                p.required_unit_type = 2

        # If level of care = HD but LoS <2 days then allow a SCU unit to care for infant
        if _required_care_level == 2:
            if p.los[2] < 2:
                p.required_unit_type = 3

        # Filter hospital list to appropriate level
        _header_list = ['neonatal_surg',
                        'neonatal_level_1',
                        'neonatal_level_2',
                        'neonatal_level_3',
                        'neonatal_level_4']
        _check_column_name = _header_list[p.required_unit_type]
        _filtered_hospitals = (
        self.data.hospital_info_df.loc[self.data.hospital_info_df[_check_column_name] == 1])
        _hospital_search_list = list(_filtered_hospitals['hospital_postcode'])

        # Generate list of all hospitals (closest first) depedning on LSOA
        _lsoa = p.lsoa
        _ordered_list_for_lsoa = list(self.data.ordered_hospital_by_network.loc[_lsoa, :])

        # Initialise parameters
        _bed_found = 0
        _closest_appropriate_hospital_identified = False

        # Record 'birth hospital' as closest hospital with any level of neonatal unit
        if p.birth_hospital == 'None':
            p.birth_hospital = _ordered_list_for_lsoa[0]
            _hospital_details = self.data.hospital_info_df[
                self.data.hospital_info_df['hospital_postcode'] == _ordered_list_for_lsoa[0]]
            p.home_network = _hospital_details['network'].item()  # network extracted as dictionary

        # If this is first spell record 'previous hospital' as birth hospital
        # This is used for transfer if 1st level of care is greater than available in bith hospital
        if p.spells == 1:
            p.previous_hospital = p.birth_hospital

        # Loop through hospital list looking for unit with:
        #  1. Appropriate level
        #  2. Spare nurse capacity
        for hospital in _ordered_list_for_lsoa:
            # Check if hospital is in list able to provide required care level
            if hospital in _hospital_search_list:

                # Record first appropraite hospital in list as closest
                if _closest_appropriate_hospital_identified == False:
                    p.closest_appropriate_hospital = hospital
                    _closest_appropriate_hospital_identified = True

                # Calculate current nursing capacity in hospital being inspected (with allowed overloading)
                _hospital_capacity = ((self.network.status['nursing_capacity'].loc[hospital] *
                                       Glob_vars.allowed_overload_fraction) -
                                      self.network.status['current_workload'].loc[hospital])

                # Check if hospital has sufficient nursing capacity
                if _hospital_capacity >= _required_nurse_resources:
                    ## BED FOUND ##
                    _bed_found = 1

                    # Adjust hospital nursing resources used
                    _new_value = self.network.status.loc[hospital][
                                     'current_workload'] + _required_nurse_resources
                    self.network.status.set_value(hospital, 'current_workload', _new_value)

                    # Adjust hospital care level count
                    network_col = Glob_vars.network_count_columns[p.required_care_level_current]
                    _new_value = self.network.status.loc[hospital][network_col] + 1
                    self.network.status.set_value(hospital, network_col, _new_value)

                    # Adjust hospital total infant count
                    _new_value = self.network.status.loc[hospital]['all_infants'] + 1
                    self.network.status.set_value(hospital, 'all_infants', _new_value)

                    # Set hospital on patient object
                    p.current_hospital = hospital
                    p.current_network = self.data.network_lookup.loc[p.current_hospital].item()
                    p.in_home_network = 1 if p.current_network == p.home_network else 0

                    # Add patient object to network patients dictionary
                    self.network.patients[p.id] = p  # add patient to dictionary of patients

                    # Calculate distance from home
                    p.distance_from_home = self.data.travel_tuples[(p.lsoa, hospital)]

                    # Look to see if new hopsital is different from last
                    if p.current_hospital != p.previous_hospital:
                        # Transfer required
                        self.transfer_patient(p.previous_hospital, p.current_hospital, p)

                    # Check if patient is in the closest appropriate unit
                    if p.closest_appropriate_hospital == p.current_hospital:
                        p.in_closest_appropriate_hospital = True
                    else:
                        p.in_closest_appropriate_hospital = False
                        # Add to list of displaced patients
                        self.network.displaced_patients_ids.append(p.id)

                    # Record selected hospital as previous hospital (used to look for change in location on next spell)
                    p.previous_hospital = p.current_hospital

                    # Return
                    return _bed_found

        return _bed_found

    def model_run(self):
        # Load data
        self.start_time = time.time()
        self.data = Data(truncate=Glob_vars.truncate_data)

        # Set up network status dataframe
        self.network = Network(self.data.hospitals, list(self.data.hospital_info_df[
                                                             'nurse_capacity']))

        # Set up audit
        self.audit = Audit()

        # Set up output files

        self.audit.set_up_output(Glob_vars.output_folder)

        # Initialise model processes
        # Process fo rgenerating new patients
        self.env.process(self.new_admission_process())
        # Process for maintaining day count
        self.env.process(self.day_count_process())
        # Process for looking to relocate patients once per day
        self.env.process(self.relocate_displaced_process())
        # Process to run audits
        self.env.process(self.day_audit_process())

        # Run model
        self.env.run(until=Glob_vars.sim_duration)

        # Model end
        self.end_time = time.time()
        Summarise(Glob_vars.output_folder)
        print('\nEnd. Model run in %d seconds' % (self.end_time - self.start_time))

    def new_admission_process(self):
        while True:
            self.network.admissions += 1
            self.network.bed_count += 1
            self.network.deliveries += 1
            p = Patient(data=self.data, id=self.network.admissions,
                        delivery=self.network.deliveries,
                        time_in=self.env.now,
                        year=Glob_vars.year)
            p.set_care_requirements(self.data)
            self.network.patients[p.id] = p
            # self.spell = self.spell_gen_process(p)
            self.env.process(self.spell_gen_process(p))
            next_admission = np.random.exponential(Glob_vars.interarrival_time)
            # print('Next patient in %f3.2' %next_p)
            if p.fetuses > 1:  # Copy twins etc
                for extra_fetus in range(p.fetuses - 1):
                    # Twins are always same category, but actual lengths of stay are sampled separately
                    p2 = copy.deepcopy(p)
                    p2.category = p2.category_without_surgery  # does not duplicate surgery, resets to category before surgery
                    p2.set_care_requirements(self.data)
                    self.network.admissions += 1
                    self.network.bed_count += 1
                    p2.id = self.network.admissions
                    self.network.patients[p2.id] = p2
                    self.env.process(self.spell_gen_process(p2))
            yield self.env.timeout(next_admission)

    def relocate_displaced_process(self):
        yield self.env.timeout(1)
        while True:
            _new_displaced_list_ids = []
            for _displaced_patient_id in self.network.displaced_patients_ids:
                _displaced_patient = self.network.patients[_displaced_patient_id]
                # Check if capacity available in
                _required_nurse_resources = Glob_vars.nurse_for_care_level[
                    _displaced_patient.required_care_level_current]
                _closest_appropriate_hospital = _displaced_patient.closest_appropriate_hospital
                _capacity_at_closest_appropriate_hospital = (
                    (self.network.status['nursing_capacity'].loc[_closest_appropriate_hospital] *
                     Glob_vars.allowed_overload_fraction) -
                    self.network.status['current_workload'].loc[_closest_appropriate_hospital])

                if _capacity_at_closest_appropriate_hospital >= _required_nurse_resources:
                    # *** Capacity at closest appropraite unit now exists. Transfer patient ***
                    _current_hopsital = _displaced_patient.current_hospital

                    _transfer_to_hospital = _closest_appropriate_hospital

                    _displaced_patient._current_hopsital = _closest_appropriate_hospital
                    self.transfer_patient(_current_hopsital, _transfer_to_hospital,
                                          _displaced_patient)

                    _displaced_patient.previous_hospital = _current_hopsital

                    # Adjust hospital tracking

                    _old_hospital = _current_hopsital
                    _new_hospital = _closest_appropriate_hospital

                    # Remove nursing resources from 'old hospital'
                    _new_value = self.network.status.loc[_old_hospital][
                                     'current_workload'] - _required_nurse_resources
                    self.network.status.set_value(_old_hospital, 'current_workload', _new_value)

                    # Remove from old hospital care level count
                    _network_col = Glob_vars.network_count_columns[
                        _displaced_patient.required_care_level_current]
                    _new_value = self.network.status.loc[_old_hospital][_network_col] - 1
                    self.network.status.set_value(_old_hospital, _network_col, _new_value)

                    # Remove from old hospital all infants count
                    _new_value = self.network.status.loc[_old_hospital]['all_infants'] - 1
                    self.network.status.set_value(_old_hospital, 'all_infants', _new_value)

                    # Add to nursing resources from 'new hospital'
                    _new_value = self.network.status.loc[_new_hospital][
                                     'current_workload'] + _required_nurse_resources
                    self.network.status.set_value(_new_hospital, 'current_workload', _new_value)

                    # Add to new hospital care level count
                    _network_col = Glob_vars.network_count_columns[
                        _displaced_patient.required_care_level_current]
                    _new_value = self.network.status.loc[_new_hospital][_network_col] + 1
                    self.network.status.set_value(_new_hospital, _network_col, _new_value)

                    # Add to new hospital all infants count
                    _new_value = self.network.status.loc[_new_hospital]['all_infants'] + 1
                    self.network.status.set_value(_new_hospital, 'all_infants', _new_value)

                    # Update patient object distance from home and record now in closest appropriate hospital
                    _displaced_patient.distance_from_home = self.data.travel_tuples[
                        (_displaced_patient.lsoa, _closest_appropriate_hospital)]
                    _displaced_patient.in_closest_appropriate_hospital = True
                else:
                    # Patient not moved; a new list of patients not relocated is built
                    _new_displaced_list_ids.append(_displaced_patient.id)

            # create new displaces patient list
            self.network.displaced_patients_ids = copy.copy(_new_displaced_list_ids)

            # trigger while loop to resule in 1 day
            yield self.env.timeout(1)

    def spell_gen_process(self, p):  # patient event generator
        # do a while loop here to go through stages of care
        while p.complete == False:
            if p.use_levels[p.required_care_level_current]:
                p.spells += 1
                _bed_found = self.find_hospital_bed(p)
                # _required_care_level = p.required_care_level_current
                # _los_mu = p.los_ln_mu[0][_required_care_level]
                # _los_stdev = p.los_ln_stdev[0][_required_care_level]
                # _los = np.random.lognormal(_los_mu, _los_stdev)
                _los = p.los[p.required_care_level_current]
                if _bed_found == 1:
                    # Start spell and delay next step for length of stay (los)
                    yield self.env.timeout(_los)

                    # End of spell

                    # Adjust hospital tracking at end of spell

                    # Remove nurse workload
                    _required_nurse_resources = Glob_vars.nurse_for_care_level[
                        p.required_care_level_current]
                    _new_value = self.network.status['current_workload'].loc[
                                     p.current_hospital] - _required_nurse_resources
                    self.network.status.set_value(p.current_hospital, 'current_workload',
                                                  _new_value)

                    # Remove from care level tracking
                    _network_col = Glob_vars.network_count_columns[p.required_care_level_current]
                    _new_value = self.network.status.loc[p.current_hospital][_network_col] - 1
                    self.network.status.set_value(p.current_hospital, _network_col, _new_value)

                    # Remove from hospital all infants count
                    _new_value = self.network.status.loc[p.current_hospital]['all_infants'] - 1
                    self.network.status.set_value(p.current_hospital, 'all_infants', _new_value)

                    # remove from displaced patients if present
                    if p.id in self.network.displaced_patients_ids:
                        self.network.displaced_patients_ids.remove(p.id)
                else:
                    # No bed found. Model tracks missing episodes and LoS
                    print('No Bed found')
                    self.audit.episodes_with_no_bed_found += 1
                    self.audit.total_episodes_length_with_no_bed_found += _los
                    yield self.env.timeout(_los)
            p.required_care_level_current += 1
            if p.required_care_level_current == 5:
                p.complete = True
        self.network.bed_count -= 1
        p.time_out = self.env.now

        if self.env.now > Glob_vars.warm_up:
            self.audit.record_patient_log(p, Glob_vars.output_folder)

        del self.network.patients[p.id]
        del p

    def transfer_patient(self, from_hospital, to_hospital, p):
        _transfer_distance = self.data.interhospital_distance_tuples[
            (from_hospital, to_hospital)]
        _transfer_time = self.data.interhospital_time_tuples[(from_hospital, to_hospital)]
        self.audit.transfers += 1
        self.audit.total_transfer_distance += _transfer_distance
        self.audit.total_transfer_time += _transfer_time
        p.total_transfer_distance += _transfer_distance
        p.transfers += 1


def main():
    random.seed(1)  # remove number to have different random seed each time
    model = Model()
    model.model_run()


if __name__ == '__main__':
    main()
