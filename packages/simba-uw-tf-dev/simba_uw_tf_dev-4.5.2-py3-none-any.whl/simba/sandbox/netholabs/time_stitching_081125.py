import numpy as np
import os
import glob
import datetime
from typing import Optional
from datetime import datetime, timezone, timedelta
import cv2
from tqdm import trange

class TimeStitcher:

    def __init__(self,
                 n_cams: int,
                 root_dir: str,
                 date: str,
                 hour_start: str,
                 n_mins: int,
                 shrink_factor: int,
                 cage_id: Optional[int] = None):


        self.n_cams, self.date, self.hour_start, self.root_dir = n_cams, date, hour_start, root_dir
        self.n_mins, self.shrink_factor, self.cage_id = n_mins, shrink_factor, cage_id

    def load_times(self,
                   fname,
                   minute):

        data = np.load(fname, allow_pickle=True)
        frame_times_ms = data['frame_times'] // 1000
        time_stamps_binned = frame_times_ms // 10 * 10  # convert to millseconds and round to 10ms bin
        return time_stamps_binned

    def decompress_video(self,
                         minute,
                         fname,
                         root_dir,
                         cam,
                         time_stamps_binned,
                         unix_time_to_start_of_minute,
                         shrink_factror=1,
                         overwrite_existing=True):

        ''' use OpenCV or something fast to load the video file or uncompress it.
            Not clear yet if we should just save to disk, but probably,
        '''
        # use opencv to load video
        # and save the png files with the filenmae of

        frame_height = 720
        frame_width = 1280
        channels = 3
        # shrink based on the shrink factor
        if shrink_factror > 1:
            frame_height //= shrink_factror
            frame_width //= shrink_factror
            print("shrinking video frames to: ", frame_height, "x", frame_width)
        frame_size_bytes = frame_height * frame_width * channels
        blank_frame = np.zeros((frame_height, frame_width, channels), dtype=np.uint8)

        # ok so we now have to take the time stamps
        times_relative_to_min_start = time_stamps_binned - unix_time_to_start_of_minute
        print("time stamps relative to start of minute: ", times_relative_to_min_start)
        print(" total frames: ", len(times_relative_to_min_start),
              "total unique frames:", np.unique(times_relative_to_min_start).shape[0])

        # make file names
        fname_video_current_minute = os.path.split(fname)[0] + "/minute_" + str(minute) + ".bin"
        fname_video_next_minute = os.path.split(fname)[0] + "/minute_" + str(minute + 1) + ".bin"

        # Step 1: Check if file exists & count existing frames
        # then we need to indepnt to existin frame to start appending

        if os.path.exists(fname_video_current_minute):
            file_size = os.path.getsize(fname_video_current_minute)
            frames_already_written = file_size // frame_size_bytes
            print(f"File already exists: {frames_already_written} frames found.")
        else:
            frames_already_written = 0
            print("File does not exist yet.")

        # need to check that if there is a full video in place already then we can exit safely
        if frames_already_written >= 6000:
            print("... this minute of data already decompressed, exiting ...")
            return

        # we need to make sure that the first time stamp is 0

        # so we now loop over the video and the raw frames
        # we fill blanks until we reach the next time stamp

        # use open cv to laod video
        import cv2
        print("opening video file: ", fname)
        cap = cv2.VideoCapture(fname)
        if not cap.isOpened():
            raise IOError("Cannot open video file: {}".format(fname))

        #
        ctr_frame = 0
        ctr_bin = frames_already_written * 10
        n_frames_read = 0
        n_unique_frames_written = 0
        with open(fname_video_current_minute, 'ab') as f:

            ##################### FILL EXISTING VIDEO WITH BLANKS ######################
            # if video already in place need to then fill the gap between the previous video ended
            #  and current one; usually about 3-5 seconds of duration during file upload to the server
            if frames_already_written > 0:
                print("... video exists filling up downtime with blank frames ...")
                # TODO: fill in video with last frame - so we load it
                while ctr_bin != times_relative_to_min_start[ctr_frame]:
                    # we write on frame to stack and advance 10 ms
                    f.write(blank_frame.tobytes())
                    ctr_bin += 10
                    # print ("ctr_bin: ",ctr_bin)
                    # print ("ctr_frame: ", ctr_frame)
                    # print ("times_relative to min start: ", times_relative_to_min_start[ctr_frame])
                    # don't increment the video frame coutner;
                    # we're just trying to catch up to it with the blank frames

            ####################################################################
            ##################### LOOP OVER 60 sec VIDEO  ######################
            ####################################################################
            while ctr_bin < 60000:
                ret, frame = cap.read()
                if not ret:
                    break

                # let's print size of the frame
                # print ("frame shape: ", frame.shape, " frame size: ", frame.size, " bytes: ", frame.nbytes)

                # return

                # if ctr_bin%5000==0:
                #    print ("processing frame: ", ctr_bin, " / ", 60000, " frames written: ", n_frames_written)

                # we subsample/shrink frame based on shrink factor
                if shrink_factror > 1:
                    # let's use simple subsampling
                    if True:
                        frame = frame[::shrink_factror, ::shrink_factror, :]
                    else:
                        #
                        frame = cv2.resize(frame, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)

                #
                while ctr_bin < times_relative_to_min_start[ctr_frame]:
                    # we need to write a blank frame
                    f.write(blank_frame.tobytes())
                    ctr_bin += 10  # increment the bin counter
                    # increment the bin counter

                # write the frame to the binary file
                # print ("ctr_bin", ctr_bin, ", ctr_frame: ", ctr_frame, times_relative_to_min_start[ctr_frame])
                n_frames_read += 1

                # check to makes sure next value is different:
                # we only write frames that are unique
                # don't generallyneed to check if we have more ctr_frame than
                if (ctr_frame + 1) <= times_relative_to_min_start.shape[0]:
                    if times_relative_to_min_start[ctr_frame] != times_relative_to_min_start[ctr_frame + 1]:
                        f.write(frame.tobytes())
                        ctr_bin += 10
                        n_unique_frames_written += 1

                #
                ctr_frame += 1

                # we also replace the blank frame now with the last read frame
                blank_frame = frame.copy()

        #
        print("# UNIQUE frames written current min", n_unique_frames_written,
              ", n_frames_read: ", n_frames_read)
        print("last frame time written: ", times_relative_to_min_start[ctr_frame], " ctr_frame: ", ctr_frame)

    def make_video(self,
                   root_dir,
                   minute,
                   n_cams,
                   fname_combined,
                   shrink_factor=1,
                   overwrite_existing=False
                   ):

        ''' make a video from the available frames for this minute '''

        frame_height = 720  # pixels
        frame_width = 1280  # pixels
        channels = 3  # RGB
        if shrink_factor > 1:
            frame_height //= shrink_factor
            frame_width //= shrink_factor
            print("shrinking video frames to: ", frame_height, "x", frame_width)
        frame_size_bytes = frame_height * frame_width * channels  # 1024 * 768 * 3 = 2,359,296 bytes

        if os.path.exists(fname_combined) and overwrite_existing == False:
            print("... combined video file already exists: ", fname_combined)
            return

        rows, cols = 3, 6
        frame_all_cams_blank = np.zeros((frame_height * rows, frame_width * cols, channels), dtype=np.uint8)

        print("creating combined video file: ", fname_combined)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(fname_combined, fourcc, 30.0, (frame_width * cols, frame_height * rows))

        # we actually want to grab freeze frames from non-recorded cameras - so we don't reinitialize this
        for i in trange(6000):

            # loop over cameras and grab a frame from each
            for cam in range(1, n_cams + 1, 1):
                # find the filename for this camera and bin
                fname_frame = os.path.join(root_dir,
                                           str(cam),
                                           "minute_" +
                                           str(minute) + ".bin")

                #
                if os.path.exists(fname_frame):
                    # we need to index into this file to the current frame i using framesize-bytes
                    with open(fname_frame, 'rb') as f:
                        f.seek(i * frame_size_bytes)

                        frame_data = f.read(frame_size_bytes)
                        if len(frame_data) != frame_size_bytes:
                            # leave the previous frame in place
                            continue
                        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((frame_height, frame_width, channels))

                        try:
                            frame = np.frombuffer(frame, dtype=np.uint8).reshape((frame_height,
                                                                                  frame_width,
                                                                                  channels))
                        except:
                            # ok we need to print a lot of metadata to understan why we're reading patst the end of the file
                            print("i: ", i)
                            print("cam: ", cam)
                            print("fname: ", fname_frame)
                            print("frame_size_bytes: ", frame_size_bytes)

                    #
                    # adding frame from camera:  2  to row:  2  col:  0  at position:  144 216 0 128
                    # adding frame from camera:  3  to row:  0  col:  0  at position:  0 72 0 128

                    col = 5 - ((cam - 1) // 3)  # 6 total columns → index 0..5 reversed
                    row = (cam - 1) % 3  # 0=top, 1=middle, 2=bottom in OpenCV coords

                    r0 = row * frame_height
                    r1 = r0 + frame_height
                    c0 = col * frame_width
                    c1 = c0 + frame_width

                    frame_all_cams_blank[r0:r1, c0:c1, :] = frame

                    #
            #         print ("adding frame from camera: ", cam,
            #                " to row: ", row, " col: ", col,
            #                " at position: ", r0, r1, c0, c1)

            # return

            # now write the combined frame to the video file
            out.write(frame_all_cams_blank)
        # this is probably coming at the end. not sure exactly
        out.release()
        print('finished writing combined video file: ', fname_combined)


    def run(self):
        for minute in range(self.n_mins):
            fname_combined = os.path.join(self.root_dir, f"minute_{minute}.avi")
            if os.path.exists(fname_combined):
                print(f"Video exists for minute {minute} ...skipping... \n \n")

            for cam in range(1, self.n_cams + 1, 1):
                if self.cage_id is not None:
                    fname_root = os.path.join(self.root_dir, str(cam), f"{self.cage_id}_{cam}_{self.date}_{self.hour_start}_{str(minute).zfill(2)}" + "*.npz")
                else:
                    fname_root = os.path.join(self.root_dir, str(cam), f"{self.date}_{self.hour_start}-{str(minute).zfill(2)}" + "*.npz")
                fnames = glob.glob(fname_root)
                if len(fnames) == 0:
                    #print(f'... no files found for camera: {cam}, minute: {min} \n')
                    continue
                print(f"minute: {minute}, 'cam': {cam}, files: {fnames}")
                time_stamps_binned = self.load_times(fnames[0], minute)
                print("time stamps binned: ", time_stamps_binned)
                dt_naive = datetime.strptime(f"{self.date.replace('_', '-')} {self.hour_start}:{minute:02d}", "%Y-%m-%d %H:%M")
                dt_utc1 = dt_naive.replace(tzinfo=timezone(timedelta(hours=1)))
                timestamp_ns = int(dt_utc1.timestamp() * 1_000_000_000)
                unix_time_to_start_of_minute = timestamp_ns // 1_000_000
                print("absolute unix time (ms, UTC+1) to start of minute:", unix_time_to_start_of_minute)
                fname_video = fnames[0].replace('_metadata.npz', '_simon.mp4')
                # use opencv to uncomrpess the video to .png files on disk
                self.decompress_video(minute,
                                 fname_video,
                                 self.root_dir,
                                 cam,
                                 time_stamps_binned,
                                 unix_time_to_start_of_minute,
                                 self.shrink_factor,
                                 overwrite_existing=True)

            print('')

            ######################################
            #process #2 - here we make the mosaic 1 minute video based on the available files
            #we loop over all possible files

            self.make_video(self.root_dir,
                            minute,
                            self.n_cams,
                            fname_combined,
                            shrink_factor=self.shrink_factor,
                            overwrite_existing=True)

            print("***************************")
            print('')


N_CAMS = 9
ROOT_DIR = r"D:\netholabs\temporal_stitching_2\test_temporal_stitching"
HOUR_START = "06"
DATE = "2025-07-16"
N_MINS =         1
SHRINK_FACTOR =  10
CAGE_ID =        None
x = TimeStitcher(n_cams=N_CAMS, root_dir=ROOT_DIR, hour_start=HOUR_START, n_mins=N_MINS, shrink_factor=SHRINK_FACTOR, cage_id=CAGE_ID, date=DATE)
x.run()





