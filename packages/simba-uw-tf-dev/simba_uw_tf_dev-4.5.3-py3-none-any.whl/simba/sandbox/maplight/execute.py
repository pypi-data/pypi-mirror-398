import os
from typing import Union
from datetime import datetime
import subprocess
import pandas as pd
import glob
from configparser import ConfigParser
import time
import json

CONFIG_PATH = 'C:\projects\simba\simba\simba\sandbox\maplight\config.json'

class Execute():
    def __init__(self,
                 video_dir: Union[str, os.PathLike]):

        self.start_time = time.time()
        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)
        video_paths = self.find_video_files(video_dir)

        timestamp_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
        if len(video_paths) == 0: raise FileNotFoundError(f'No video files found in {video_dir}')
        else: print(f'Analyzing {len(video_paths)} videos...')
        self.project_name = f'SimBA_project_{timestamp_str}'
        self.project_path = os.path.join(video_dir, self.project_name)
        self.project_config_path = os.path.join(video_dir, self.project_name, 'project_folder', 'project_config.ini')
        self.video_info_path = os.path.join(video_dir, self.project_name, 'project_folder', 'logs', 'video_info.csv')
        self.logs_dir = os.path.join(video_dir, self.project_name, 'project_folder', 'logs')
        self.yolo_csv_dir = os.path.join(video_dir, self.project_name, 'yolo_data')
        self.video_dir, self.video_paths = video_dir, video_paths
        if not os.path.isdir(self.yolo_csv_dir):
            os.makedirs(self.yolo_csv_dir)
    #
    def find_video_files(self, root_dir, extensions=None):
        if extensions is None:
            extensions = self.config['video']['accepted_formats']
        video_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if any(file.lower().endswith(ext) for ext in extensions):
                    video_files.append(os.path.join(dirpath, file))
        return video_files


    def run(self):

        ########## CREATE PROJECT
        print('Creating a new SimBA project...')
        create_project_args = ["--project_path", self.video_dir,
                               "--project_name", self.project_name,
                               "--target_list", self.config['classifier']['target']]
        subprocess.Popen(["conda", "run", "-n", "simba_310", "python", self.config['paths']['config_creator']] + create_project_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).wait()

        config = ConfigParser()
        config.read(self.project_config_path)
        config['Multi animal IDs']['ID_list'] = 'resident, intruder'
        config['threshold_settings']['threshold_1'] = '0.6'
        config['Minimum_bout_lengths']['min_bout_1'] = '200'
        config['SML settings']['model_path_1'] = self.config['paths']['classifier']
        with open(self.project_config_path, "w") as file: config.write(file)

        ########## RUN YOLO
        print(f'Running YOLO tracking on {len(self.video_paths)} video(s) in {self.video_dir}...')
        run_yolo_args = ["--weights", self.config['paths']['yolo_inference'],
                         "--video_path", self.video_dir,
                         "--save_dir", self.yolo_csv_dir,
                         "--keypoint_names", ",".join(self.config['keypoints']['names']),
                         "--interpolate",
                         "--verbose",
                         "--smoothing", "100",
                         "--box_threshold", "0.1",
                         "--max_per_class", "1"]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['yolo_inference']] + run_yolo_args)


        ######## CREATE VIDEO INFO
        EXPECTED_FLOAT_COLS = ["fps", "Resolution_width", "Resolution_height", "Distance_in_mm", "pixels/mm"]
        video_info_df = pd.DataFrame(columns=["Video", "fps", "Resolution_width", "Resolution_height", "Distance_in_mm", "pixels/mm"])
        csv_files = glob.glob(os.path.join(self.yolo_csv_dir, '**', '*.csv'), recursive=True)
        csv_files = [os.path.splitext(os.path.basename(p))[0] for p in csv_files]
        for video_name in csv_files:
            video_info_df.loc[len(csv_files)] = [video_name, 30, 500, 600, 987, 1.12]
        video_info_df[EXPECTED_FLOAT_COLS] = video_info_df[EXPECTED_FLOAT_COLS].apply(pd.to_numeric, errors="coerce")
        video_info_df = video_info_df.set_index("Video")
        video_info_df.to_csv(self.video_info_path)

        ########## IMPORT YOLO
        print(f'Importing YOLO tracking data for {len(self.video_paths)} videos to SimBA project...')
        import_yolo_args = ["--data_dir", self.yolo_csv_dir,
                            "--config_path", self.project_config_path,
                            "--verbose",
                            "--px_per_mm", "1.12",
                            "--fps", "30"]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['yolo_importer']] + import_yolo_args)

        ########## EXTRACT FEATURES
        print(f'Extracting features for {len(self.video_paths)} videos in SimBA project...')
        x_extract_args = ["--config_path", self.project_config_path]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['feature_extractor']] + x_extract_args)

        ########## INFERENCE
        print(f'Running {self.config["classifier"]["target"]} classifications on {len(self.video_paths)} videos...')
        x_inf_args = ["--config_path", self.project_config_path]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['inference']] + x_inf_args)

        ########## DESCRIPTIVE STATISTICS
        print(f'Calculating descriptive statistics for {self.config["classifier"]["target"]} classifications on {len(self.video_paths)} videos...')
        descriptive_args = ["--config_path", self.project_config_path,
                            "--classifiers", self.config['classifier']['target'],
                            "--no_mean_event_duration",
                            "--no_median_event_duration",
                            "--no_mean_interval_duration",
                            "--no_median_interval_duration"]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['agg_clf']] + descriptive_args)

        ########## CALUCLATING MOVEMENT STATISTICS
        print(f'Calculating MOVEMENT statistics for on {len(self.video_paths)} videos...')
        movement_args = ["--config_path", self.project_config_path,
                         "--body_parts", ",".join(self.config['movement']['bodyparts'])]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", self.config['paths']['movement']] + movement_args)
        elapsed_time = round((time.time() - self.start_time), 5)
        print(f'ANALYSIS FOR {len(self.video_paths)} VIDEOS COMPLETE!. DATA SAVED IN {self.logs_dir} (elapsed time: {elapsed_time}s)')


    #
    #
    #
    #
    #
    #
    #





