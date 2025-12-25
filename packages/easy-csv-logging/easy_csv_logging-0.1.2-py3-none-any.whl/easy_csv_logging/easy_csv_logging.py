import pandas as pd
from pathlib import Path
import warnings
import inspect
from tabulate import tabulate
from collections.abc import Iterable
from typing import List,Tuple
import subprocess
import sys


from rich.table import Table
from rich import print as rprint
from rich.console import Console
from rich.box import SQUARE  

CSV_LOG_FILENAME = "csv_log.csv"
TXT_LOG_FILENAME = "csv_log.txt"  
COL0_NAME = "_____"
S_NO_ARGUMENT = "empty"



def _get_csv_path() -> Path:

    def _get_caller_directory():
        """
        Returns the directory of the script that called log_line.
        This makes the log file location relative to the callers script path, 
        not the current working directory of this file.
        """
        # Get the frame of the caller (outside this module)
        frame = inspect.stack()[-1]
        caller_path = Path(frame.filename)
        return caller_path.parent.resolve()

    dir_path = _get_caller_directory()
    dir_path.mkdir(parents=True, exist_ok=True)
    csv_path = dir_path / CSV_LOG_FILENAME

    return csv_path




def log(*args):#TODO one val or pair

    def rewrite_csv_as_txt(csv_path: Path):
        txt_path = csv_path.with_name(TXT_LOG_FILENAME)

        # Om CSV inte finns eller är tom → tom TXT-fil
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            txt_path.write_text("", encoding="utf-8")
            return

        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            txt_path.write_text("", encoding="utf-8")
            return

        if df.empty:
            txt_path.write_text("", encoding="utf-8")
            return

        # Konvertera allt till str och fyll NaN med tom sträng
        df = df.fillna("").astype(str)

        # get max length of eacch column
        col_max_lengths = {}
        for col in df.columns:
            name_len = len(col)
            values_lens = [len(str(val).strip()) for val in df[col]]
            max_value_len = max(values_lens) if values_lens else 0
            # Total bredd för cellen: namn + " : " + värde → +3 för " : "
            col_max_lengths[col] = name_len + max_value_len + 3

        
        lines = []
        separator = " | "  # separator for columns

        for idx, row in df.iterrows():
            cells = []
            for col in df.columns:
                value = str(row[col]).strip()
                name = col


                raw_cell = f"{name}: {value}"
                max_width = col_max_lengths[col]

                ## Klipp av om för långt, annars vänsterjustera
                #if len(raw_cell) > max_width:
                #cell = raw_cell[: max_width - 1] #+ "…"  # Lägg till … om avklippt
                #else:
                cell = raw_cell.ljust(max_width)

                cells.append(cell)

            lines.append(f"| {separator.join(cells)} |")

        # Steg 3: Skriv hela TXT-filen (overwrite)
        txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def create_col0_if_needed():
        if COL0_NAME not in df.columns:
            df[COL0_NAME] = pd.NA

    def create_new_columns_if_needed(pairs):
        for column_name,_ in pairs:
            column_name = (str(column_name)).strip()

            # create new column if it does not exist
            if column_name not in df.columns:
                df[column_name] = pd.NA

    def handle_arguments(args):
        def check_no_duplicate_names(lis_names):
            if len(lis_names)!=len(set(lis_names)):

                print("column_names:")
                print(lis_names)
                print("there can not be duplicate names")
                raise ValueError("there is duplicate column names")

        def is_array(x):
            return isinstance(x, Iterable) and not isinstance(x, (str, bytes))

        def is_pair(x):
            return is_array(x) and len(x) == 2

        # empty
        if len(args) == 0:
            return S_NO_ARGUMENT
        
        #one arg
        elif len(args) == 1 and not is_array(args[0]):
            return [[COL0_NAME,args[0]]]

        # two or more items, even count, none are arrays
        elif len(args) >= 2 and len(args) % 2 == 0 and all(not is_array(x) for x in args):

            lis_names = [item for i,item in enumerate(args) if i%2==0]
            lis_values = [item for i,item in enumerate(args) if i%2==1]
            
            check_no_duplicate_names(lis_names)
            if len(lis_names)!=len(lis_values):raise ValueError
           
            #fix up names
            pairs = [[name,value] for name,value in zip(lis_names,lis_values)]

            return pairs

        # many arguments, all pairs
        elif len(args) >= 1 and all(is_pair(x) for x in args):

            lis_names = [name for name,_ in args]
            check_no_duplicate_names(lis_names)

            pairs = [[name,value] for name,value in args]
            return pairs

        # one array containing pairs
        elif len(args) == 1 and is_array(args[0]) and all(is_pair(x) for x in args[0]):

            pairs = args[0]
            
            lis_names = [name for name,_ in pairs]
            check_no_duplicate_names(lis_names)

            return pairs

        else:# invalid
            raise ValueError


    pairs = handle_arguments(args)
    
    if pairs==S_NO_ARGUMENT:
        empty = True
    else:
        empty = False


    csv_path = _get_csv_path()
    
    # Load or create DataFrame
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    create_col0_if_needed()

    if not empty:
        create_new_columns_if_needed(pairs)

    #make an empty row
    new_row = pd.DataFrame([{col: pd.NA for col in df.columns}])
    
    #fill the row with what should be logged
    if not empty:
        for column_name,value in pairs:

            column_name = (str(column_name)).strip()
            value = str(value).strip()

            new_row[column_name] = value
            # New row
            
        
    # append row
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        df = pd.concat([df, new_row], ignore_index=True)
    
    # Save
    df.to_csv(csv_path, index=False)
    rewrite_csv_as_txt(csv_path)
        

def view_log(print_to_console: bool = True):


    def df_to_padded_grid(df: pd.DataFrame) -> List[List[str]]:
        """
        Konverterar en DataFrame till en perfekt paddad grid av strängar.
        Format per cell: "kolumnnamn : värde" eller "kolumnnamn :   -   " om tomt.
        Raise ValueError om någon cell överskrider max tillåten bredd.
        """
        if df.empty:
            return []

        df_display = df.fillna("").astype(str)

        # Steg 1: Beräkna max tillåten bredd per kolumn
        col_max_widths = {}
        for col in df_display.columns:
            name_len = len(col)
            value_lens = [len(v.strip()) for v in df_display[col]]
            max_value_len = max(value_lens) if any(value_lens) else 1  # minst plats för "-"
            max_width = name_len + 3 + max_value_len  # "namn : värde"
            col_max_widths[col] = max_width

        # Steg 2: Skapa grid (tom list of lists)
        grid: List[List[str]] = []

        # Steg 3: Fyll grid rad för rad
        for _, row in df_display.iterrows():
            row_cells: List[str] = []
            for col in df_display.columns:
                value = row[col].strip()
                display_value = value if value else "-"

                # Bygg raw cell
                raw_cell = f"{col} : {display_value}"

                max_width = col_max_widths[col]

                # Steg 4: Kontrollera längd – raise error om för lång
                if len(raw_cell) > max_width:
                    raise ValueError(
                        f"Cell för lång! Kolumn '{col}', värde '{value}', "
                        f"raw='{raw_cell}' har längd {len(raw_cell)} men max är {max_width}"
                    )

                # Steg 5: Pad med mellanslag (vänsterjusterat)
                padded_cell = raw_cell.ljust(max_width)

                row_cells.append(padded_cell)

            grid.append(row_cells)

        return grid

    csv_path = _get_csv_path()

    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()

    if df.empty:
        if print_to_console:
            rprint("[yellow]Log is empty.[/yellow]")
        return

    try:
        grid = df_to_padded_grid(df)
    except ValueError as e:
        if print_to_console:
            rprint(f"[red]Formateringsfel: {e}[/red]")
        return

    # Skapa Rich-tabell
    table = Table(title="LOG VIEWER", box=SQUARE, show_header=True,
                  header_style="bold magenta", title_style="bold green")

    # Headers = kolumnnamnen
    for col in df.columns:
        table.add_column(col, justify="left", style="#FFD700")

    # Lägg till rader från grid
    for row in grid:
        table.add_row(*row)

    if print_to_console:

        rprint("="*100)
        rprint(table)
        rprint("="*100)

