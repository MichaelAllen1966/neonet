National neonatal simulation
============================


Requirements
------------

Requires Python 3.6 or later


Data sources
------------

Location of mother by LSOA
Raw neonatal demand from Badger (2015-2016)
Births from HES (2015-2016)
Road Travel times and distances from Maptitude/MP-MileCharter 2016
Travel times for LSOA based on postoce closest to populated-weighted centroid
Neonatal Unit designation from NNAP 2015
Index of Multiple Deprivation (IMD: https://www.gov.uk/government/statistics/english-indices-of-deprivation-2015)
Demand in model based on multiple regression of neonatal demand vs births + IMD

Description
-----------

Model identifies closest Surgical, NICU, HDU and SCU to mother's LSOA.
Model does not yet include Operational Network Boundaries.
