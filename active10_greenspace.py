# DATA CLEANING

import openpyxl
import pandas as pd
import numpy as np

# Define the file path
input_file = "/Users/nsi/Downloads/FINAL1_Test.xlsx"
output_file = "/Users/nsi/Downloads/Active10_Greenspace_Steps.csv"

# Read the Excel file
print('Reading the file: ' + input_file)
df = pd.read_excel(input_file, header=[0, 1], index_col=0)

# Display the first few rows of the data
print(df.head())

# Select only users in Great Britain
df = df.loc[df[0]['countyCode'] == 'GBR']

# Define the base column names
base_column_names = [
    'date', 'firstStepTime', 'lastStepTime', 'steps',
    'stepCadence30', 'stepCadence60', 'stepCadence90',
    'stepCadence120', 'stepCadence150', 'stepCadence180',
    'stepCadence210', 'stepCadence240', 'stepCadence270',
    'stepCadence300', 'stepCadence>300'
]

# Columns for All_Walking calculation
all_walking_columns = [
    'stepCadence60', 'stepCadence90', 'stepCadence120',
    'stepCadence150', 'stepCadence180', 'stepCadence210',
    'stepCadence240', 'stepCadence270', 'stepCadence300',
    'stepCadence>300'
]

# Columns for Active_Walking calculation
active_walking_columns = [
    'stepCadence90', 'stepCadence120', 'stepCadence150',
    'stepCadence180', 'stepCadence210', 'stepCadence240',
    'stepCadence270', 'stepCadence300', 'stepCadence>300'
]

# DESCRIPTIVES

# Replace zeros with NaN in all columns to ignore them in the median calculation
df.replace(0, np.nan, inplace=True)

# Display the first few rows of the DataFrame
print(df.head())


# CALCULATE VALUE FOR ALL STEPS

# Select only steps columns for each day
all_steps = df.xs('steps', axis=1, level=1, drop_level=False)
print(all_steps.head())

# calculate the median of the daily steps
median_all_steps = all_steps.median(axis=1, skipna=True)
median_all_steps = median_all_steps.to_frame().reset_index()
median_all_steps.columns = ['Userid', 'All_Steps']
print(median_all_steps.head())

# Replace NaN with zeros to count days
all_steps.replace(np.nan, 0, inplace=True)
all_day_count = all_steps.astype(bool).sum(axis=1)
all_day_count = all_day_count.to_frame().reset_index()
all_day_count.columns = ['Userid', 'All_Days']
print(all_day_count.head())


# CALCULATE VALUE FOR ALL WALKING STEPS (CADENCE >= 60)

# Select only walking cadence (>=60) columns for each day
select_all_walking = df.columns.get_level_values(1).isin(all_walking_columns)
all_walking = df.loc[:, select_all_walking]
all_walking = all_walking.groupby(level=0, axis=1).sum()
all_walking.replace(0, np.nan, inplace=True)
print(all_walking.head())

# calculate the median of the daily walking steps
median_all_walking = all_walking.median(axis=1, skipna=True)
median_all_walking = median_all_walking.to_frame().reset_index()
median_all_walking.columns = ['Userid', 'Walking_Steps']
print(median_all_walking.head())

# Replace NaN with zeros to count days
all_walking.replace(np.nan, 0, inplace=True)
all_walking_day_count = all_walking.astype(bool).sum(axis=1)
all_walking_day_count = all_walking_day_count.to_frame().reset_index()
all_walking_day_count.columns = ['Userid', 'Walking_Days']
print(all_walking_day_count.head())


# CALCULATE VALUE FOR ALL ACTIVE WALKING STEPS (CADENCE >= 90)

# Select only active walking cadence (>=60) columns for each day
active_walking = df.loc[:, df.columns.get_level_values(1).isin(active_walking_columns)]
active_walking = active_walking.groupby(level=0, axis=1).sum()
active_walking.replace(0, np.nan, inplace=True)
print(active_walking.head())

# calculate the median of the daily active walking steps
median_active_walking = active_walking.median(axis=1, skipna=True)
median_active_walking = median_active_walking.to_frame().reset_index()
median_active_walking.columns = ['Userid', 'Active_Steps']
print(median_active_walking.head())

# Replace NaN with zeros to count days
active_walking.replace(np.nan, 0, inplace=True)
active_walking_day_count = active_walking.astype(bool).sum(axis=1)
active_walking_day_count = active_walking_day_count.to_frame().reset_index()
active_walking_day_count.columns = ['Userid', 'Active_Days']
print(active_walking_day_count.head())


# MERGE ALL DATA

df = df.drop(base_column_names, axis=1, level=1)
df.columns = df.columns.get_level_values(1)
df = df.reset_index()
df.columns = ['Userid', 'countyCode', 'censusArea']
print(df.head())

merged = pd.merge(all_day_count, median_all_steps, on='Userid', how='left')
merged = pd.merge(merged, median_all_walking, on='Userid', how='left')
merged = pd.merge(merged, median_active_walking, on='Userid', how='left')
print(merged.head())

df = pd.merge(df, merged, on='Userid', how='left')
print(df.head(10).to_string())

print("Writing results to file: " + output_file)
df.to_csv(output_file, index=False)

