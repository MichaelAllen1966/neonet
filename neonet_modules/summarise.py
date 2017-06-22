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

        # then count patients more than 30, 45 and 60 min from home
        results=pd.Series()
        results['greater_than_30']=(patient_audit['distance_from_home']>30).mean()
        results['greater_than_45']=(patient_audit['distance_from_home']>45).mean()
        results['greater_than_60']=(patient_audit['distance_from_home']>60).mean()
        results.to_csv(output_folder + '/travel_greater_than_30_45_60.csv')

        del patient_audit
        del df_patient_audit
        del patient_audit_by_year
        del results

        # Summarise hospital audit
        print('Summarising hospital audit')
        filename = output_folder + '/hospital_day_audit.csv'
        hosp_audit = pd.read_csv(output_folder + '/hospital_day_audit.csv')
        workload_percentile_by_year = pd.DataFrame()
        # Sum workloads at different percentiles (e.g. 50 is calculate median workload at each
        # hospital and sum)
        for i in [50, 75, 80, 85, 90, 95, 99]:
            pivot = hosp_audit.pivot_table(index='hospital', columns='year',
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
        del hosp_audit
        del workload_percentile_by_year
        del pivot
        del total_nurse_workload

        # Summarise hospital by day
        hospital_day_audit = pd.read_csv(output_folder + '/hospital_day_audit.csv')

        for item in ['current_workload', 'current_surgery', 'current_level_1', 'current_level_2',
                     'current_level_3', 'current_level_4', 'all_infant']:
            pivot = hospital_day_audit.pivot_table(index='day', columns='hospital', values=item)
            file_name = '/hospital_pivot_by_day_' + item + '.csv'
            pivot.to_csv(output_folder + file_name)

        # Stats for each hospital
        file_list = ['hospital_pivot_by_day_current_surgery.csv',
                     'hospital_pivot_by_day_current_level_1.csv',
                     'hospital_pivot_by_day_current_level_2.csv',
                     'hospital_pivot_by_day_current_level_3.csv',
                     'hospital_pivot_by_day_current_level_4.csv',
                     'hospital_pivot_by_day_all_infant.csv',
                     'hospital_pivot_by_day_current_workload.csv']
        column_names = ['surgery', 'level_1', 'level_2', 'level_3', 'level_4', 'infants',
                        'workload']

        summary_df = pd.DataFrame()

        for i in range(7):
            file_name = output_folder + '/' + file_list[i]
            data = pd.read_csv(file_name)
            del data['day']
            summary_df[column_names[i] + '_mean'] = data.mean()
            summary_df[column_names[i] + '_stdev'] = data.std()
            summary_df[column_names[i] + '_10_percentile'] = data.quantile(0.1)
            summary_df[column_names[i] + '_25_percentile'] = data.quantile(0.25)
            summary_df[column_names[i] + '_50_percentile'] = data.quantile(0.5)
            summary_df[column_names[i] + '_75_percentile'] = data.quantile(0.75)
            summary_df[column_names[i] + '_90_percentile'] = data.quantile(0.90)

        summary_df.to_csv(output_folder + '/summary_by_hospital.csv')
