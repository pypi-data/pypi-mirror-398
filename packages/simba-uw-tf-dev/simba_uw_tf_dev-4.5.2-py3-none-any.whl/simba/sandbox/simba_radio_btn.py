from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from PIL import ImageTk
from simba.utils.enums import Formats
from tkinter import *
import PIL

def SimBARadioButton(parent: Union[Frame, Canvas, LabelFrame, Toplevel],
                     txt: str,
                     variable: BooleanVar,
                     txt_clr: Optional[str] = 'black',
                     font: Optional[Tuple] = Formats.FONT_REGULAR.value,
                     compound: Optional[str] = 'left',
                     img: Optional[Union[ImageTk.PhotoImage, str]] = None,
                     enabled: Optional[bool] = True,
                     tooltip_txt: Optional[str] = None,
                     value: bool = False,
                     cmd: Optional[Callable] = None,
                     cmd_kwargs: Optional[Dict[Any, Any]] = None) -> Radiobutton:

    if isinstance(img, str):
        img = ImageTk.PhotoImage(image=PIL.Image.open(MENU_ICONS[img]["icon_path"]))

    if cmd_kwargs is None:
        cmd_kwargs = {}

    def execute_command():
        if cmd:
            evaluated_kwargs = {k: (v() if callable(v) else v) for k, v in cmd_kwargs.items()}
            cmd(**evaluated_kwargs)

    if cmd is not None:
        command = execute_command
    else:
        command = None


    btn = Radiobutton(parent,
                      text=txt,
                      font=font,
                      image=img,
                      fg=txt_clr,
                      variable=variable,
                      value=value,
                      compound=compound,
                      command=command)

    if img is not None:
        btn.image = img

    if not enabled:
        btn.config(state=DISABLED)

    if tooltip_txt is not None:
        CreateToolTip(widget=btn, text=tooltip_txt)

    return btn





