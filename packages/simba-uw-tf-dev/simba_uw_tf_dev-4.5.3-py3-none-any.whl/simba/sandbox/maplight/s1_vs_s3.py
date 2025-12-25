import pandas as pd
import numpy as np

COMPARISON_PATH = r"E:\maplight_videos\data_summaries\comparison.xlsx"
NEW_PATH = r"E:\maplight_videos\data_summaries\simba3_new.csv"
OLD_SIMBA3_DATA = r"E:\maplight_videos\data_summaries\simba3_old.csv"

old_simba3_data = pd.read_csv(OLD_SIMBA3_DATA)
old_simba3_data = old_simba3_data.rename(columns={"ATTACK - Total event duration (s)": "DURATION (SIMBA3 OLD)"})[['VIDEO', "DURATION (SIMBA3 OLD)"]].sort_values(by='VIDEO')


new_data = pd.read_csv(NEW_PATH)
new_data = new_data.rename(columns={"ATTACK - Total event duration (s)": "DURATION (SIMBA3 NEW)"})[['VIDEO', "DURATION (SIMBA3 NEW)"]].sort_values(by='VIDEO')

old_simba3_data["DURATION (SIMBA3 NEW)"] = new_data["DURATION (SIMBA3 NEW)"]


#old_simba3_data.to_csv('E:\maplight_videos\data_summaries\comparison.csv')

for i in range(1, 14):
    day_data = old_simba3_data[old_simba3_data["VIDEO"].str.contains(f"_D{i}_", na=False)]
    old_mean= np.mean(day_data["DURATION (SIMBA3 OLD)"].values)
    new_mean = np.mean(day_data["DURATION (SIMBA3 NEW)"].values)

    old_std = np.std(day_data["DURATION (SIMBA3 OLD)"].values)
    new_std = np.std(day_data["DURATION (SIMBA3 NEW)"].values)

    print(old_mean, old_std, new_mean, new_std)


# for day, day_data in comparison_sheets.items():
#     new_day_data = new_data[new_data["VIDEO"].str.contains(f"_D{day}_", na=False)]
#     old_simba3_day_data = old_simba3_data[old_simba3_data["VIDEO"].str.contains(f"_D{day}_", na=False)]
#     print(old_simba3_day_data)
#     for val in day_data['S3'].values:
#         match = old_simba3_day_data[old_simba3_day_data['ATTACK - Total event duration (s)'] == val]
#         print(match)
#     break