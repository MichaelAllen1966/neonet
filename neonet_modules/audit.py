"""National neonatal demand and capacity model
*** Requires Python 3.6 or greater***

Class to describe audits

Version 170501

(c)2017 Michael Allen 
This code is distributed under GNU GPL2
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
For info contact michael.allen1966@gmail.com
"""


import pandas as pd
import os
import csv
import time


# Todo add lengths of stay at each level and calaculate total length of stay from time in and time out

class Audit():
    def __init__(self):
        self.transfers = 0
        self.total_transfer_distance = 0
        self.total_transfer_time = 0
        self.episodes_with_no_bed_found = 0
        self.total_episodes_length_with_no_bed_found = 0

    def perform_daily_audit(self, day, year, network, output_folder):
        self.perform_general_audit(day, year, network, output_folder)
        self.perform_hospital_audit(day, year, network, output_folder)
        # Run patient audit every 10 days (default)
        if day % 10 == 0:
            self.perform_patient_audit(day, year, network, output_folder)

    def perform_general_audit(self, day, year, network, output_folder):
        data_list = []
        data_list.append(day)
        data_list.append(year)
        data_list.append(network.bed_count)  # all infants
        data_list.append(network.status['current_surgery'].sum())  # surgical infants
        data_list.append(network.status['current_level_1'].sum())  # L1 infants
        data_list.append(network.status['current_level_2'].sum())  # L2 infants
        data_list.append(network.status['current_level_3'].sum())  # L3 infants
        data_list.append(network.status['current_level_4'].sum())  # L4 infants
        data_list.append(network.status['current_workload'].sum())  # Nurse workload
        data_list.append(len(network.displaced_patients_ids))  # displaced infants

        my_csv = output_folder + '/general_day_audit.csv'
        with open(my_csv, "a") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow(data_list)

    def perform_hospital_audit(self, day, year, network, output_folder):
        df = network.status
        df['day'] = day
        df['year'] = year
        my_csv = output_folder + '/hospital_day_audit.csv'
        with open(my_csv, 'a') as f:
            df.to_csv(f, header=False)

    def perform_patient_audit(self, day, year, network, output_folder):
        my_csv = output_folder + '/patient_audit.csv'
        patients = []

        for key, p in network.patients.items():
            data_list = []
            data_list.append(day)
            data_list.append(year)
            data_list.append(p.id)
            data_list.append(p.delivery_id)
            data_list.append(p.lsoa)
            data_list.append(p.category[0])
            data_list.append(p.required_care_level_current)
            data_list.append(p.current_hospital)
            data_list.append(p.distance_from_home)
            data_list.append(p.fetuses)
            data_list.append(p.in_closest_appropriate_hospital)
            data_list.append(p.closest_appropriate_hospital)
            data_list.append(p.in_home_network)
            patients.append(data_list)

        with open(my_csv, "a") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerows(patients)

    def record_patient_log(self, p, output_folder):
        my_csv = output_folder + '/patient_log.csv'
        patient = []
        patient.append(p.time_in)
        patient.append(p.year)
        patient.append(p.birth_hospital)
        patient.append(p.category[0])
        patient.append(p.category_without_surgery[0])
        patient.append(p.delivery_id)
        patient.append(p.entry)
        patient.append(p.fetuses)
        patient.append(p.id)
        patient.append(p.lsoa)
        patient.append(p.spells)
        patient.append(p.transfers)
        patient.append(p.total_transfer_distance)

        # Add lengtos of stay for levels used
        for level in range(5):
            if p.use_levels[level]:
                patient.append(p.los[level])
            else:
                patient.append("")

        patient.append(p.time_out)
        patient.append(p.time_out - p.time_in)

        with open(my_csv, "a") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow(patient)

    def set_up_output(self, output_folder):
        # First check output folder exists. If not, make it.
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Set up general audit
        filename = output_folder + '/general_day_audit.csv'
        headers = ['day',
                   'year',
                   'all infants',
                   'surgery',
                   'level_1',
                   'level_2',
                   'level_3',
                   'level_4',
                   'nurse_workload',
                   'displaced']
        self.write_file(filename, headers)

        # Set up patient audit

        headers = ['day',
                   'year',
                   'patient_id',
                   'delivery_id',
                   'lsoa',
                   'infant_category',
                   'current_level_of_care',
                   'hospital',
                   'distance_from_home',
                   'fetuses',
                   'in_closest_suitable_unit',
                   'closest_suitable_unit',
                   'in_home_network']
        filename = output_folder + '/patient_audit.csv'
        self.write_file(filename, headers)

        # Set up patient log

        headers = ['time_in',
                   'year',
                   'birth_hospital',
                   'category',
                   'category_without_surgery',
                   'delivery_id',
                   'entry',
                   'fetuses',
                   'id',
                   'lsoa',
                   'spells',
                   'transfers',
                   'total_transfer_distance',
                   'los_surgery',
                   'los_level_1',
                   'los_level_2',
                   'los_level_3',
                   'los_level_4',
                   'time_out',
                   'total_los']

        filename = output_folder + '/patient_log.csv'
        self.write_file(filename, headers)

        # Set up hospital audit

        headers = ['hospital',
                   'nursing_capacity',
                   'current_workload',
                   'current_surgery',
                   'current_level_1',
                   'current_level_2',
                   'current_level_3',
                   'current_level_4',
                   'all_infant',
                   'day',
                   'year']

        filename = output_folder + '/hospital_day_audit.csv'
        self.write_file(filename, headers)

    def write_file(self, filename, headers):
        with open(filename, "w") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow(headers)
