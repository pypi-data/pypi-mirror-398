import os.path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from simba.utils.read_write import create_directory, remove_a_folder

clf_time_mean, clf_time_sem = [], []
first_mean, first_sem = [], []
distance_cm_mean, distance_cm_sem = [], []

def org_data(clf_path: str, movement_path: str, save_dir: str):

    clf_df, mov_df = pd.read_csv(clf_path), pd.read_csv(movement_path)
    for i in range(1, 14):
        clf_day_df = clf_df[clf_df["VIDEO"].str.contains(f'_D{i}_', case=True, na=False)].reset_index(drop=True)

        mov_day_df = mov_df[mov_df["VIDEO"].str.contains(f'_D{i}_', case=True, na=False)].reset_index(drop=True)
        data_dir = os.path.join(save_dir, f'Day {i}')
        if os.path.isdir(data_dir): remove_a_folder(folder_dir=data_dir)
        create_directory(data_dir)
        clf_out_path = os.path.join(data_dir, 'attack_data.csv')
        mov_out_path = os.path.join(data_dir, 'movement.csv')
        clf_day_df.to_csv(clf_out_path)
        mov_day_df.to_csv(mov_out_path)

        total_event_durations = clf_day_df[clf_day_df['MEASUREMENT'] == 'Total event duration (s)']['VALUE'].fillna(0).values
        first_occurances = clf_day_df[clf_day_df['MEASUREMENT'] == 'First occurrence (s)']['VALUE'].fillna(0).values

        total_distance = mov_day_df[mov_day_df['MEASURE'] == 'Distance (cm)']['VALUE'].fillna(0).values

        duration_mean = np.mean(total_event_durations)
        duration_sem = np.std(total_event_durations, ddof=1) / np.sqrt(len(total_event_durations))
        first_occurances_mean = np.mean(first_occurances)
        first_occurances_sem = np.std(first_occurances, ddof=1) / np.sqrt(len(first_occurances))
        dist_mean = np.mean(total_distance)
        dist_sem = np.std(total_distance, ddof=1) / np.sqrt(len(total_distance))


        clf_time_mean.append(duration_mean)
        clf_time_sem.append(duration_sem)
        first_mean.append(first_occurances_mean)
        first_sem.append(first_occurances_sem)

        distance_cm_mean.append(dist_mean)
        distance_cm_sem.append(dist_sem)



    # # X positions (optional)
    # x = range(len(distance_cm_mean))
    #
    # # Plot with error bars
    # plt.figure(figsize=(6, 4))
    # plt.errorbar(x, distance_cm_mean, yerr=distance_cm_sem, fmt='-o', capsize=5, label='Mean ± SEM')
    #
    # # Labels and styling
    # plt.xlabel("Index")
    # plt.ylabel("Value")
    # plt.title("Line Plot with SEM Error Bars")
    # plt.legend()
    # plt.grid(True)
    # plt.tight_layout()
    # plt.show()
    #



    print(clf_time_mean)
    print(clf_time_sem)


org_data(clf_path=r"E:\maplight_videos\data_csvs\data_summary_20251023053746.csv", movement_path=r"E:\maplight_videos\data_csvs\Movement_log_20251023052350.csv", save_dir=r"E:\maplight_videos\data_csvs")