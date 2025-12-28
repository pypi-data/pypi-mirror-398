import os, glob, re
import xlwings as xw

def Art2CSV(mw, fPath, progress_callback):
    all_text = ""
    all_text = all_text + "Starting art 2 csv conversion process\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Starting art 2 csv conversion process")
    Art2Data = "Country,Bar Code,Style Code,Colour,Size,Price1,Date,Season,Category1,Category2\n"
    fileList = glob.glob(os.path.join(fPath, "Art2*.dat"))
    for filen in fileList:
        fn = os.path.split(filen)[-1]
        Country = fn[4:6].strip()
        #print(f"Processing : {os.path.split(filen)[-1]} for {Country}")
        tmpFile = open(filen, "r", encoding = "utf8")
        tmpLine = tmpFile.readlines()
        for line in tmpLine:
            Art2Data = Art2Data + f"{Country},{line[:13]},{line[13:20]},{line[20:24]},{line[24:30].strip()},{line[34:41]}.{line[41:43]},{line[43:51]},{line[51:54]},{line[118:148].strip()},{line[148:].strip()}\n"

        tmpFile.close()

    with open(os.path.join(fPath, "Master.csv"), "w", encoding="utf8") as f:
        f.write(Art2Data)

    all_text = all_text + "Done converting Art files\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Done converting Art files")
    return "Done."


def EDI2CSV(mw, fPath, progress_callback):
    all_text = ""
    all_text = all_text + "Starting edi 2 csv conversion process\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Starting edi 2 csv conversion process")
    try:
        app = xw.App(visible=False)
        wb = xw.Book(mw.macroBook)
        uzEDI_macro = wb.macro('Undiz_EDI_File_Cleanup')
        fileList = glob.glob(os.path.join(fPath, "*.edi"))

        for filen in fileList:
            #print(f"Processing : {filen}")
            all_text = all_text + f"Processing : {filen}\n"
            progress_callback.emit(all_text)
            uzEDI_macro(filen)

    except:
        wb.close()
        app.kill()
        all_text = all_text + "Error occured in Image insert process, exiting process\n"
        progress_callback.emit(all_text)

    #print("Done...")
    all_text = all_text + "Done converting edi files\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Done converting edi files")
    wb.close()
    app.kill()
    return "Done."

def process_art_files(mw, folder_path, effective_price_date="20251201"):
    # Check if the folder path exists
    if not os.path.isdir(folder_path):
        #print(f"Error: The path '{folder_path}' is not a valid directory.")
        mw.infotextmisc_lable.setText(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    # Pattern to match: Art2(XX)OK(YYYYMMDD).dat
    # Group 1: The two-letter code (AE, BH, etc.)
    # Group 2: The original date
    pattern = re.compile(r"Art2([A-Z]{2})OK(\d{8})\.dat")

    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        
        if match:
            code = match.group(1)  # e.g., 'AE' or 'BH'
            _date = match.group(2)
            # 1. Define the New Filename
            # Logic: Art2_20251223_{code}.dat
            new_filename = f"Art2_{_date}_{code}.dat"
            
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(folder_path, new_filename)

            # 2. Edit the File Content (Positions 44-51)
            # Python indices are 0-based, so 44-51 (1-based) is [43:51]
            try:
                with open(old_file_path, 'r') as f:
                    lines = f.readlines()

                #--------------------------------------------------------------
                seen_prefixes = set()
                unique_lines = []

                for line in lines:
                    # Determine duplicity by the first 24 characters
                    # We strip to handle short lines or trailing whitespace consistently
                    prefix = line[:24]
                    
                    if prefix not in seen_prefixes:
                        seen_prefixes.add(prefix)
                        
                        # 2. Edit the content (Positions 44-51)
                        if len(line) >= 51:
                            # Replace indices 43 through 50 (1-based 44-51)
                            updated_line = line[:43] + effective_price_date + line[51:]
                            unique_lines.append(updated_line)
                        else:
                            unique_lines.append(line)
                #--------------------------------------------------------------

                with open(old_file_path, 'w') as f:
                    f.writelines(unique_lines)
                    '''
                    for line in lines:
                        # Ensure the line is long enough to have those positions
                        if len(line) >= 51:
                            # Replace indices 43 through 50 with the new date
                            updated_line = line[:43] + effective_price_date + line[51:]
                            f.write(updated_line)
                        else:
                            f.write(line)
                    '''
                # 3. Rename the File
                os.rename(old_file_path, new_file_path)
                mw.infotextmisc_lable.setText(f"Processed and renamed: {filename} -> {new_filename}")

            except Exception as e:
                mw.infotextmisc_lable.setText(f"Failed to process {filename}: {e}")

    return "Done."

def process_prd_files(mw, folder_path):
    # Check if the folder path exists
    if not os.path.isdir(folder_path):
        mw.infotextmisc_lable.setText(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    pattern = re.compile(r"Prod2([A-Z]{2})OK(\d{8})\.dat")

    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        
        if match:
            code = match.group(1)  # e.g., 'AE' or 'BH'
            _date = match.group(2)
            new_filename = f"Prd2_{_date}_{code}.dat"
            
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(folder_path, new_filename)

            try:
                # Rename the File
                os.rename(old_file_path, new_file_path)
                mw.infotextmisc_lable.setText(f"Processed and renamed: {filename} -> {new_filename}")

            except Exception as e:
                mw.infotextmisc_lable.setText(f"Failed to process {filename}: {e}")

    return "Done."

def process_hier_files(mw, folder_path):
    # Check if the folder path exists
    if not os.path.isdir(folder_path):
        mw.infotextmisc_lable.setText(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    pattern = re.compile(r"Hie([A-Z]{2})OK(\d{8})\.dat")

    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        
        if match:
            code = match.group(1)  # e.g., 'AE' or 'BH'
            _date = match.group(2)
            new_filename = f"Hie2_{_date}_{code}.dat"
            
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(folder_path, new_filename)
            try:
                # Rename the File
                os.rename(old_file_path, new_file_path)
                mw.infotextmisc_lable.setText(f"Processed and renamed: {filename} -> {new_filename}")

            except Exception as e:
                mw.infotextmisc_lable.setText(f"Failed to process {filename}: {e}")

    return "Done."

def rename_art_files(mw, folder_path, progress_callback):
    progress_callback.emit("Starting Art file rename process")
    mw.infotextmisc_lable.setText(f"Starting Art file rename process")
    process_art_files(mw, folder_path, "20251210")
    process_prd_files(mw, folder_path)
    process_hier_files(mw, folder_path)
    progress_callback.emit("Done.")
    mw.infotextmisc_lable.setText(f"Done.")
    return "Done."
