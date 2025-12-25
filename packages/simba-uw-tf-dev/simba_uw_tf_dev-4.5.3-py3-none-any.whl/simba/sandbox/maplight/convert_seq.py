
from simba.utils.read_write import find_files_of_filetypes_in_directory
import pims
import cv2

def convert_seq(dir: str):

    file_paths = find_files_of_filetypes_in_directory(directory=dir, extensions=['.seq'])
    file_paths = [x for x in file_paths if x.endswith('_t.seq')]
    for file in file_paths:
        frames = pims.open(file)





convert_seq(dir='E:\crim13\CRIM13_test1')