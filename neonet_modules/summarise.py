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


class Summarise:
    def __init__(self, output_folder):
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
        df_hospital = pd.DataFrame()
        hospital_by_year = hospital_day_audit.groupby('year').mean()
        df_hospital['mean'] = hospital_day_audit.mean()
        df_hospital['std'] = hospital_day_audit.std()
        df_hospital['count'] = hospital_day_audit.count()
        df_hospital['10%'] = hospital_day_audit.quantile(0.1)
        df_hospital['25%'] = hospital_day_audit.quantile(0.25)
        df_hospital['50%'] = hospital_day_audit.quantile(0.5)
        df_hospital['75%'] = hospital_day_audit.quantile(0.75)
        df_hospital['90%'] = hospital_day_audit.quantile(0.9)
        df_hospital.to_csv(output_folder + '/summary_hospital.csv')
        del hospital_day_audit
        del df_hospital
        del hospital_by_year
