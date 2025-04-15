import math
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import os
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


def calculate_brokerage(lot_size, total_lot_size, buy_value, sell_value):
    """
    Calculate brokerage and other charges based on input values.
    This is a simplified calculation based on Zerodha's fee structure.
    """
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        url = "https://zerodha.com/brokerage-calculator/#tab-equities"
        driver.get(url)

        # Wait for elements and scrape values
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "intra_brokerage")))

        # Calculate turnover
        buy_turnover = buy_value * total_lot_size
        sell_turnover = sell_value * total_lot_size
        total_turnover = buy_turnover + sell_turnover

        # Enter values in the calculator fields
        buy_price_input = driver.find_element(By.CLASS_NAME, "intra_bp")
        sell_price_input = driver.find_element(By.CLASS_NAME, "intra_sp")
        quantity_input = driver.find_element(By.CLASS_NAME, "intra_qty")

        buy_price_input.clear()
        buy_price_input.send_keys(str(buy_value))
        sell_price_input.clear()
        sell_price_input.send_keys(str(sell_value))
        quantity_input.clear()
        quantity_input.send_keys(str(total_lot_size))

        # Wait for the results to updat
        # Brokerage (0.03% or Rs. 20 per executed order, whichever is lower)
        brokerage = driver.execute_script(
            'return document.querySelector("#intra_brokerage").innerHTML')  # Rs. 20 for buy + Rs. 20 for sell

        # STT (0.1% on sell side for delivery)
        stt = driver.execute_script('return document.querySelector("#intra_stt").innerHTML')

        # Exchange transaction charge (0.00325%)
        etc = driver.execute_script('return document.querySelector("#intra_etc").innerHTML')

        # GST (18% on brokerage and etc)
        gst = driver.execute_script('return document.querySelector("#intra_st").innerHTML')

        # SEBI charges (Rs. 10 per crore)
        sebi = driver.execute_script('return document.querySelector("#sebi").innerHTML')

        # Stamp duty (0.015% on buy side)
        stamp = driver.execute_script('return document.querySelector("#stamp_duty").innerHTML')

        # Total charges
        total = driver.execute_script('return document.querySelector("#intra_total").innerHTML')

        # Break even points (total charges / total quantity)
        break_even = driver.execute_script('return document.querySelector("#intra_breakeven").innerHTML')

        # Calculate total turnover for percentage calculation
        total_turnover = (buy_value + sell_value) * total_lot_size

        # Convert string values to float for percentage calculation
        def clean_value(val):
            return float(val.replace('₹', '').replace(',', ''))

        brokerage_value = clean_value(brokerage)
        stt_value = clean_value(stt)
        etc_value = clean_value(etc)
        gst_value = clean_value(gst)
        sebi_value = clean_value(sebi)
        stamp_value = clean_value(stamp)
        total_value = clean_value(total)
        total_brokerage = brokerage_value + stt_value + etc_value + gst_value + sebi_value + stamp_value

        # Format values to match Zerodha's display with percentages
        # Round to 2 decimal places, rounding up if the 3rd decimal is >= 5
        def round_up(value, decimals=2):
            multiplier = 10 ** decimals
            # Remove debug print to avoid console clutter
            if value * multiplier * 10 % 10 >= 5:
                return math.ceil(value * multiplier) / multiplier
            else:
                return math.floor(value * multiplier) / multiplier

        # Calculate brokerage percentage rounded up
        brokerage_percentage = round((total_brokerage / total_turnover) * 100, 3)

        result = {
            "BROKERAGE": brokerage,
            "STT_TOTAL": stt,
            "EXCHANGE_TXN_Charge": etc,
            "GST": gst,
            "SEBI_CHARGES": sebi,
            "STAMP DUTY": stamp,
            "TOTAL TAX AND CHARGES": total,
            "POINTS TO BREAKEVEN": break_even,
            "TOTAL BROKERAGE": total,
            "BROKERAGE %": f"{brokerage_percentage}%",
        }

        return result

    except Exception as e:
        import traceback
        error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
        print(f"Error in calculate_brokerage at line {error_line}: {str(e)}")
        print("Full stack trace:")
        print(traceback.format_exc())
       
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing WebDriver: {str(e)}")


def process_excel_file(input_file, progress_bar, progress_label, root_window):
    try:
        # Read the input Excel file
        # Check if INPUT directory exists, create it if it doesn't
        input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "INPUT")
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
            print(f"Created input directory: {input_dir}")
        
        # Create a copy of the input file with timestamp in INPUT directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_filename = os.path.basename(input_file)
        input_basename, input_ext = os.path.splitext(input_filename)
        input_copy_path = os.path.join(input_dir, f"{input_basename}_{timestamp}{input_ext}")
        
        # Copy the file
        if input_file != input_copy_path:  # Avoid copying if already in the right place
            with open(input_file, 'rb') as src_file:
                with open(input_copy_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            print(f"Copied input file to: {input_copy_path}")

        # Now process the file
        if input_file.lower().endswith('.csv'):
            df = pd.read_csv(input_file)
        else:  # Excel file
            df = pd.read_excel(input_file)

        # Create lists to store the scraped data
        brokerage_data = []
        total_rows = len(df)

        print(f"Processing {total_rows} rows from {input_file}")
        symbol = df.iloc[0]['SYMBOL'] if 'SYMBOL' in df.columns else "UNKNOWN"
        parameter_output = f"{symbol}_parameter.xlsx"

        # Copy the required columns to the first output file
        parameter_df = df[
            ['SL_N0', 'SYMBOL', 'LOT_SIZE', 'NO_OF_LOTS', 'TOTAL_LOT_SIZE', 'BUY_VALUE', 'SELL_VALUE']].copy()
        parameter_df.to_excel(parameter_output, index=False)
        print(f"Parameter file saved to {parameter_output}")

        # Process each row
        # Define a function to process a single row
        def process_row(row_data):
            lot_size = int(row_data['LOT_SIZE'])
            no_of_lots = int(row_data['NO_OF_LOTS'])

            # Get brokerage calculations
            buy_value = float(row_data['BUY_VALUE'])
            sell_value = float(row_data['SELL_VALUE'])
            calculated_values = calculate_brokerage(lot_size, lot_size * no_of_lots, buy_value, sell_value)
            buy_turnover = (buy_value + sell_value) * no_of_lots * lot_size

            # Prepare row data
            result_row = {
                'SL_N0': row_data['SL_N0'],
                'SYMBOLS': row_data['SYMBOL'],
                'LOT_SIZE': lot_size,
                "PREMUIM_VALUE": buy_value + sell_value,
                'NO_OF_LOTS': row_data['NO_OF_LOTS'],
                'TOTAL_LOT_SIZE': row_data['TOTAL_LOT_SIZE'],
                'TOTAL_PREMIUM_VALUE': buy_turnover,
            }

            # Add calculated values
            for key, value in calculated_values.items():
                if isinstance(value, str) and value.replace(".", "", 1).isdigit():
                    result_row[key] = float(value)  # Convert to float if it's a valid decimal number
                else:
                    result_row[key] = value

            return result_row

        # Process rows in parallel
        brokerage_data = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Create list of future objects
            futures = {executor.submit(process_row, row): i for i, row in df.iterrows()}

            # Process results as they complete
            for future in as_completed(futures):
                row_index = futures[future]
                progress = ((row_index + 1) / total_rows) * 100

                try:
                    result = future.result()
                    brokerage_data.append(result)

                    # Update progress
                    progress_bar['value'] = progress
                    progress_label.config(text=f"Processing: {progress:.1f}%")
                    root_window.update()
                except Exception as exc:
                    print(f"Row {row_index} generated an exception: {exc}")

        # Sort results back into original order
        brokerage_data.sort(key=lambda x: x['SL_N0'])

        # Create a new DataFrame with all the data
        results_df = pd.DataFrame(brokerage_data)

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Check if OUTPUT directory exists, create it if it doesn't
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OUTPUT")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # Generate output filename with timestamp in the OUTPUT directory
        output_file = os.path.join(output_dir, f'{symbol}SUMMARY_REPORT{timestamp}_intra_equity.xlsx')

        

        # Save to a new Excel file
        results_df.to_excel(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        return output_file, parameter_output

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        messagebox.showerror("Error", f"Error processing file: {str(e)}")
        return None, None


def find_input_file():
    """Find input files with naming pattern ending with _input.xl* (.xlsx, .xls, etc.) in the current directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Looking for input files in: {current_dir}")

    input_files = []
    for file in os.listdir(current_dir):
        file_path = os.path.join(current_dir, file)
        if os.path.isfile(file_path) and (
                (file.lower().endswith('_input.xlsx') or
                 file.lower().endswith('_input.xls') or
                 file.lower().endswith('_input.csv'))
        ):
            input_files.append(file_path)
            print(f"Found input file: {file_path}")

    if input_files:
        return input_files[0]  # Return the first matching file
    return None


def open_file_dialog():
    # Create the root window with larger dimensions
    root = tk.Tk()
    root.title("Brokerage Calculator")
    root.geometry("1000x500")  # Made window much bigger
    root.configure(bg="#f0f0f0")

    # Create a frame with larger dimensions
    main_frame = tk.Frame(root, padx=60, pady=60, bg="#f0f0f0")  # Increased padding
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Add a label with larger font
    label = tk.Label(main_frame, text="Brokerage Calculator", font=("Arial", 20, "bold"), fg="#000000",
                     bg="#f0f0f0")  # Larger font
    label.pack(pady=(0, 30))  # Increased padding

    # Find input file in the current directory
    input_file = find_input_file()

    selected_file = [None]  # Using list for mutable reference

    def start_processing():
        if input_file:
            selected_file[0] = input_file  # Store the path before closing
            root.destroy()
        else:
            messagebox.showerror("Error",
                                 "No input file found. Please ensure there's a file ending with '_input.xlsx', '_input.xls', or '_input.csv' in the same directory.")

    # Display appropriate message based on file presence
    if input_file:
        info_label = tk.Label(main_frame,
                              text="Input file is already present",
                              bg="#f0f0f0", fg="#000000", font=("Arial", 14))  # Increased font size
        file_info = tk.Label(main_frame,
                             text=f"Found: {os.path.basename(input_file)}",
                             bg="#f0f0f0", fg="#006400", font=("Arial", 12))
        file_info.pack(pady=10)
    else:
        info_label = tk.Label(main_frame,
                              text="Input file not present",
                              bg="#f0f0f0", fg="#FF0000",
                              font=("Arial", 14))  # Increased font size and changed color to red
    info_label.pack(pady=20)

    # Process button with larger size
    process_button = tk.Button(main_frame, text="Process File", command=start_processing,
                               bg="white", fg="#000000", font=("Arial", 14), padx=30, pady=15)  # Increased size
    process_button.pack(pady=30)  # Increased padding

    # Add info text with larger font
    info_label = tk.Label(main_frame,
                          text="The input file should be an Excel or CSV file containing the required columns:\nLOT_SIZE, SYMBOLS, NO_OF_LOTS, BUY_VALUE, SELL_VALUE\nand have a filename ending with '_input.xlsx', '_input.xls', or '_input.csv'",
                          bg="#f0f0f0", fg="#555555", justify=tk.LEFT, font=("Arial", 12))  # Increased font size
    info_label.pack(anchor=tk.W, pady=20)  # Added padding

    root.mainloop()
    return selected_file[0]  # Return only the selected file path


if __name__ == "__main__":
    file_path = open_file_dialog()
    if file_path:
        print(f"Selected file: {file_path}")

        # Create a processing window with progress bar - made larger
        processing_root = tk.Tk()
        processing_root.title("Processing File")
        processing_root.geometry("800x300")  # Made window larger
        processing_root.configure(bg="#f0f0f0")

        processing_frame = tk.Frame(processing_root, padx=30, pady=30, bg="#f0f0f0")  # Increased padding
        processing_frame.pack(fill=tk.BOTH, expand=True)

        processing_label = tk.Label(
            processing_frame,
            text=f"Processing file: {os.path.basename(file_path)}",
            bg="#f0f0f0",
            font=("Arial", 14)  # Increased font size
        )
        processing_label.pack(pady=(15, 25))  # Increased padding

        # Progress bar - made longer
        progress_bar = ttk.Progressbar(processing_frame, orient="horizontal", length=700,
                                       mode="determinate")  # Increased length
        progress_bar.pack(pady=15)  # Increased padding

        # Progress label
        progress_label = tk.Label(processing_frame, text="Progress: 0.0%", bg="#f0f0f0", fg="#000000",
                                  font=("Arial", 12))  # Increased font size
        progress_label.pack(pady=10)  # Increased padding

        # Start processing in a separate thread to keep UI responsive
        processing_root.update()

        output_file, parameter_output = process_excel_file(file_path, progress_bar, progress_label, processing_root)
        processing_root.destroy()

        if output_file and parameter_output:
            # Show success message and offer to open the file - made window larger
            root = tk.Tk()
            root.title("Processing Complete")
            root.geometry("600x300")  # Made window larger
            root.configure(bg="#f0f0f0")

            frame = tk.Frame(root, padx=30, pady=30, bg="#f0f0f0")  # Increased padding
            frame.pack(fill=tk.BOTH, expand=True)

            success_label = tk.Label(
                frame,
                text=f"Results saved successfully to:\n{output_file}",
                bg="#f0f0f0",
                justify=tk.CENTER,
                wraplength=550,  # Increased wraplength
                font=("Arial", 12)  # Added font size
            )
            success_label.pack(pady=(15, 25))  # Increased padding


            def open_output_file():
                try:
                    if platform.system() == 'Windows':
                        os.startfile(output_file)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.call(('open', output_file))
                    else:  # Linux
                        subprocess.call(('xdg-open', output_file))
                    root.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open file: {str(e)}")


            button_frame = tk.Frame(frame, bg="#f0f0f0")
            button_frame.pack(fill=tk.X)

            # Larger buttons
            open_button = tk.Button(
                button_frame,
                text="Open File",
                command=open_output_file,
                bg="#4CAF50",
                fg="#000000",
                padx=20,  # Increased padding
                pady=10,  # Increased padding
                font=("Arial", 12)  # Added font size
            )
            open_button.pack(side=tk.LEFT, padx=(100, 15))  # Adjusted spacing

            close_button = tk.Button(
                button_frame,
                text="Close",
                command=root.destroy,
                bg="#f44336",
                fg="#000000",
                padx=20,  # Increased padding
                pady=10,  # Increased padding
                font=("Arial", 12)  # Added font size
            )
            close_button.pack(side=tk.RIGHT, padx=(15, 100))  # Adjusted spacing

            root.mainloop()
        else:
            messagebox.showerror("Error", "Failed to process the file. Please check the console for details.")
    else:
        print("No input file selected or available")
