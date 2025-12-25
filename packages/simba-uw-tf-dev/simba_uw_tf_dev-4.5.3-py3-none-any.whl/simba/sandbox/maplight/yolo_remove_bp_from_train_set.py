from simba.utils.read_write import recursive_file_search



def yolo_remove_bp_from_train_set(in_dir: str):

    file_paths = recursive_file_search(directory=in_dir, extensions=['txt'])
    for cnt, file_path in enumerate(file_paths):
        print(f'Processing file {cnt+1}/{len(file_paths)}')
        results = ''
        with open(file_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            line_data = line.split()[:-6]
            results += " ".join(line_data)
            results += '\n'

        with open(file_path, "w") as f:
            f.write(results)


yolo_remove_bp_from_train_set(in_dir=r'E:\netholabs_videos\mosaics\yolo_mdl_wo_tail')