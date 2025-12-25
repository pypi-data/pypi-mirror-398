# ToughAnimator

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://stride-c.synology.me:50000/ytkuof/toughanimator.git
   cd toughanimator
   ```

2. **Create a Python Virtual Environment**:

   ```bash
   python -m venv .env
   ```

3. **Activate the Virtual Environment**:

   - **Windows**:
     ```bash
     .env\Scripts\activate.bat
     ```
   - **Linux/Mac**:
     ```bash
     source .env/bin/activate
     ```

4. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Install ToughAnimator Locally**:

   ```bash
   pip install .
   ```

   This will install ToughAnimator in your Python virtual environment.

## Run Your Own Case with ToughAnimator

1. **Create a New Case**:

   - Create a new folder under `unresolve`. Name the folder according to your case (e.g., `unresolve/your_case_name`).
   - Copy all necessary TOUGH result files into the new folder.
   - Copy the `config.json` file from an existing case in the `test_cases` directory or create a new `config.json` file in the new folder. The file should have the following structure:

     ```json
     {
       "case_name": "your_case_name",
       "input_files": [
         "name_of_your_input_file (e.g., flow.inp)",
         "MESH",  // For a separate mesh file, if applicable
         "INCON"  // For a separate INCON file, if applicable
       ],
       "output_files": [
         "name_of_your_output_file (e.g., conn.csv)",
         "name_of_another_output_file (e.g., mesh.csv)",
         "name_of_other_output_file (add or remove as needed)"
       ],
       "corners_file": "name_of_your_corners_file (e.g., corners.csv)",
       "nas_path": "path/to/nas",
       "notes": "Any additional notes"
     }
     ```

   - The `config.json` file should contain these fields:
     - **case_name**: The name of your case.
     - **input_files**: A list of TOUGH input files (e.g., `flow.inp`). You can include multiple input files, but they must contain the `INCON`, `ELEME`, and `CONNE` blocks.
     - **output_files**: A list of output files (e.g., `conn.csv`, `mesh.csv`). Only CSV format files are currently supported.
     - **corners_file**: The name of the corners file (e.g., `corners.csv`). This field is optional and can be omitted if not applicable.
       - To obtain the corners file, open the **3D Results** in your PetraSim project, select **Export Data** from the **File** menu, and on the right side of the file-saving window, set the **Interpolation type** to **Interpolate to cell corners**. Save the file as CSV.
       
       ![Exporting corners file from PetraSim](../figures/export_results_data.png)
       
     - **nas_path**: The path to the NAS (Network Attached Storage) location where the case files are stored. This field is optional.
     - **notes**: Any additional notes or comments about the case. This field is optional.

2. **Run the Script**:

   - Ensure the virtual environment is activated.
   - Open `toughanimator/run.py` in VS Code and select **Run Without Debugging** (Ctrl+F5) or run the script from the command line:
     
     ```bash
     python run.py
     ```

## Run an Existing Case with ToughAnimator

1. **Set Name and Directory**:

   - Open `toughanimator/run.py`.
   - Modify the `dir_name` and `case_name` variables to match your case directory and name.

2. **Run the Script**:

   - Ensure the virtual environment is activated.
   - Open `toughanimator/run.py` in VS Code and select **Run Without Debugging** (Ctrl+F5) or run the script from the command line:
     
     ```bash
     python run.py
     ```

## Acknowledgments

Special thanks to the TOUGH3 development team for their outstanding work on the TOUGH suite of tools.

