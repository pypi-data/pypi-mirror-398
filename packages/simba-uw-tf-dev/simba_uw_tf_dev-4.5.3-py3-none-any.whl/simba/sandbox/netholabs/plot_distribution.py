from simba.utils.read_write import recursive_file_search, get_fn_ext
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid display issues
import matplotlib.pyplot as plt
import seaborn as sns
from simba.utils.data import bucket_data, hist_1d

  # Use non-interactive backend to avoid display issues


def plot_distribution(data_dir: str, save_path: str = None, show_plot: bool = True):
    file_paths = recursive_file_search(directory=data_dir, extensions=['csv'])
    lengths = []
    for file_path in file_paths:
        file_name = get_fn_ext(filepath=file_path)[1]
        try:
            x = int(file_name.split('_', 100)[-1])
            lengths.append(x+1)
        except (ValueError, IndexError):
            print(f"Warning: Could not extract length from filename: {file_name}")
            continue

    if not lengths:
        print("No valid files found to plot")
        return

    lengths = np.array(lengths)

    # Calculate statistics
    r = np.array([np.min(lengths), np.max(lengths)])
    bin_width, bin_cnt = bucket_data(data=lengths)
    x_hist = np.histogram(lengths, bin_cnt, (r[0], r[1]))

    print(f"Data range: {r[0]} to {r[1]}")
    print(f"Number of files: {len(lengths)}")
    print(f"Mean length: {np.mean(lengths):.2f}")
    print(f"Median length: {np.median(lengths):.2f}")
    print(f"Standard deviation: {np.std(lengths):.2f}")

    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Histogram
    ax1.hist(lengths, bins=bin_cnt, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(np.mean(lengths), color='red', linestyle='--', label=f'Mean: {np.mean(lengths):.1f}')
    ax1.axvline(np.median(lengths), color='green', linestyle='--', label=f'Median: {np.median(lengths):.1f}')
    ax1.set_xlabel('File Length')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of File Lengths')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Box plot
    ax2.boxplot(lengths, patch_artist=True, boxprops=dict(facecolor='lightblue'))
    ax2.set_ylabel('File Length')
    ax2.set_title('Box Plot of File Lengths')
    ax2.grid(True, alpha=0.3)

    # Add statistics text
    stats_text = f'Count: {len(lengths)}\nMean: {np.mean(lengths):.1f}\nMedian: {np.median(lengths):.1f}\nStd: {np.std(lengths):.1f}'
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    if show_plot:
        plt.show()

    return lengths, x_hist



DATA_DIR = r'/mnt/filesystem/yolo_sequences'
SAVE_PATH = r'/mnt/filesystem/yolo_sequences/plot.png'

plot_distribution(data_dir=DATA_DIR, show_plot=False, save_path=SAVE_PATH)