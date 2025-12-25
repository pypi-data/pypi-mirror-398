import tkinter as tk
from tkinter import filedialog, messagebox
import os
from simba.sandbox.maplight.execute import Execute

def browse_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        dir_var.set(folder_selected)
        status_label.config(text="Directory selected", fg="#27ae60")

def run_action():
    folder = dir_var.get()
    if not os.path.isdir(folder):
        messagebox.showwarning("Warning", "Please select a valid directory!")
        status_label.config(text="Invalid directory!", fg="#e74c3c")
        return
    status_label.config(text="Processing...", fg="#3498db")
    root.update_idletasks()
    try:
        executor = Execute(video_dir=folder)
        executor.run()
        status_label.config(text="Completed successfully!", fg="#27ae60")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        status_label.config(text="Error occurred", fg="#e74c3c")

def on_enter_browse(e):
    browse_btn.config(bg="#5a6268", fg="white")

def on_leave_browse(e):
    browse_btn.config(bg="#6c757d", fg="white")

def on_enter_run(e):
    run_btn.config(bg="#218838", fg="white")

def on_leave_run(e):
    run_btn.config(bg="#28a745", fg="white")

root = tk.Tk()
root.title("Classification Application")
root.geometry("550x300")
root.resizable(False, False)
root.config(bg="#ecf0f1")

dir_var = tk.StringVar()
dir_var.set("No directory selected")

header_frame = tk.Frame(root, bg="#2c3e50", height=60)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

header_label = tk.Label(header_frame, text="VIDEO CLASSIFICATION", 
                        font=("Arial", 18, "bold"), 
                        bg="#2c3e50", fg="white")
header_label.pack(expand=True)

main_frame = tk.Frame(root, bg="#ecf0f1", padx=30, pady=20)
main_frame.pack(fill="both", expand=True)

instruction_label = tk.Label(main_frame, 
                            text="Select a video directory to begin classification", 
                            font=("Arial", 10), 
                            bg="#ecf0f1", 
                            fg="#34495e")
instruction_label.pack(pady=(0, 15))

browse_btn = tk.Button(main_frame, 
                      text="📁 BROWSE VIDEO DIRECTORY", 
                      command=browse_directory,
                      font=("Arial", 11, "bold"),
                      bg="#6c757d",
                      fg="white",
                      relief="flat",
                      padx=20,
                      pady=12,
                      cursor="hand2",
                      activebackground="#5a6268",
                      activeforeground="white")
browse_btn.pack(pady=(0, 10))
browse_btn.bind("<Enter>", on_enter_browse)
browse_btn.bind("<Leave>", on_leave_browse)

dir_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
dir_frame.pack(fill="x", pady=(0, 15))

dir_label = tk.Label(dir_frame, 
                    textvariable=dir_var, 
                    bg="white", 
                    anchor="w", 
                    font=("Arial", 9),
                    fg="#2c3e50",
                    padx=10,
                    pady=8)
dir_label.pack(fill="x")

run_btn = tk.Button(main_frame, 
                   text="▶ RUN CLASSIFICATION", 
                   command=run_action,
                   font=("Arial", 12, "bold"),
                   bg="#28a745",
                   fg="white",
                   relief="flat",
                   padx=30,
                   pady=15,
                   cursor="hand2",
                   activebackground="#218838",
                   activeforeground="white")
run_btn.pack(pady=(5, 10))
run_btn.bind("<Enter>", on_enter_run)
run_btn.bind("<Leave>", on_leave_run)

status_label = tk.Label(main_frame, 
                       text="Ready", 
                       font=("Arial", 9, "italic"),
                       bg="#ecf0f1",
                       fg="#7f8c8d")
status_label.pack()

root.mainloop()