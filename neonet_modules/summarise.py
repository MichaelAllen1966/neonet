"""National neonatal demand and capacity model
*** Requires Python 3.6 or greater***

Class to describe data loading

Version 170528

(c)2017 Michael Allen 
This code is distributed under GNU GPL2
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
For info contact michael.allen1966@gmail.com
"""

import pandas as pd
import numpy as np


class Summarise:
    def __init__(self, audit, output_folder):
        # Summarise general audit
        general_audit = pd.read_csv(output_folder + '/general_day_audit.csv')
        print('Summarising general audit')
        df_general = pd.DataFrame()
        general_by_year = general_audit.groupby('year').mean()
        df_general['mean'] = general_by_year.mean()
        df_general['std'] = general_by_year.std()
        df_general['count'] = general_by_year.count()
        df_general['10%'] = general_by_year.quantile(0.1)
        df_general['25%'] = general_by_year.quantile(0.25)
        df_general['50%'] = general_by_year.quantile(0.5)
        df_general['75%'] = general_by_year.quantile(0.75)
        df_general['90%'] = general_by_year.quantile(0.9)
        df_general.to_csv(output_folder + '/summary_general.csv')
        del df_general
        del general_audit
        del general_by_year

        # Save transfers and no bed
        df_transfers = pd.Series()
        df_transfers['transfers'] = audit.transfers
        df_transfers['transfer_distance'] = audit.total_transfer_distance
        df_transfers['transfer_time'] = audit.total_transfer_time
        df_transfers['episodes_no_bed'] = audit.episodes_with_no_bed_found
        df_transfers['los_no_bed'] = audit.total_episodes_length_with_no_bed_found
        df_transfers.to_csv(output_folder + '/transfers_and_no_bed.csv')
        del df_transfers

        # Summarise patient log
        print('Summarising patient log')
        patient_log = pd.read_csv(output_folder + '/patient_log.csv')
        df_patient_log = pd.DataFrame()
        patient_log_by_year = patient_log.groupby('year').mean()
        df_patient_log['mean'] = patient_log_by_year.mean()
        df_patient_log['std'] = patient_log_by_year.std()
        df_patient_log['count'] = patient_log_by_year.count()
        df_patient_log['10%'] = patient_log_by_year.quantile(0.1)
        df_patient_log['25%'] = patient_log_by_year.quantile(0.25)
        df_patient_log['50%'] = patient_log_by_year.quantile(0.5)
        df_patient_log['75%'] = patient_log_by_year.quantile(0.75)
        df_patient_log['90%'] = patient_log_by_year.quantile(0.9)
        df_patient_log.to_csv(output_folder + '/summary_patient_log.csv')
        del df_patient_log
        del patient_log
        del patient_log_by_year

        # Summarise patient
        print('Summarising patient audit')
        patient_audit = pd.read_csv(output_folder + '/patient_audit.csv')
        df_patient_audit = pd.DataFrame()
        patient_audit_by_year = patient_audit.groupby('year').mean()
        df_patient_audit['mean'] = patient_audit_by_year.mean()
        df_patient_audit['std'] = patient_audit_by_year.std()
        df_patient_audit['count'] = patient_audit_by_year.count()
        df_patient_audit['10%'] = patient_audit_by_year.quantile(0.1)
        df_patient_audit['25%'] = patient_audit_by_year.quantile(0.25)
        df_patient_audit['50%'] = patient_audit_by_year.quantile(0.5)
        df_patient_audit['75%'] = patient_audit_by_year.quantile(0.75)
        df_patient_audit['90%'] = patient_audit_by_year.quantile(0.9)
        df_patient_audit.to_csv(output_folder + '/summary_patient_audit.csv')
        del patient_audit
        del df_patient_audit
        del patient_audit_by_year

        # Summarise hospital audit
        print('Summarising hospital audit')
        hospital_day_audit = pd.read_csv(output_folder + '/hospital_day_audit.csv')
        workload_percentile_by_year = pd.DataFrame()
        # Sum workloads at different percentiles (e.g. 50 is calculate median workload at each
        # hospital and sum)
        for i in [50, 75, 80, 85, 90, 95, 99]:
            pivot = hospital_day_audit.pivot_table(index='hospital', columns='year',
                                                   values='current_workload',
                                                   aggfunc=lambda x: np.percentile(x, i))
            workload_percentile_by_year[i] = pivot.sum()

        total_nurse_workload = pd.DataFrame()
        total_nurse_workload['mean'] = workload_percentile_by_year.mean()
        total_nurse_workload['stdv'] = workload_percentile_by_year.std()
        total_nurse_workload['0.1'] = workload_percentile_by_year.quantile(0.1)
        total_nurse_workload['0.25'] = workload_percentile_by_year.quantile(0.25)
        total_nurse_workload['0.50'] = workload_percentile_by_year.quantile(0.50)
        total_nurse_workload['0.75'] = workload_percentile_by_year.quantile(0.75)
        total_nurse_workload['0.90'] = workload_percentile_by_year.quantile(0.90)
        total_nurse_workload.to_csv(output_folder + '/summary_nurse_workload.csv')
        del hospital_day_audit
        del workload_percentile_by_year
        del pivot
        del total_nurse_workload

        # Summarise hospital by day
        hospital_day_audit = pd.read_csv('hospital_day_audit.csv')

        for item in ['current_workload', 'current_surgery', 'current_level_1', 'current_level_2',
                     'current_level_3', 'current_level_4', 'all_infant']:
            pivot = hospital_day_audit.pivot_table(index='day', columns='hospital', values=item)
            file_name = '/hospital_pivot_by_day_' + item + '.csv'
            pivot.to_csv(output_folder + file_name)

            # pivot=hospital_day_audit.pivot_table(index='hospital',columns='year',values='current_workload',aggfunc=lambda x: np.percentile(x, 0.5))
