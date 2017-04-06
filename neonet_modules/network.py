import pandas as pd


class Network:
    """Network class holds capacity and utilisation of all hospitals"""

    def __init__(self, hospitals):
        self.status = pd.DataFrame()
        self.status['hospital'] = hospitals
        self.status.set_index('hospital', inplace=True)
        self.status['nursing_capacity'] = 2
        self.status['current_workload'] = 0.0
        self.status['current_surgery'] = 0
        self.status['current_level_1'] = 0
        self.status['current_level_2'] = 0
        self.status['current_level_3'] = 0
        self.status['current_level_4'] =0
        self.status['all_infants'] = 0
        self.admissions = 0
        self.bed_count = 0
        self.patients = {}
        self.displaced_patients_ids = []
        self.deliveries= 0
