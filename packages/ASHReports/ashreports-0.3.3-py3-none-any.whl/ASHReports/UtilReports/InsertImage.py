import os
import xlwings as xw
from ASHC_v3.initiateConfig import initiateConfig
from PySide6.QtWidgets import QFileDialog

def insertImage(mw, file_path, progress_callback):            # progress_callback
    all_text = ""
    imageDirectory = mw.imgFolderPath_lineedit.text() + "\\"
    all_text = all_text + f"Inserting Image in file {file_path}\n"
    progress_callback.emit(all_text)
    
    try:
        app = xw.App(visible=False)
        wb = xw.Book(mw.macroBook)
        InsertImage_macro = wb.macro('InsertImage')
        InsertImage_macro(file_path, imageDirectory, 1, 1)
        wb.close()
        app.kill()
        all_text = all_text + "Finished Image insert process\n"
        progress_callback.emit(all_text)
    except:
        wb.close()
        app.kill()
        all_text = all_text + "Error occured in Image insert process, exiting process\n"
        progress_callback.emit(all_text)

    return "Done."
