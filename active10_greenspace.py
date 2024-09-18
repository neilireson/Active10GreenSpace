import openpyxl
import pandas as pd
import numpy as np

# Define the file path
# input_file = "C:\\Users\\roych\\OneDrive\\Desktop\\FINAL1.xlsx"
# output_file = "C:\\Users\\roych\\OneDrive\\Desktop\\Active10_Greenspace_Steps.csv"

# input_file = "/data/active10/user-steps-locations-lsoa-20240521.csv.gz"
input_file = "/Users/nsi/Downloads/FINAL1.xlsx"
output_file = "/Users/nsi/Downloads/Active10_Greenspace_Steps.csv"
min_step_threshold = 500

# Read the Excel file
print('Reading the file: ' + input_file)
if input_file.endswith('.xlsx'):
    df = pd.read_excel(input_file, header=[0, 1], index_col=0)
else: # this is untested, need to add header rows
    df = pd.read_csv(input_file, header=[0, 1], index_col=0, compression='infer')

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

# Replace zeros with NaN in all columns to ignore them in the median calculation
df.replace(0, np.nan, inplace=True)

# Display the first few rows of the DataFrame
print(df.head())


# FUNCTIONS

def get_daily_steps(df, columns, min_step_threshold=0):
    # Select the columns to be included
    select = df.columns.get_level_values(1).isin(columns)
    # get the selected column steps
    steps = df.loc[:, select]
    # get the sum of the daily values
    steps = steps.groupby(level=0, axis=1).sum()
    # replace zero values with NaN so they are ignored
    steps.replace(0, np.nan, inplace=True)
    print(steps.head())

    # Remove days (set to NaN) with fewer steps than min_step_threshold
    steps = steps.mask(steps < min_step_threshold)
    return steps


def get_median_daily_steps(steps, col_name):
    # get the median steps, ignoring NaN (i.e. zero values)
    median_steps = steps.median(axis=1, skipna=True)
    median_steps = median_steps.to_frame().reset_index()
    median_steps.columns = ['Userid', col_name]
    print(median_steps.head())
    return median_steps


def get_day_count(steps, col_name):
    # Replace NaN with zeros to count days
    steps.replace(np.nan, 0, inplace=True)
    # count all non-zero values
    day_count = steps.astype(bool).sum(axis=1)
    day_count = day_count.to_frame().reset_index()
    day_count.columns = ['Userid', col_name]
    print(day_count.head())
    return day_count


# CALCULATE VALUE FOR ALL STEPS

# Select only steps columns for each day
all_steps = df.xs('steps', axis=1, level=1, drop_level=False)
print(all_steps.head())

# Remove days with less than 500 steps
all_steps = all_steps.mask(all_steps < min_step_threshold)

# calculate the median of the daily steps
median_all_steps = get_median_daily_steps(all_steps, 'All_Steps')
all_day_count = get_day_count(all_steps, 'All_Days')

# CALCULATE VALUE FOR ALL WALKING STEPS (CADENCE >= 60)

all_walking = get_daily_steps(df, all_walking_columns, min_step_threshold)
median_all_walking = get_median_daily_steps(all_walking, 'Walking_Steps')
all_walking_day_count = get_day_count(all_walking, 'Walking_Days')

# CALCULATE VALUE FOR ALL ACTIVE WALKING STEPS (CADENCE >= 90)

active_walking = get_daily_steps(df, active_walking_columns, min_step_threshold)
median_active_walking = get_median_daily_steps(active_walking, 'Active_Steps')
active_walking_day_count = get_day_count(active_walking, 'Active_Days')

# MERGE ALL DATA

merged = pd.merge(all_day_count, all_walking_day_count, on='Userid', how='left')
merged = pd.merge(merged, active_walking_day_count, on='Userid', how='left')
merged = pd.merge(merged, median_all_steps, on='Userid', how='left')
merged = pd.merge(merged, median_all_walking, on='Userid', how='left')
merged = pd.merge(merged, median_active_walking, on='Userid', how='left')
print(merged.head().to_string())

df = df.drop(base_column_names, axis=1, level=1)
df.columns = df.columns.get_level_values(1)
df = df.reset_index()
df.columns = ['Userid', 'countyCode', 'censusArea']
df = pd.merge(df, merged, on='Userid', how='left')
print(df.head(10).to_string())

# Replace NaN with zeros
df.replace(np.nan, 0, inplace=True)

print("Writing results to file: " + output_file)
df.to_csv(output_file, index=False)
