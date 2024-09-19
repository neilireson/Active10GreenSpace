import openpyxl # required for Excel
import pandas as pd
import numpy as np
from tqdm import tqdm

# Define the file path
# input_file = "C:\\Users\\roych\\OneDrive\\Desktop\\FINAL1.xlsx"
# output_file = "C:\\Users\\roych\\OneDrive\\Desktop\\Active10_Greenspace_Steps.csv"

# input_file = "/data/active10/user-steps-locations-lsoa-20240521.csv.gz"
input_file = "/Users/nsi/Downloads/FINAL1.xlsx"
output_file = "/Users/nsi/Downloads/Active10_Greenspace_Steps.csv"
min_all_step_threshold = 500
min_walking_step_threshold = 1
min_active_step_threshold = 1

# Read the Excel file
print('Reading the file: ' + input_file)
if input_file.endswith('.xlsx'):
    df = pd.read_excel(input_file, header=[0, 1], index_col=0)
else:  # TODO this is untested, need to add header rows
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


# FUNCTIONS start

def get_daily_steps(df, columns, min_step_threshold=1):
    # hack to remove days, where steps are < min_all_step_threshold
    # add steps to columns
    if 'steps' not in columns:
        columns.append('steps')

    # Select the columns to be included
    select = df.columns.get_level_values(1).isin(columns)
    # get the selected column steps
    steps = df.loc[:, select]
    # Replace NaN with zeros to count valid days
    steps.replace(np.nan, 0, inplace=True)

    # This is slow: iterate through all the values
    for i in tqdm(set(steps.index)):
        # for each user
        user_df = steps.loc[i].reset_index()
        # iterate through user rows
        for index, row in user_df.iterrows():
            # if row is steps values then change value to MaN if steps are < min_all_step_threshold, otherwise zero
            if row.values[1] == 'steps':
                user_id = row.index.values[2]
                col0 = row.values[0]
                col1 = row.values[1]
                if row.values[2] < min_all_step_threshold:
                    steps.loc[user_id, (col0, col1)] = np.nan
                else:
                    steps.loc[user_id, (col0, col1)] = 0

    # get the sum of the daily values, where min_count means that if the steps are NaN then sum is also NaN
    steps = steps.groupby(level=0, axis=1, dropna=False).sum(min_count=len(columns))

    # Remove days (set to NaN) with fewer steps than min_step_threshold
    steps = steps.mask(steps < min_step_threshold)

    print(steps.head())
    return steps


def get_average_daily_steps(average_func, steps, col_name):
    # get the median or mean steps, ignoring NaN (i.e. zero values)
    if (average_func == "median"):
        average_steps = steps.median(axis=1, skipna=True)
    elif (average_func == "mean"):
        average_steps = steps.mean(axis=1, skipna=True).round(2)
    else:
        raise SystemExit('Unrecognised average func: ' + average_func)

    average_steps = average_steps.to_frame().reset_index()
    average_steps.columns = ['Userid', col_name]
    print(average_steps.head())
    return average_steps


def get_day_count(steps, col_name):
    # Replace NaN with zeros to count days
    steps.replace(np.nan, 0, inplace=True)
    # count all non-zero values
    day_count = steps.astype(bool).sum(axis=1)
    day_count = day_count.to_frame().reset_index()
    day_count.columns = ['Userid', col_name]
    print(day_count.head())
    return day_count

# FUNCTIONS end

print(df.head())

# Replace zeros with NaN in all columns to ignore them in the median calculation
df.replace(0, np.nan, inplace=True)

print('Calculating values for all steps...')

# Select only steps columns for each day
all_steps = df.xs('steps', axis=1, level=1, drop_level=False)
print(all_steps.head())

# Remove days with less than 500 steps
all_steps = all_steps.mask(all_steps < min_all_step_threshold)

# calculate the average of the daily steps
median_all_steps = get_average_daily_steps('median', all_steps, 'Median_All_Steps')
mean_all_steps = get_average_daily_steps('mean', all_steps, 'Mean_All_Steps')
all_day_count = get_day_count(all_steps, 'All_Days')

print('Calculating values for all walking steps (cadence >= 60)...')

all_walking = get_daily_steps(df, all_walking_columns, min_walking_step_threshold)
median_all_walking = get_average_daily_steps('median', all_walking, 'Median_Walking_Steps')
mean_all_walking = get_average_daily_steps('mean', all_walking, 'Mean_Walking_Steps')
all_walking_day_count = get_day_count(all_walking, 'Walking_Days')

print('Calculate value for all active walking steps (cadence >= 90)')

active_walking = get_daily_steps(df, active_walking_columns, min_active_step_threshold)
median_active_walking = get_average_daily_steps('median', active_walking, 'Median_Active_Steps')
mean_active_walking = get_average_daily_steps('mean', active_walking, 'Mean_Active_Steps')
active_walking_day_count = get_day_count(active_walking, 'Active_Days')

print('Merging data')

merged = pd.merge(all_day_count, all_walking_day_count, on='Userid', how='left')
merged = pd.merge(merged, active_walking_day_count, on='Userid', how='left')
merged = pd.merge(merged, median_all_steps, on='Userid', how='left')
merged = pd.merge(merged, mean_all_steps, on='Userid', how='left')
merged = pd.merge(merged, median_all_walking, on='Userid', how='left')
merged = pd.merge(merged, mean_all_walking, on='Userid', how='left')
merged = pd.merge(merged, median_active_walking, on='Userid', how='left')
merged = pd.merge(merged, mean_active_walking, on='Userid', how='left')
print(merged.head().to_string())

# remove columns that are not required in output
df = df.drop(base_column_names, axis=1, level=1)
# remove day multiindex
df.columns = df.columns.get_level_values(1)
df = df.reset_index()
df.columns = ['Userid', 'countyCode', 'censusArea']
# merge all the columns
df = pd.merge(df, merged, on='Userid', how='left')
print(df.head(10).to_string())

# Replace NaN with zeros
df.replace(np.nan, 0, inplace=True)

print("Writing results to file: " + output_file)
df.to_csv(output_file, index=False)
