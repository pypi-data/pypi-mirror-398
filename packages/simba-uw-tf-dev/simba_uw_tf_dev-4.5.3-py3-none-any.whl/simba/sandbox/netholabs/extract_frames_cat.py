import numpy as np

# ok so we start with two vides from cameras
fnames_cam1 = [r"D:\netholabs\temporal_stitching_2\test_temporal_stitching\1\2025-07-16_06-00-56_metadata.npz",
               r"D:\netholabs\temporal_stitching_2\test_temporal_stitching\1\2025-07-16_06-03-01_metadata.npz"]

fnames_cam2 = [r"D:\netholabs\temporal_stitching_2\test_temporal_stitching\2\2025-07-16_06-00-56_metadata.npz",
               r"D:\netholabs\temporal_stitching_2\test_temporal_stitching\2\2025-07-16_06-03-01_metadata.npz"]

#########################################
# LOAD video time stamps
data = np.load(fnames_cam1[0], allow_pickle=True)
print(data.files)
frame_times_ms = data['frame_times'] // 1000
print(frame_times_ms)
recording_start_time = data['recording_start_time']
print("recording start time: ", recording_start_time)
encoder_start = data['encoder_start']
print("encoder start: ", encoder_start)

###############################################
# convert july 24, 2025  exacdtly midngith to milisecond in epoch systm eimte clock but make sure its' UTC+1 london time
epoch_start = np.datetime64('2025-07-24T00:00:00', 'ms') - np.timedelta64(1, 'h')  # UTC+1
epoch_start_ms = epoch_start.astype('datetime64[ms]').astype(int)

# so this is the video time stamps relative to the epoch start
delta_times = frame_times_ms - epoch_start_ms
print("time srelative to midnight (in ms): ", delta_times)

# now convert into bucket discrete time
delta_times_bucket = delta_times // 10 * 10  # convert to seconds
print("time relative to midnight in 10ms buckets: ", delta_times_bucket)

# and convert into a discrete bin of 10ms from midnight
delta_times_bucket_discrete = delta_times_bucket // 10
print("time relative to midnight in 10ms discrete buckets: ", delta_times_bucket_discrete)
print('')
print(' So we either ruse this bueckt version which tells you which 10ms bucket the frame is in')
print(' or the disrete version which tells you exactly what frame of the video to put the uncompressed video data into')

#####################################
# make some fake video data but don't generate the full array as it will take 100GB of ram
data_cam1_vid1 = np.zeros((frame_times_ms.shape[0]))
print("video data (ordinarlily this would be an .mp4 that's decompressed on the fly: ", data_cam1_vid1.shape)

# and we crate a 1 min video bucket to hold the videos
stitched_video = np.zeros((18, 60000))
print("stitched video (18 rpis, 60000 times should be about 10minutes (100fps * 60 * 10)): ", stitched_video.shape)
print(" (the full video is much larger as it has the frames 1024 , 768 and 3 channels for RGB)")

# so now we can loop over the relative to midnight time dicscrete buickets
for i in range(delta_times_bucket_discrete.shape[0]):
    bucket = delta_times_bucket_discrete[i]
    if i % 1000 == 0:
        print("processing frame ", i, " in bucket ", bucket)


    # so now we can put the video data into the stitched video
    # this is just a fake example, in reality you would decompress the video and put it into the stitched video
    stitched_video[0, bucket] = data_cam1_vid1[i]  # assuming we are putting cam1 data into the first row
