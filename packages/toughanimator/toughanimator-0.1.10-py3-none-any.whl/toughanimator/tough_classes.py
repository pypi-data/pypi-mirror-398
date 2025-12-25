import math
import os
import io
import sys
import re
import shutil
import numpy as np
import pandas as pd
from vtkmodules.all import *
import pathlib
import json

from enum import Enum

class MeshType(Enum):
    RegularGrid = 1
    StructuredGridOrth = 2
    StructuredGridFree = 3
    PolygonalMesh = 4

class MeshPlane():
    unknown = -1,
    X = 1,
    Y = 2,
    Z = 3,
    XZ = 4,
    XY = 5,
    YZ = 6,
    XYZ = 7

class OutType():
    Unknown = 0,
    TEC = 1, 
    CSV = 2

class VisType():
    Tecplot = 1
    ParaView = 2
    MatplotLib = 3

class ToughVersion(Enum):
    Unknown = 0
    TOUGH2 = 2
    TOUGH3 = 3
    TOUGHReact = 4

class ValueType(Enum):
    Unknown = 0
    Scalar = 1
    Vector = 3

class VisTimeStep:
    def __init__(self, time_step, iteration, time):
        self.selected = True
        self.time_step = time_step
        self.iter = iteration
        self.time = time
        self.vtu_file_name = ""

class VisVariable:
    def __init__(self, name, value_type, number_of_components):
        self.variable_name = name
        self.value_type = value_type
        self.number_of_components = number_of_components
    def to_dict(self):
        return {
            "variable_name": self.variable_name,
            "value_type": self.value_type.name,  # or .value if you prefer
            "number_of_components": self.number_of_components  # or .value if you prefer
        }

class VisSetting:
    def __init__(self, input_file_paths, out_file_paths, vis_dir, corners_file="unkown", out_format_type=OutType.Unknown, tough_version = ToughVersion.Unknown, vis_types=[VisType.ParaView, VisType.Tecplot], mesh_type=MeshType.RegularGrid, debug=False, eos="ECO2N", minc=False, selected_variables_scalar = [], selected_variables_vector = [], ngv=False):
        self.mesh_type = mesh_type
        self.out_format_type = out_format_type
        self.vis_types = vis_types
        self.input_file_paths = input_file_paths
        self.out_file_paths = out_file_paths
        self.vis_dir = vis_dir
        self.known_bounds = False
        self.debug = debug
        self.tough_version = tough_version
        self.mesh_plane = MeshPlane.unknown
        self.isReverse = False
        self.corners_file = corners_file
        self.debug = debug
        self.eos = eos
        self.minc = minc
        self.selected_variables_scalar = selected_variables_scalar
        self.selected_variables_vector = selected_variables_vector
        self.ngv = ngv


    def setBounds(self, x_bounds, y_bounds, z_bounds):
        self.bounds = np.concatenate((x_bounds, y_bounds, z_bounds))
        self.known_bounds = True

class vis_reader:
    def __init__(self, case_dir):
        self.setting = None
        self.main_geometry = None
        self.incon_path = None
        #self.variable_list = []
        self.variable_list = {}
        self.time_steps_list = []
        self.rock_dict = []
        if os.path.isdir(case_dir):
            config_path = os.path.join(case_dir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as config_file:
                    config = json.load(config_file)
            else:
                print(f"Config file:({config_path}) not found. Please create it.")
                sys.exit(1)
        else:
            print(f"Case directory:({case_dir}) not found. Please check it.")
            sys.exit(1)

        
        if "input_files" not in config:
            print(f"Input files not found in config.json. Please check it.")
            sys.exit(1)
        if "output_files" not in config:
            print(f"Output files not found in config.json. Please check it.")
            sys.exit(1)



        setting = VisSetting(
            input_file_paths = [os.path.join(case_dir, f) for f in config["input_files"]],
            out_file_paths = [os.path.join(case_dir, f) for f in config["output_files"]],
            vis_dir = config["vis_dir"] if "vis_dir" in config else case_dir,
            corners_file = os.path.join(case_dir, config["corners_file"] if "corners_file" in config else "None"),
            debug = config['debug'] if 'debug' in config else False,
            #eos = config['EOS'] if 'EOS' in config else "ECO2N",
            eos = next((v for k, v in config.items() if k.lower() == "eos"),"ECO2N"),
            #minc = config['MINC'] if 'MINC' in config else False,
            minc = next((v for k, v in config.items() if k.lower() == "minc"),False),
            selected_variables_scalar = config['selected_variables_scalar'] if 'selected_variables_scalar' in config else [],
            selected_variables_vector = config['selected_variables_vector'] if 'selected_variables_vector' in config else [],
            #ngv= config['NGV'] if 'NGV' in config else False
            ngv = next((v for k, v in config.items() if k.lower() == "ngv"),False)
        )

        # check if the project is using MINC
        minc_file = os.path.join(case_dir, 'MINC')
        if os.path.exists(minc_file):
            setting.minc = True
            self.minc_file = minc_file
            self.__check_num_of_minc()
        if minc_file in setting.input_file_paths:
            setting.input_file_paths.remove(minc_file)

        for input_file_path in setting.input_file_paths:
            if not os.path.exists(input_file_path):
                print(f'Can\'t find input file: ({input_file_path}). please check the path or remove it from the config.json.')
                sys.exit(1)

        for out_file_path in setting.out_file_paths:
            if not os.path.exists(input_file_path):
                print(f'Can\'t find output file: ({out_file_path}). please check the path or remove it from the config.json.')
                sys.exit(1)
                
        if not os.path.isdir(setting.vis_dir):
            print(f'Can\'t find directory: ({setting.vis_dir}). please check the path or remove it from the config.json.')
            sys.exit(1)
        else:
            vis_path = os.path.join(setting.vis_dir, "tough_vis")
            # delete the directory if it exists
            if os.path.isdir(vis_path):
                shutil.rmtree(vis_path)
            os.mkdir(vis_path)
            paraview_path = os.path.join(vis_path, 'paraview')
            os.mkdir(paraview_path)
            print(f"Visualization folder created: {vis_path}")
            setting.vis_dir = vis_path
        
        self.setting = setting

    def write_eleme_conne(self):
        if self.setting ==  None:
            print(f'Please initialize the vis_reader class with the case directory.')
            sys.exit(1)
        print(f'Reading input files ...')
        self.__write_elem_buffer()
        self.__write_conne_buffer()
        self.__write_rocks_buffer()
        print(f'Creating elements and connections ...')
        self.__create_elem_conne()
    
    def write_geometry(self):
        if self.setting ==  None:
            print(f'Please initialize the vis_reader class with the case directory.')
            sys.exit(1)

        
        if self.elem_conne_path == None:
            print(f'Can\'t find element and connection file. Please create it first. (write_eleme_conne)')
            sys.exit(1)
        
        print(f'Creating main geometry ...')
        self.__create_main_geometry()
          
    def write_incon(self):
        if self.setting ==  None:
            print(f'Please initialize the vis_reader class with the case directory.')
            sys.exit(1)
        if self.main_geometry == None:
            print(f'Can not find main geometry. Please create the main geometry first. (write_geometry)')
            sys.exit(0)
        print(f'Reading input files ...')
        self.__write_incon_buffer()
        print(f'Creating initial condition ...')
        self.__write_initial_conditions()
    
    def write_result(self):
        if self.setting ==  None:
            print(f'Please initialize the vis_reader class with the case directory.')
            sys.exit(1)
        if self.main_geometry == None:
            print(f'Can not find main geometry. Please create the main geometry first. (write_geometry)')
            sys.exit(0)
        
        for output_file_path in self.setting.out_file_paths:
            print(f'Reading output ({output_file_path}) ... ')
            
            self.current_out_file = output_file_path
            self.__check_TOUGH_version()
            print(f'    Version: {self.setting.tough_version.name}')
            print(f'    EOS: {self.setting.eos}')
            if self.setting.tough_version == ToughVersion.TOUGH2:
                self.__read_TOUGH2_CSV_outfile()
            elif self.setting.tough_version == ToughVersion.TOUGH3:
                self.__read_TOUGH3_CSV_outfile()
            elif self.setting.tough_version == ToughVersion.TOUGHReact:
                self.__read_tough_TEC_outfile()
                # add post calculation
        for timestep in self.time_steps_list:
                self.__post_process(timestep)
                if self.setting.ngv:
                    self.__post_process_ngv(timestep)
        self.__write_json()
        print(f'All files have been created in {self.setting.vis_dir}.')

    def write_all(self):
        self.write_eleme_conne()
        self.write_geometry()
        self.write_incon()
        self.write_result()

    # TODO: need to clean up the code
    def __check_bounds(self):
        if not self.setting.bounds[1] > self.setting.bounds[0]:
            print(
                f'Max X {self.setting.bounds[1]} must be greater than Min X {self.setting.bounds[0]}.')
            sys.exit(1)
        if not self.setting.bounds[3] > self.setting.bounds[2]:
            print(
                f'Max Y {self.setting.bounds[3]} must be greater than Min Y {self.setting.bounds[2]}.')
            sys.exit(1)
        if not self.setting.bounds[5] > self.setting.bounds[4]:
            print(
                f'Max Z {self.setting.bounds[5]} must be greater than Min Z {self.setting.bounds[4]}.')
            sys.exit(1)
        # print(f'Can\'t find input file: {self.setting.input_path}.')

    def __read_input(self):
        self.__write_elem_buffer()
        self.__write_conne_buffer()
        self.__write_rocks_buffer()
        self.__write_incon_buffer()

    def __write_elem_buffer(self):
        self.eleme_buffer = io.StringIO()
        # write temp element txt
        has_elem = False
        for input_file_path in self.setting.input_file_paths:
            line_counter = 0
            with open(input_file_path, encoding="utf-8") as f:
                reading_elem = False

                for line in f:
                    if line.startswith('ELEME-') or line.startswith('ELEME'):
                        reading_elem = True
                        has_elem = True
                        find_elem = True
                        continue
                    if reading_elem:
                        line_counter += 1
                        if self.__check_if_block_end(line, line_counter):
                            reading_elem = False
                            found_path = input_file_path
                            break
                        else:
                            self.eleme_buffer.write(line)

        if has_elem == False:
            print(f'Can\'t find ELEME block in input_file_paths.')
            sys.exit(1)
        else:
            print(f'    Found ELEME block in {found_path}')
    def __check_num_of_minc(self):
        #self.minc_buffer = io.StringIO()
        minc_num = 0
        with open(self.minc_file, encoding="utf-8") as f:
            reading_minc = False
            for line in f:
                if line.startswith('ELEME-') or line.startswith('ELEME'):
                    reading_minc = True
                    #has_minc = True
                    continue
                if reading_minc: 
                    
                    if self.__check_if_block_end(line, minc_num):
                        reading_minc = False
                        #found_path = input_file_path
                        break
                    else:
                        minc_num += 1
                        #self.minc_buffer.write(line)
        self.num_of_minc = minc_num

    def __write_conne_buffer(self):
        self.conne_buffer = io.StringIO()
        # write temp element txt
        has_conne = False
        for input_file_path in self.setting.input_file_paths:
            line_counter = 0
            with open(input_file_path, encoding="utf-8") as f:
                
                reading_conne = False
                for line in f:
                    if line.startswith('CONNE-') or line.startswith('CONNE'):
                        reading_conne = True
                        has_conne = True
                        continue
                    if reading_conne: 
                        line_counter += 1
                        if self.__check_if_block_end(line, line_counter):
                            reading_conne = False
                            found_path = input_file_path
                            break
                        else:
                            self.conne_buffer.write(line)

        if has_conne == False:
            print(f'Can\'t find CONNE block in input_file_paths.')
            sys.exit(1)
        else:
            print(f'    Found CONNE block in {found_path}')

    def __write_rocks_buffer(self):
        self.rocks_buffer = io.StringIO()
        #self.rocks_sgr_buffer = io.StringIO()
        has_rocks = False
        
        for input_file_path in self.setting.input_file_paths:
            line_counter = 0
            with open(input_file_path, encoding="utf-8") as f:
                reading_rocks = False
                for line in f:
                    if line.startswith('ROCKS-'):
                        reading_rocks = True
                        has_rocks = True
                        continue

                    if reading_rocks:
                        line_counter+= 1
                        if self.__check_if_block_end(line, line_counter):
                            reading_rocks = False
                            found_path = input_file_path
                            break
                        else:
                            if 'SEED' in line:
                                continue
                            first_line = line.replace('\n', '').rstrip()
                            
                            #skip 1 lines
                            f.readline()
                            third_line = f.readline()
                            new_line = f'{first_line}{third_line}'
                            self.rocks_buffer.write(new_line)
                            f.readline()


        if has_rocks == False:
            print(f'Can\'t find ROCKS block in all input_file_paths.')
            sys.exit(1)
        else:
            print(f'    Found ROCKS block in {found_path}')

    def __write_incon_buffer(self):
        self.incon_buffer = io.StringIO()
        has_incon = False
        self.global_incon = False
        # write temp element txt
        
        for input_file_path in self.setting.input_file_paths:
            line_counter = 0
            with open(input_file_path, encoding="utf-8") as f:
                
                reading_incon = False
                for line in f:
                    if line.startswith('INCON-'):
                        reading_incon = True
                        has_incon = True
                        #find_incon = True
                        continue

                    if reading_incon:
                        line_counter += 1
                        if self.__check_if_block_end(line, line_counter):
                            found_path = input_file_path
                            break
                        #line = f.readline() # skip first line #self.number_of_elements
                        eos = self.setting.eos
                        num = len(line.split())
                        if self.setting.eos.upper() == "ECO2N" and len(line.split()) == 4:
                            self.incon_buffer.write(line)
                        elif self.setting.eos.upper() == "EOS1":
                            line = f.readline() # skip first line #self.number_of_elements
                            if len(line.split()) == 2:
                                self.incon_buffer.write(line)


        if has_incon == False or self.incon_buffer.tell() == 0:
            print(f'Can\'t find INCON block in input_file_paths (or length of INCON is zero).')
            
            # find the fifth line of the "PARAM" block
            reading_pram = False
            for input_file_path in self.setting.input_file_paths:
                line_counter = 0
                with open(input_file_path, encoding="utf-8") as f:
                    reading_pram = False
                    for line in f:
                        if line.startswith('PARAM-'):
                            reading_pram = True
                            continue
                        if reading_pram:
                            line_counter += 1
                            if self.__check_if_block_end(line, line_counter):
                                if line_counter <5:
                                    print(f'    Can\'t find Global INCON line in PARAM block of {input_file_path}. Please check the PARAM block.')
                                    break
                                
                            if line_counter == 5:
                                self.global_incon = True
                                print(f'    Found Global INCON line in PARAM block of {input_file_path}')
                                self.incon_buffer.write(line)
                                break

        else:
            print(f'    Found INCON block in {found_path}')

    def __write_initial_conditions(self):

        self.incon_vtk = self.__read_vtk_file(self.main_geometry)


        
        self.incon_buffer.seek(0)
        incon_df = pd.DataFrame()
        if self.setting.eos.upper() == "ECO2N":
            # read incon
            incon_colspecs = [(0, 20), (20, 40), (40, 60), (60, 80)]  # define column widths
            incon_names = ['Pressure', 'NaCl', 'CO2', 'Temperature']
            incon_df = pd.read_fwf(self.incon_buffer, colspecs=incon_colspecs, header=None,
                                names=incon_names,
                                dtype={'Pressure':float, 'NaCl':float, 'CO2':float, 'Temperature':float})
        elif self.setting.eos.upper() == "EOS1":
            # read incon
            incon_colspecs = [(0, 20), (20, 40)]
            incon_names = ['Temperature', 'Pressure']
            incon_df = pd.read_fwf(self.incon_buffer, colspecs=incon_colspecs, header=None,
                                names=incon_names,
                                dtype={'Temperature':float, 'Pressure':float})
        if len(incon_df) == 0:
            print(f'    It is empty in INCON block.')
            return
        
        else:
            for header in incon_names:
                array = vtkDoubleArray()
                array.SetName(header)
                self.incon_vtk.GetCellData().AddArray(array)
                
            for i in range(0, self.incon_vtk.GetNumberOfCells()):
                for header in incon_names:
                    if self.global_incon:
                        # if global incon, use the first row
                        value = self.__parse_float(incon_df[header][0])
                    else:
                        index = self.sequence_dist[i]
                        value = self.__parse_float(incon_df[header][index])
                    self.incon_vtk.GetCellData().GetArray(header).InsertNextValue(value)

        extension = os.path.splitext(self.main_geometry)[1]
        self.incon_path = os.path.join(self.setting.vis_dir, f'incon{extension}')
        self.__write_vtk_file(self.incon_vtk, self.incon_path)
        print(f'    ✓ Initial condition file created: {self.incon_path}')



    def __read_TOUGH2_CSV_outfile(self):
        self.time_steps_list = []
        value_type = ValueType.Unknown
        current_time = None
        buffer = io.StringIO()
        csv_headers = []
        line_number = -1
        start_index = -1
        def process_chunk():
            """Define what to do with each flushed chunk."""
            buffer.seek(0)
            df = pd.read_csv(buffer)
            #print(f"Processing time group:\n{df.head()}")
            time_step = VisTimeStep(
                time=float(current_time),
                time_step=len(self.time_steps_list)+1,
                iteration=1
            )
            self.time_steps_list.append(time_step)
            if value_type == ValueType.Scalar:
                self.__write_scalar_result(time_step, df, csv_headers)
            elif value_type == ValueType.Vector:
                self.__write_vector_result(time_step, df, csv_headers)
            else:
                print('Error: Your value type is not supported')
                sys.exit(1)
            
            buffer.flush()
            buffer.close()

        with open(self.current_out_file, encoding="utf-8") as f:
            for line in f:
                line_number = line_number + 1
                values = line.strip().split(',')

                if line_number == 0:
                    csv_headers = [x.strip() for x in values]
                    #replace all " with ''"
                    csv_headers = [x.replace('"', '') for x in csv_headers]
                    if 'ELEM' in csv_headers and 'INDEX' in csv_headers:
                        value_type = ValueType.Scalar
                        #start_index = 1 # remove the first item

                    elif 'ELEM1' in csv_headers and 'ELEM2' in csv_headers:
                        value_type = ValueType.Vector
                        #start_index = 1

                    start_index = 1
                    # remove the first "TIME" header (to reduce the number of columns)    
                    csv_headers = csv_headers[start_index:]

                    # Write header once
                    buffer.write(','.join(csv_headers) + '\n')
                    continue

                row_time = self.__parse_float(values[0].strip())

                if current_time is None:
                    current_time = row_time

                if row_time != current_time:
                    # Time changed → flush and reset
                    process_chunk()
                    buffer = io.StringIO()
                    buffer.write(','.join(csv_headers) + '\n')  # Write header
                    current_time = row_time

                # Write current row
                buffer.write(','.join(values[start_index:]) + '\n')
            
            # Flush the last group
            if buffer.tell() > 0:
                process_chunk()
    

    def __read_TOUGH3_CSV_outfile(self):
        scalar_buffer = io.StringIO()
        current_time_step = None
        tim_step_counter = 1
        csv_headers = []
        line_number = -1
        reading_number = 0
        value_type = ValueType.Unknown
        start_index = -1
        self.time_steps_list = []
        
        with open(self.current_out_file, encoding="utf-8") as f:
            for line in f:
                line_number = line_number + 1
                values = line.strip().split(',')
                if line_number == 0:
                    values = [x.replace('"', '') for x in values]
                    csv_headers = [x.strip() for x in values]

                    if 'ELEM' in csv_headers:
                        value_type = ValueType.Scalar
                        start_index = 5
                        
                    elif 'ELEM1' in csv_headers and 'ELEM2' in csv_headers:
                        value_type = ValueType.Vector
                        start_index = 5
            
                    csv_headers = csv_headers[start_index:]
                    f.readline() # skip next line
                    print(f'    Value type: {value_type.name}')
                    continue

                # Find time item
                if len(values) == 1:
                    time_string = values[0].replace('"', '').strip()
                    time_string = time_string.split()[-1]
                    time = self.__parse_float(time_string)

                    # if not the first time step
                    if value_type == ValueType.Scalar and reading_number == self.number_of_elements:
                        scalar_buffer.seek(0)
                        df = pd.read_csv(scalar_buffer, sep=',', header=0)
                        self.__write_scalar_result(
                             current_time_step, df, csv_headers)
                        scalar_buffer.flush()
                        scalar_buffer.close()
                        scalar_buffer = io.StringIO()
                        reading_number = 0

                    if value_type == ValueType.Vector and reading_number == self.number_of_connections:
                        scalar_buffer.seek(0)
                        df = pd.read_csv(scalar_buffer, sep=',', header=0)
                        self.__write_vector_result(
                            current_time_step, df, csv_headers)
                        scalar_buffer.flush()
                        scalar_buffer.close()
                        scalar_buffer = io.StringIO()
                        reading_number = 0
                    
                    current_time_step = VisTimeStep(
                        time=float(time),
                        time_step=tim_step_counter,
                        iteration=1
                    )

                    # Initialize buffer
                    header_string = ','.join(csv_headers)
                    scalar_buffer.write(header_string + '\n')
                    self.time_steps_list.append(current_time_step)
                    tim_step_counter = tim_step_counter + 1

                else:
                    scalar_buffer.write(','.join(values[start_index:]) + '\n')
                    reading_number = reading_number + 1

            else:
                # write the last time step
                if value_type == ValueType.Scalar:
                    scalar_buffer.seek(0)
                    df = pd.read_csv(scalar_buffer, sep=',', header=0)
                    self.__write_scalar_result(current_time_step, df, csv_headers)
                if value_type == ValueType.Vector:
                    scalar_buffer.seek(0)
                    df = pd.read_csv(scalar_buffer, sep=',', header=0)
                    self.__write_vector_result(current_time_step, df, csv_headers)
                scalar_buffer.close()   

    def __old_read_TOUGH3_CSV_outfile(self):
        scalar_buffer = io.StringIO()
        current_time_step = None
        tim_step_counter = 1
        csv_headers = []
        line_number = -1
        reading_number = 0
        value_type = ValueType.Unknown
        start_index = -1
        self.time_steps_list = []
        
        with open(self.current_out_file, encoding="utf-8") as f:
            for line in f:
                line_number = line_number + 1
                values = line.strip().split(',')
                if line_number == 0:
                    values = [x.replace('"', '') for x in values]
                    csv_headers = [x.strip() for x in values]

                    if 'ELEM' in csv_headers:
                        value_type = ValueType.Scalar
                        start_index = 5
                        
                    elif 'ELEM1' in csv_headers and 'ELEM2' in csv_headers:
                        value_type = ValueType.Vector
                        start_index = 5
            
                    csv_headers = csv_headers[start_index:]
                    f.readline() # skip next line
                    print(f'    Value type: {value_type.name}')
                    continue

                # Find time item
                if len(values) == 1:
                    time_string = values[0].replace('"', '').strip()
                    time_string = time_string.split()[-1]
                    time = self.__parse_float(time_string)

                    # if not the first time step
                    if value_type == ValueType.Scalar and reading_number == self.number_of_elements:
                        scalar_buffer.seek(0)
                        df = pd.read_csv(scalar_buffer, sep=',', header=0)
                        self.__write_scalar_result(
                             current_time_step, df, csv_headers)
                        scalar_buffer.flush()
                        scalar_buffer.close()
                        scalar_buffer = io.StringIO()
                        reading_number = 0

                    if value_type == ValueType.Vector and reading_number == self.number_of_connections:
                        scalar_buffer.seek(0)
                        df = pd.read_csv(scalar_buffer, sep=',', header=0)
                        self.__write_vector_result(
                            current_time_step, df, csv_headers)
                        scalar_buffer.flush()
                        scalar_buffer.close()
                        scalar_buffer = io.StringIO()
                        reading_number = 0
                    
                    current_time_step = VisTimeStep(
                        time=float(time),
                        time_step=tim_step_counter,
                        iteration=1
                    )

                    # Initialize buffer
                    header_string = ','.join(csv_headers)
                    scalar_buffer.write(header_string + '\n')
                    self.time_steps_list.append(current_time_step)
                    tim_step_counter = tim_step_counter + 1

                else:
                    scalar_buffer.write(','.join(values[start_index:]) + '\n')
                    reading_number = reading_number + 1

            else:
                # write the last time step
                if value_type == ValueType.Scalar:
                    scalar_buffer.seek(0)
                    df = pd.read_csv(scalar_buffer, sep=',', header=0)
                    self.__write_scalar_result(current_time_step, df, csv_headers)
                if value_type == ValueType.Vector:
                    scalar_buffer.seek(0)
                    df = pd.read_csv(scalar_buffer, sep=',', header=0)
                    self.__write_vector_result(current_time_step, df, csv_headers)
                scalar_buffer.close()    

    def __read_tough_TEC_outfile(self):
        
        scalar_buffer = io.StringIO()
        #vector_buffer = io.StringIO()
        current_time_step = None
        tim_step_counter = 1
        reading_scalar = False
        scalar_headers = []
        self.time_steps_list = []

        with open(self.current_out_file, encoding="utf-8") as f:
            for line in f:
                if line.strip().lower().startswith('Variables'.lower()):
                    headers_value = line.strip().split('=')[1]
                    #scalar_headers = headers_value.replace('"', '')
                   
                    scalar_headers = re.split(' |,', headers_value.replace('"', '').strip())
                    scalar_headers = [x for x in scalar_headers if x]
                    scalar_headers.pop(0)
                    scalar_headers.pop(0)
                    scalar_headers.pop(0)
                    
                    continue
                if line.strip().lower().startswith('Zone T'.lower()):
                    if reading_scalar:
                        scalar_buffer.seek(0)
                        df = pd.read_csv(scalar_buffer, sep=',', header=0)
                        self.__write_scalar_result(
                            current_time_step, df, scalar_headers)
                        
                        scalar_buffer.flush()
                        scalar_buffer.close()
                        scalar_buffer = io.StringIO()

                    time_values = line.split('"')
                    time = time_values[1].split()[0]
                    current_time_step = VisTimeStep(
                        time=float(time),
                        time_step=tim_step_counter,
                        iteration=1
                    )
                    reading_scalar = True
                    header_string = ','.join(scalar_headers)
                    scalar_buffer.write(header_string + '\n')
                    self.time_steps_list.append(current_time_step)
                    tim_step_counter = tim_step_counter + 1
                    continue
                
                if reading_scalar and len(line.split()) == len(scalar_headers)+3:
                    csv_line = ','.join(line.split()[3:]) + '\n'
                    scalar_buffer.write(csv_line)
            
            # if process to the end of file
            else:
                if len(scalar_buffer.getvalue()) > 0:
                    #df = self.prepare_fixed_length_scalar_dataframe(scalar_headers, scalar_buffer)
                    scalar_buffer.seek(0)
                    df = pd.read_csv(scalar_buffer, sep=',', header=0)
                    self.__write_scalar_result(
                        current_time_step, df, scalar_headers)
                    scalar_buffer.flush()
                    scalar_buffer.close()
                    scalar_buffer = io.StringIO()
                    tim_step_counter = tim_step_counter + 1

    def __post_process(self, vis_time_step):
        time_index = self.time_steps_list.index(vis_time_step)
        #vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}.vtr')

        extension = os.path.splitext(self.main_geometry)[1]
        vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}{extension}')
        self.time_steps_list[time_index].vtu_file_name = vtr_path
        scalar_vtr = self.__read_vtk_file(vtr_path)   
        vtr = scalar_vtr

        post_variable_list = []
        # p
        p_name = "P"
        if vtr.GetCellData().GetArray("P (Pa)") is not None:
            p_name = "P (Pa)"
        if vtr.GetCellData().GetArray("P(Pa)") is not None:
            p_name = "P(Pa)"
        if vtr.GetCellData().GetArray("P(bar)") is not None:
            p_name = "P(bar)"
        if vtr.GetCellData().GetArray("PRES") is not None:
            p_name = "PRES"

        if vtr.GetCellData().GetArray(p_name) is not None and self.incon_vtk.GetCellData().GetArray('Pressure') is not None:
            delPArray = vtkDoubleArray()
            delPArray.SetName(f'del_{p_name}')
            for i in range(0, vtr.GetNumberOfCells()):
                p_value = vtr.GetCellData().GetArray(p_name).GetValue(i)
                incon_p = self.incon_vtk.GetCellData().GetArray('Pressure').GetValue(i)
                delP = p_value - incon_p
                delPArray.InsertNextValue(delP)

            vtr.GetCellData().AddArray(delPArray)
            post_variable_list.append(VisVariable(f'del_{p_name}', ValueType.Scalar, 1))
        
      # Put cell-centered data into points
        filter = vtkCellDataToPointData()
        filter.SetInputData(vtr)
        filter.Update()
        vtr_cell_to_points = filter.GetOutput()

        if vtr.GetCellData().GetArray(f'del_{p_name}') is not None:
            vtr.GetPointData().AddArray(vtr_cell_to_points.GetPointData().GetArray(f'del_{p_name}'))

        
        # add toughreact variables
        if self.setting.tough_version == ToughVersion.TOUGHReact or self.setting.tough_version == ToughVersion.TOUGH3:
            trapHCO2_array = vtkDoubleArray()
            trapHCO2_array.SetName('trapHCO2')

            trapRCO2_array = vtkDoubleArray()
            trapRCO2_array.SetName('trapRCO2')
        
            trapDCO2_array = vtkDoubleArray()
            trapDCO2_array.SetName('trapDCO2')

            trapMCO2_array = vtkDoubleArray()
            trapMCO2_array.SetName('trapMCO2')

            for index in range(0, vtr.GetNumberOfCells()):
                trapHCO2 = 0
                trapRCO2 = 0
                trapDCO2 = 0
                trapMCO2 = 0   
                VOLX = 0
                if vtr.GetCellData().GetArray("VOLX") is not None:
                    VOLX = vtr.GetCellData().GetArray("VOLX").GetValue(index)

                SatGas = 0
                if vtr.GetCellData().GetArray("SatGas") is not None:
                    SatGas = vtr.GetCellData().GetArray("SatGas").GetValue(index)
                elif vtr.GetCellData().GetArray("SAT_G") is not None:
                    SatGas = vtr.GetCellData().GetArray("SAT_G").GetValue(index)

                Porosity = 0
                if vtr.GetCellData().GetArray("Porosity") is not None:
                    Porosity = vtr.GetCellData().GetArray("Porosity").GetValue(index)
                elif vtr.GetCellData().GetArray("POR") is not None:
                    Porosity = vtr.GetCellData().GetArray("POR").GetValue(index)
                
                DGas_kg_m3 = 0
                if vtr.GetCellData().GetArray("DGas_kg/m3") is not None:
                    DGas_kg_m3 = vtr.GetCellData().GetArray("DGas_kg/m3").GetValue(index)
                elif vtr.GetCellData().GetArray("DEN_G") is not None:
                    DGas_kg_m3 = vtr.GetCellData().GetArray("DEN_G").GetValue(index)

                SatLiq = 0
                if vtr.GetCellData().GetArray("SatLiq") is not None: 
                    SatLiq = vtr.GetCellData().GetArray("SatLiq").GetValue(index)
                elif vtr.GetCellData().GetArray("SAT_L") is not None:
                    SatLiq = vtr.GetCellData().GetArray("SAT_L").GetValue(index)
                
                XCO2Liq = 0
                if vtr.GetCellData().GetArray("XCO2Liq") is not None:
                    XCO2Liq = vtr.GetCellData().GetArray("XCO2Liq").GetValue(index)
                elif vtr.GetCellData().GetArray("X_CO2_L") is not None:
                    XCO2Liq = vtr.GetCellData().GetArray("X_CO2_L").GetValue(index)

                sgr = 0
                if vtr.GetCellData().GetArray("sgr") is not None:
                    sgr = vtr.GetCellData().GetArray("sgr").GetValue(index)


                trapHCO2 =(SatGas-sgr)*VOLX*Porosity*DGas_kg_m3* (SatGas>sgr)
                trapRCO2 = 0.05 * VOLX * Porosity * DGas_kg_m3* (SatGas > sgr)+ SatGas * VOLX * Porosity * DGas_kg_m3*(SatGas <= sgr)
                trapDCO2 = SatLiq*VOLX*Porosity*DGas_kg_m3*XCO2Liq
                trapHCO2_array.InsertNextValue(self.__fix_negative_zero(trapHCO2))
                trapRCO2_array.InsertNextValue(self.__fix_negative_zero(trapRCO2))
                trapDCO2_array.InsertNextValue(self.__fix_negative_zero(trapDCO2))

                trapMCO2 = 0
                if vtr.GetCellData().GetArray("calcite") is not None:
                    calcite = vtr.GetCellData().GetArray("calcite").GetValue(index)
                    ankerite_2 = vtr.GetCellData().GetArray("ankerite-2").GetValue(index)
                    dawsonite = vtr.GetCellData().GetArray("dawsonite").GetValue(index)
                    dolomite_2 = vtr.GetCellData().GetArray("dolomite-2").GetValue(index)
                    magnesite = vtr.GetCellData().GetArray("magnesite").GetValue(index)
                    siderite_2 = vtr.GetCellData().GetArray("siderite-2").GetValue(index)
                    trapMCO2 =(calcite*1 + ankerite_2*2 + dawsonite*1 + dolomite_2*2 + magnesite*1 + siderite_2*1)*VOLX*Porosity*0.012
                trapMCO2_array.InsertNextValue(self.__fix_negative_zero(trapMCO2))

        
            vtr.GetCellData().AddArray(trapHCO2_array)
            vtr.GetCellData().AddArray(trapRCO2_array)
            vtr.GetCellData().AddArray(trapDCO2_array)
            vtr.GetCellData().AddArray(trapMCO2_array)
        
            post_variable_list.append(VisVariable('trapHCO2', ValueType.Scalar, 1))
            post_variable_list.append(VisVariable('trapRCO2', ValueType.Scalar, 1))
            post_variable_list.append(VisVariable('trapDCO2', ValueType.Scalar, 1))
            post_variable_list.append(VisVariable('trapMCO2', ValueType.Scalar, 1))

        
        # Put cell-centered data into points
        filter = vtkCellDataToPointData()
        filter.SetInputData(vtr)
        filter.Update()
        vtr_cell_to_points = filter.GetOutput()

        for variabl_name in ['trapHCO2', 'trapRCO2', 'trapDCO2', 'trapMCO2']:
            vtr.GetPointData().AddArray(vtr_cell_to_points.GetPointData().GetArray(variabl_name))

        if len(post_variable_list) > 0:
            self.variable_list["post"] = post_variable_list
            self.__write_vtk_file(vtr, vtr_path)

    def __post_process_ngv(self, vis_time_step):

        #self.rock_dict
        post_variable_list = []
        if self.setting.mesh_type != MeshType.RegularGrid:
            print('    NGV post-processing is only available for RegularGrid mesh.')
            return
        
        
        time_index = self.time_steps_list.index(vis_time_step)
        #vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}.vtr')

        extension = os.path.splitext(self.main_geometry)[1]
        vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}{extension}')
        self.time_steps_list[time_index].vtu_file_name = vtr_path
        scalar_vtr = self.__read_vtk_file(vtr_path)
        vtr = scalar_vtr

        
        vtr_dimemsion = scalar_vtr.GetDimensions()
        cell_index = 0 
        matIDArray = vtr.GetCellData().GetArray('Material_ID')
        
        G = 9.81
        Pc = 3000
        # creare vtk double array 'ut','delta_p','Ncv_k1','Ncv_k2','Ncv_k3','Ngv_k1','Ngv_k2','Ngv_k3','Nb','R1'

        Ncv_k1_array = vtkDoubleArray()
        Ncv_k1_array.SetName('Ncv_k1') 
        vtr.GetCellData().AddArray(Ncv_k1_array)
        Ncv_k2_array = vtkDoubleArray()
        Ncv_k2_array.SetName('Ncv_k2')  
        vtr.GetCellData().AddArray(Ncv_k2_array)
        Ncv_k3_array = vtkDoubleArray()
        Ncv_k3_array.SetName('Ncv_k3')
        vtr.GetCellData().AddArray(Ncv_k3_array)
        Ngv_k1_array = vtkDoubleArray()
        Ngv_k1_array.SetName('Ngv_k1')
        vtr.GetCellData().AddArray(Ngv_k1_array)
        Ngv_k2_array = vtkDoubleArray()
        Ngv_k2_array.SetName('Ngv_k2')
        vtr.GetCellData().AddArray(Ngv_k2_array)
        Ngv_k3_array = vtkDoubleArray()
        Ngv_k3_array.SetName('Ngv_k3')
        vtr.GetCellData().AddArray(Ngv_k3_array)
        Nb_array = vtkDoubleArray()
        Nb_array.SetName('Nb')
        vtr.GetCellData().AddArray(Nb_array)
        R1_array = vtkDoubleArray()
        R1_array.SetName('R1')
        vtr.GetCellData().AddArray(R1_array)

        post_variable_list.append(VisVariable('Ncv_k1', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Ncv_k2', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Ncv_k3', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Ngv_k1', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Ngv_k2', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Ngv_k3', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('Nb', ValueType.Scalar, 1))
        post_variable_list.append(VisVariable('R1', ValueType.Scalar, 1))
    
    
        # check if the required arrays are in the vtk file
        vis_gas_array = vtkDoubleArray()
        vis_gas_name = 'VIS(gas)'
        if vtr.GetCellData().GetArray(vis_gas_name) is not None:
            vis_gas_array = vtr.GetCellData().GetArray(vis_gas_name)
        else:
            print(f'    Can\'t find {vis_gas_name} array in the vtk file for NGV post-processing.')
            return
        
        dl_array = vtkDoubleArray()
        dl_name = 'DL (kg/m^3)'
        if vtr.GetCellData().GetArray(dl_name) is not None:
            dl_array = vtr.GetCellData().GetArray(dl_name)
        else:
            print(f'    Can\'t find {dl_name} array in the vtk file for NGV post-processing.')
            return
        
        dg_array = vtkDoubleArray()
        dg_name = 'DG (kg/m^3)'
        if vtr.GetCellData().GetArray(dg_name) is not None:
            dg_array = vtr.GetCellData().GetArray(dg_name)
        else:   
            print(f'    Can\'t find {dg_name} array in the vtk file for NGV post-processing.')
            return
        
        flof_array = vtkDoubleArray()
        flof_name = 'FLOF (kg/s)'
        if vtr.GetCellData().GetArray(flof_name) is not None:
            flof_array = vtr.GetCellData().GetArray(flof_name)
        else:
            print(f'    Can\'t find {flof_name} array in the vtk file for NGV post-processing.')
            return
        


        for z_index in range(0, vtr_dimemsion[2]-1):
            for y_index in range(0, vtr_dimemsion[1]-1):
                for x_index in range(0, vtr_dimemsion[0]-1):
                    dx = vtr.GetXCoordinates().GetValue(x_index+1) - vtr.GetXCoordinates().GetValue(x_index)
                    dy = vtr.GetYCoordinates().GetValue(y_index+1) - vtr.GetYCoordinates().GetValue(y_index)
                    #dz = vtr.GetZCoordinates().GetValue(z_index+1) - vtr.GetZCoordinates().GetValue(z_index)
                    

                    #elemID = self..GetValue(cell_index)
                    matID = matIDArray.GetValue(cell_index)
                    # find rock from self.rock_dict with id = matID
                    #rock = [obj for obj in self.rock_dict if obj.id == matID]

                    rock = next((o for o in self.rock_dict if o["id"] == matID), None)
                    per_1 = rock["per_1"] if rock else 0
                    per_2 = rock["per_2"] if rock else 0
                    per_3 = rock["per_3"] if rock else 0

                    #df['μCO2'] = df['VIS(gas)']
                    μCO2 = vis_gas_array.GetValue(cell_index)
                    #df['delta_p'] = df['DL (kg/m^3)'] - df['DG (kg/m^3)'] 
                    delta_p = dl_array.GetValue(cell_index) - dg_array.GetValue(cell_index)
                    #df['ut'] = np.sqrt(df['FLOF (kg/s)_x']**2 + df['FLOF (kg/s)_y']**2 + df['FLOF (kg/s)_z']**2)
                    FLOF = flof_array.GetTuple(cell_index)
                    
                    ut = math.sqrt(FLOF[0]**2 + FLOF[1]**2 + FLOF[2]**2)

                    #df['Ncv_k1']  = (df['k1'] * df[L] * df['Pc'] )/(df[H]**2 * df['μCO2'] * df['ut'])
                    #df['Ncv_k2']  = (df['k2'] * df[L] * df['Pc'] )/(df[H]**2 * df['μCO2'] * df['ut'])
                    #df['Ncv_k3']  = (df['k3'] * df[L] * df['Pc'] )/(df[H]**2 * df['μCO2'] * df['ut'])
                    #df['Ngv_k1']  = (df['delta_p'] * df['G'] * df['k1'] * df['d_x'])/(df[H] * df['μCO2'] * df['ut'])
                    #df['Ngv_k2']  = (df['delta_p'] * df['G'] * df['k2'] * df['d_x'])/(df[H] * df['μCO2'] * df['ut'])
                    #df['Ngv_k3']  = (df['delta_p'] * df['G'] * df['k3'] * df['d_x'])/(df[H] * df['μCO2'] * df['ut'])

                    L = dx
                    H = dy
                    k1 = per_1
                    k2 = per_2
                    k3 = per_3
                    Ncv_k1  = (k1 * L * Pc )/(H**2 * μCO2 * ut) if (H**2 * μCO2 * ut) !=0 else 0
                    Ncv_k2  = (k2 * L * Pc )/(H**2 * μCO2 * ut) if (H**2 * μCO2 * ut) !=0 else 0
                    Ncv_k3  = (k3 * L * Pc )/(H**2  * μCO2 * ut) if (H**2 * μCO2 * ut) !=0 else 0
                    Ngv_k1  = (delta_p * G * k1 * dx)/(H * μCO2 * ut) if (H * μCO2 * ut) !=0 else 0
                    Ngv_k2  = (delta_p * G * k2 * dx)/(H * μCO2 * ut) if (H * μCO2 * ut) !=0 else 0
                    Ngv_k3  = (delta_p * G * k3 * dx)/(H    * μCO2 * ut) if (H * μCO2 * ut) !=0 else 0

                    #df['Nb']  =(df['delta_p']  * df['G'] * df[H])/df['Pc'] 
                    Nb  =(delta_p  * G * H)/Pc if Pc !=0 else 0
                    #df['R1']  = df[L]/df[H]
                    R1  = L/H if H !=0 else 0
                    Ncv_k1_array.InsertNextValue(Ncv_k1)
                    Ncv_k2_array.InsertNextValue(Ncv_k2)
                    Ncv_k3_array.InsertNextValue(Ncv_k3)
                    Ngv_k1_array.InsertNextValue(Ngv_k1)
                    Ngv_k2_array.InsertNextValue(Ngv_k2)
                    Ngv_k3_array.InsertNextValue(Ngv_k3)
                    Nb_array.InsertNextValue(Nb)
                    R1_array.InsertNextValue(R1)
                    cell_index += 1

                #for z_index in range(0, scalar_vtr.GetZCoordinates().GetNumberOfTuples()):
            

        #if len(post_variable_list) > 0:
            #self.variable_list["post"].append(post_variable_list)
        self.__write_vtk_file(vtr, vtr_path)

        

        
    def __write_scalar_result(self, vis_time_step, dataframe, csv_headers):

        headers = csv_headers.copy()
        index = self.time_steps_list.index(vis_time_step)
        #vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}.vtr')

        extension = os.path.splitext(self.main_geometry)[1]
        vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}{extension}')
        self.time_steps_list[index].vtu_file_name = vtr_path
        #scalar_vtr = vtkRectilinearGrid()

        if not os.path.exists(vtr_path):
            scalar_vtr = self.__read_vtk_file(self.main_geometry)

            # add time step data
            timesteps = vtkDoubleArray()
            timesteps.SetName("TimeValue")
            timesteps.SetNumberOfTuples(1)
            timesteps.SetNumberOfComponents(1)
            timesteps.SetTuple1(0, vis_time_step.time)
            scalar_vtr.SetFieldData(vtkFieldData())
            scalar_vtr.GetFieldData().AddArray(timesteps)
         
        else:
            scalar_vtr = self.__read_vtk_file(vtr_path)    
        
        vtr = scalar_vtr

        variable_list = []

        # make sure to drop TIME and INDEX columns if they exist
        if 'INDEX' in dataframe.columns:
            dataframe = dataframe.drop(columns=['INDEX'])
            headers.remove('INDEX')
        if 'ELEM' in dataframe.columns:
            # change the data type of ELEM to string
            dataframe['ELEM'] = dataframe['ELEM'].astype(str)
            # remove leading spaces from ELEM column
            dataframe['ELEM'] = dataframe['ELEM'].str.lstrip()
            headers.remove('ELEM')
                        
        # create vtkDoubleArray for each header
        for header in headers:
            array = vtkDoubleArray()
            array.SetName(header)
            vtr.GetCellData().AddArray(array)
            variable_list.append(VisVariable(header, ValueType.Scalar, 1))


        #if self.setting.minc:
            #print(f'    MinC is enabled. Adding MinC values to the result.')
        minc_ratio = 1
        if self.setting.minc:
            minc_ratio = self.num_of_minc / self.number_of_elements
            
        for i in range(0, vtr.GetNumberOfCells()):
            elemID = self.elemIDArray.GetValue(i)
            
            index = self.sequence_dist[i]
            if 'ELEM' in dataframe.columns:
                index = dataframe['ELEM'].tolist().index(elemID)
                #elem_string = dataframe['ELEM'].iloc[index]
                #target_row = dataframe.iloc[index]
                #print(f'    Processing ELEM {elem_string} at index {index}')
            for header in headers:
                minc_index = int(index * minc_ratio)
                value = float(self.__parse_float(dataframe[header].iloc[minc_index]))
                vtr.GetCellData().GetArray(header).InsertNextValue(value)



        # update the variable list
        if self.current_out_file not in self.variable_list:
            self.variable_list[self.current_out_file] = variable_list

        
        # Put cell-centered data into points
        filter = vtkCellDataToPointData()
        filter.SetInputData(vtr)
        filter.Update()
        vtr_cell_to_points = filter.GetOutput()

        for i in range(0, vtr_cell_to_points.GetPointData().GetNumberOfArrays()):
            vtr.GetPointData().AddArray(vtr_cell_to_points.GetPointData().GetArray(i))

        self.__write_vtk_file(vtr, vtr_path)
        print(f'    ✓ Timestep {vis_time_step.time_step}:{vis_time_step.time} created: {vtr_path}')

        if VisType.Tecplot not in self.setting.vis_types:
            return
        

        if self.setting.mesh_type == MeshType.PolygonalMesh:
            print(f'    Tecplot output for polygonal mesh is not supported yet.')
            return
    
        # Start Tecplot generating
        tec_name = pathlib.Path(self.setting.input_file_paths[0]).stem
        self.tec_scalar_path = os.path.join(self.setting.vis_dir, f'{tec_name}_scalar.dat')
        firstFile = True
        if os.path.isfile(self.tec_scalar_path):
            firstFile = False
        file = open(self.tec_scalar_path, "a", encoding="utf-8")
        if len(self.setting.selected_variables_scalar) == 0:
            self.setting.selected_variables_scalar = headers

        if firstFile:
            file.write('TITLE = TECPLOT PLOT \n')
            selected_header_string = '"'+'", "'.join(self.setting.selected_variables_scalar) + '"'
            #header_string = '"'+'", "'.join(headers) + '"'
            file.write(f'VARIABLES = "X", "Y", "Z", {selected_header_string}\n')
        
        #tecplot_cell_type = 'BRICK'
        
        #time_statement = f'ZONE T ="{vis_time_step.time_step}, Time = {vis_time_step.time}", N = {vtu_cell_to_points.GetNumberOfPoints()}, E = {vtu_cell_to_points.GetNumberOfCells()}, F = FEPOINT, ET = {tecplot_cell_type}, SOLUTIONTIME = {vis_time_step.time}\n' 
        
        time_statement = f'ZONE T="{vis_time_step.time_step}, Time = {vis_time_step.time}", I={self.xyz_elem[0] + 1}, J={self.xyz_elem[1] + 1}, K={self.xyz_elem[2] + 1}, SOLUTIONTIME={vis_time_step.time}, DATAPACKING=BLOCK, VARLOCATION=({self.__get_varlocarion_string(self.setting.selected_variables_scalar)})'
        if not firstFile:
            time_statement = f'{time_statement}, D=(1,2,3,FECONNECT)'
        #if self.setting.debug:
            #time_statement = f'ZONE T ="{vis_time_step.time_step}, Time = {vis_time_step.time}", N = {vtu_cell_to_points.GetNumberOfPoints()}, E = {vtu_cell_to_points.GetNumberOfCells()}, F = FEPOINT, ET = {tecplot_cell_type}\n' 
        file.write(f'{time_statement}\n')
        max_line_length = 20000
        # X, Y, Z
        if firstFile:
            for point_idx in range(0, 3):
                line_string = ''
                for i in range(0, vtr.GetNumberOfPoints()):
                    point = vtr.GetPoint(i)
                    #file.write(str(point[0]) + " ")
                    if len(line_string) + len(str(point[point_idx])) + 1 > max_line_length:
                        # write the current line to file
                        file.write(f'{line_string}\n')
                        # reset the line string
                        line_string = ''
                    line_string = f'{line_string}{str(point[point_idx])} '
               
                file.write(f'{line_string}\n')

        # Other data
        for header in self.setting.selected_variables_scalar:
            array = vtr.GetCellData().GetArray(header)
            line_string = ''
            for e in range(0, vtr.GetNumberOfCells()):
                #file.write(f'{str(array.GetComponent(e, 0))} ')
                if len(line_string) + len(str(array.GetValue(e))) + 1 > max_line_length:
                    # write the current line to file
                    file.write(f'{line_string}\n')
                    # reset the line string
                    line_string = ''
                line_string = f'{line_string}{str(array.GetValue(e))} '
            file.write(f'{line_string}\n')
 
        file.close()

    def __get_tec_vector_headers(self, headers):
        vector_headers = []
        for header in headers:
            vector_headers.append(f'{header}_X')
            vector_headers.append(f'{header}_Y')
            vector_headers.append(f'{header}_Z')
        return vector_headers
    
    def __get_varlocarion_string(self, headers):
        var_string = ''
        for i in range(0, len(headers)):
            if i == len(headers)-1:
                var_string = f'{var_string}{str(i+4)}=CELLCENTERED'
            else:
                var_string = f'{var_string}{str(i+4)}=CELLCENTERED,'
        return var_string
    
    # write the vector result for one timestep
    def __write_vector_result(self, vis_time_step, dataframe, csv_headers):
        
        headers = csv_headers.copy()
        index = self.time_steps_list.index(vis_time_step)
        extension = os.path.splitext(self.main_geometry)[1]
        vtr_path = os.path.join(self.setting.vis_dir, 'paraview', f'time_step_{vis_time_step.time_step}{extension}')
        self.time_steps_list[index].vtu_file_name = vtr_path

        if not os.path.exists(vtr_path):
            vector_vtr = self.__read_vtk_file(self.main_geometry)
            # add time step data
            timesteps = vtkDoubleArray()
            timesteps.SetName("TimeValue")
            timesteps.SetNumberOfTuples(1)
            timesteps.SetNumberOfComponents(1)
            timesteps.SetTuple1(0, vis_time_step.time)
            #timesteps.SetTuple2(1, 100000)
            vector_vtr.SetFieldData(vtkFieldData())
            vector_vtr.GetFieldData().AddArray(timesteps)
         
        else:
            vector_vtr = self.__read_vtk_file(vtr_path) 

        vtu_reader = vtkXMLUnstructuredGridReader()
        vtu_reader.SetFileName(self.elem_conne_path)
        vtu_reader.Update()
        conne_vtu = vtu_reader.GetOutput()

        # make sure to drop TIME and INDEX columns if they exist
        if 'INDEX' in dataframe.columns:
            dataframe = dataframe.drop(columns=['INDEX'])
            headers.remove('INDEX')
        if 'ELEM1' in dataframe.columns:
            # remove leading spaces from ELEM column
            dataframe['ELEM1'] = dataframe['ELEM1'].astype(str)
            dataframe['ELEM1'] = dataframe['ELEM1'].str.lstrip()
            headers.remove('ELEM1')
        if 'ELEM2' in dataframe.columns:
            # remove leading spaces from ELEM column
            dataframe['ELEM2'] = dataframe['ELEM2'].astype(str)
            dataframe['ELEM2'] = dataframe['ELEM2'].str.lstrip()
            headers.remove('ELEM2')

        variable_list = []
    
        # find max number of cell connections of a element
        num_of_components = 3
        for elem_id in range(0, conne_vtu.GetNumberOfPoints()):
            cellIDs = vtkIdList()
            conne_vtu.GetPointCells(elem_id, cellIDs)
            if cellIDs.GetNumberOfIds() > num_of_components:
                num_of_components = cellIDs.GetNumberOfIds() 


        # create double array for each header
        for header in headers:
            #if not header == 'ELEM1' and not header == 'ELEM2' and not header == 'INDEX':
            array = vtkDoubleArray()
            array.SetName(header)
            array.SetNumberOfComponents(num_of_components)
            array.SetNumberOfTuples(vector_vtr.GetNumberOfCells())
            for i in range(0, num_of_components):
                # set the default value to 0
                array.FillComponent(i, 0)
            vector_vtr.GetCellData().AddArray(array)
            
            variable_list.append(VisVariable(header, ValueType.Vector, 3))

        if self.current_out_file not in self.variable_list:
            self.variable_list[self.current_out_file] = variable_list
                

        # prepare cell data array for cells in conne_vtu
        for header in headers:
            array = vtkDoubleArray()
            array.SetName(header)
            conne_vtu.GetCellData().AddArray(array)

        # add celldata to cells in elem_conn
        for cell_id in range(0, conne_vtu.GetNumberOfCells()):
            for header in headers:
                    value = dataframe.loc[cell_id, header]
                    conne_vtu.GetCellData().GetArray(header).InsertNextValue(value)
        #self.__write_vtk_file(
            #conne_vtu, self.elem_conne_path)

        # create the vector data
        for elem_id in range(0, conne_vtu.GetNumberOfPoints()):
            cellIDs = vtkIdList()
            conne_vtu.GetPointCells(elem_id, cellIDs)
            for i in range(0, cellIDs.GetNumberOfIds()):
                cellID = cellIDs.GetId(i)

                for header in headers:
                    #value = dataframe.loc[next_id, header]
                    value = conne_vtu.GetCellData().GetArray(header).GetValue(cellID)
                    vector_vtr.GetCellData().GetArray(header).SetComponent(elem_id, i, value)

        # Put cell-centered data into points
        filter = vtkCellDataToPointData()
        filter.SetInputData(vector_vtr)
        filter.Update()
        vtr_cell_to_points = filter.GetOutput()

        for i in range(0, vtr_cell_to_points.GetPointData().GetNumberOfArrays()):
            vector_vtr.GetPointData().AddArray(vtr_cell_to_points.GetPointData().GetArray(i))

        self.__write_vtk_file(
            vector_vtr, self.time_steps_list[index].vtu_file_name)
        print(f'    ✓ Timestep {vis_time_step.time_step}:{vis_time_step.time} created: {vtr_path}')

        if VisType.Tecplot not in self.setting.vis_types:
            return


        if self.setting.mesh_type == MeshType.PolygonalMesh:
            print(f'    Tecplot output for polygonal mesh is not supported yet.')
            return
        
        # Start Tecplot generating
        tec_name = pathlib.Path(self.setting.input_file_paths[0]).stem
        self.tec_vector_path = os.path.join(self.setting.vis_dir, f'{tec_name}_vector.dat')
        firstFile = True
        if os.path.isfile(self.tec_vector_path):
            firstFile = False
        file = open(self.tec_vector_path, "a", encoding="utf-8")

        #selected_header_string = '"'+'", "'.join(self.setting.selected_variables_scalar) + '"'
        if len(self.setting.selected_variables_vector) == 0:
            self.setting.selected_variables_vector = headers
        vector_headers = self.__get_tec_vector_headers(self.setting.selected_variables_vector)

        # add header
        if firstFile:
            file.write('TITLE = TECPLOT PLOT \n')
            header_string = '"'+'", "'.join(vector_headers) + '"'

            file.write(f'VARIABLES = "X", "Y", "Z", {header_string}\n')
        
        time_statement = f'ZONE T="{vis_time_step.time_step}, Time = {vis_time_step.time}", I={self.xyz_elem[0] + 1}, J={self.xyz_elem[1] + 1}, K={self.xyz_elem[2] + 1}, SOLUTIONTIME={vis_time_step.time}, DATAPACKING=BLOCK, VARLOCATION=({self.__get_varlocarion_string(vector_headers)})'
        if not firstFile:
            time_statement = f'{time_statement}, D=(1,2,3,FECONNECT)'
        #if self.setting.debug:
            #time_statement = f'ZONE T ="{vis_time_step.time_step}, Time = {vis_time_step.time}", N = {vtu_cell_to_points.GetNumberOfPoints()}, E = {vtu_cell_to_points.GetNumberOfCells()}, F = FEPOINT, ET = {tecplot_cell_type}\n' 
        file.write(f'{time_statement}\n')

        max_line_length = 20000
        # X, Y, Z
        if firstFile:   
            for point_idx in range(0, 3):
                line_string = ''
                for i in range(0, vector_vtr.GetNumberOfPoints()):
                    point = vector_vtr.GetPoint(i)
                    #file.write(str(point[0]) + " ")
                    if len(line_string) + len(str(point[point_idx])) + 1 > max_line_length:
                        # write the current line to file
                        file.write(f'{line_string}\n')
                        # reset the line string
                        line_string = ''
                    line_string = f'{line_string}{str(point[point_idx])} '
                file.write(f'{line_string}\n')



        # Other data
        for header in self.setting.selected_variables_vector:

            array = vector_vtr.GetCellData().GetArray(header)

            for dim_idx in range(0, 3):
                line_string = ''
                for e in range(0, vector_vtr.GetNumberOfCells()):
                    #file.write(f'{str(array.GetComponent(e, 0))} ')
                    if len(line_string) + len(str(array.GetComponent(e, dim_idx))) + 1 > max_line_length:
                        # write the current line to file
                        file.write(f'{line_string}\n')
                        # reset the line string
                        line_string = ''
                    line_string = f'{line_string}{str(array.GetComponent(e, dim_idx))} '
                file.write(f'{line_string}\n')

        file.close()


    def __create_elem_conne(self):

        '''
            read elem and conn files into dataframe
        '''
        
        elem_colspecs = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 40),
                         (40, 50), (50, 60), (60, 70), (70, 80)]  # define column widths
        self.eleme_buffer.seek(0)
        elem_df = pd.read_fwf(self.eleme_buffer, colspecs=elem_colspecs, header=None,
                              names=['ELEME', 'NSEQ', 'NADD', 'MA12',
                                     'VOLX', 'AHTX', 'PMX', 'X', 'Y', 'Z'],
                              dtype={'ELEME': str, 'NSEQ': float, 'NADD': float, 'MA12': str, 'VOLX': float, 'AHTX': float, 'PMX': float, 'X': float, 'Y': float, 'Z': float})
        
        conn_colspecs = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30),
                         (30, 40), (40, 50), (50, 60), (60, 70), (70, 80)]  # define column widths

        self.conne_buffer.seek(0)
        conn_df = pd.read_fwf(self.conne_buffer, colspecs=conn_colspecs, header=None,
                              names=['ELEM_1', 'ELEM_2', 'NSEQ', 'NAD1', 'NAD2',
                                     'ISOT', 'D1', 'D2', 'AREAX', 'BETAX', 'SIGX'],
                              dtype={'ELEM_1': str, 'ELEM_2': str, 'NSEQ': float, 'NAD1': float, 'NAD2': float, 'ISOT': float, 'D1': float, 'D2': float, 'AREAX': float, 'BETAX': float, 'SIGX': float})

        
        elem_df['original_index'] = range(0, len(elem_df))
        if self.__check_isReverse(elem_df):
            #Sort all dataframes
            elem_df = elem_df.sort_values(['Z', 'Y', 'X'], ascending = [True, True, True])
            elem_df = elem_df.reset_index(drop=True)
            elem_df.reset_index()


        # create material map
        unique_mats = elem_df['MA12'].unique()
        # Create a dictionary mapping index -> MAT value
        mat_mapping = {mat: i for i, mat in enumerate(unique_mats)}
        
        '''
            create vtk points from elem
        '''
        vtk_points = vtkPoints()
        elemIDArray = vtkStringArray()
        elemIDArray.SetName('ELEME')
        matArray = vtkStringArray()
        matArray.SetName('Material')
        matIDArray = vtkIntArray()
        matIDArray.SetName('Material_ID')
        pmxArray = vtkDoubleArray()
        pmxArray.SetName('PMX')
        volxArray = vtkDoubleArray()
        volxArray.SetName('VOLX')
        elem_id_dist = {}
        self.sequence_dist = {}
        self.number_of_elements = len(elem_df.values)
        length = len(elem_df.values)
        for i in range(0, len(elem_df.values)):
            # y = elem_df['Y'][i]
            #[x, y, z] = [elem_df['X'][i], elem_df['Y'][i], elem_df['Z'][i]]
            vtk_points.InsertNextPoint(self.__parse_float(elem_df['X'][i]), self.__parse_float(
                elem_df['Y'][i]), self.__parse_float(elem_df['Z'][i]))
            elem_id = elem_df['ELEME'][i].strip()
            elemIDArray.InsertNextValue(elem_id)
            elem_id_dist[elem_id] = i
            original_index = int(elem_df['original_index'][i])
            self.sequence_dist[i] = original_index
            volxArray.InsertNextValue(self.__parse_float(elem_df['VOLX'][i]))
            matArray.InsertNextValue(elem_df['MA12'][i])
            matIDArray.InsertNextValue(mat_mapping[elem_df['MA12'][i]])
            pmxArray.InsertNextValue(self.__parse_float(elem_df['PMX'][i]))
        
        self.elemIDArray = elemIDArray

        '''
        compute permeability
        '''
        rock_colspecs = [(0, 5), (30, 40), (40, 50), (50, 60), (100, 110)]  # define column widths
        rock_names = ['MAT', 'PER_1', 'PER_2', 'PER_3', 'SGR']
        self.rocks_buffer.seek(0)
        rocks_df = pd.read_fwf(self.rocks_buffer, colspecs=rock_colspecs, header=None,
                              names=rock_names,
                              dtype={'MAT':str, 'PER_1':str, 'PER_2':str, 'PER_3':str, 'SGR':str})
        
        #sgr_dict = {}
        self.rock_dict = None
        if len(rocks_df) > 0:
            #rock_dict = {}
            rock_dict = []
            for i in range(0, len(rocks_df)):
                #rock_dict[rocks_df['MAT'][i]] = [self.parse_float(rocks_df['PER_1'][i]), self.parse_float(rocks_df['PER_2'][i]), self.parse_float(rocks_df['PER_3'][i])]
                rock_dict.append({
                    'id': i,
                    'rock_name': rocks_df['MAT'][i],
                    'per_1':self.__parse_float(rocks_df['PER_1'][i]),
                    'per_2':self.__parse_float(rocks_df['PER_2'][i]),
                    'per_3':self.__parse_float(rocks_df['PER_3'][i]),
                    'sgr':self.__parse_float(rocks_df['SGR'][i])
                })
                #sgr_dict[rocks_df['MAT'][i]] = self.__parse_float(rocks_df['SGR'][i])
            # compute per
            per_array = vtkDoubleArray()
            per_array.SetName('Permeability')

            sgr_array = vtkDoubleArray()
            sgr_array.SetName('sgr')
            for i in range(0, len(elem_df.values)):
                value = 0

                mat = matArray.GetValue(i)
                if self.__isInt(mat):  
                    mat_id = int(mat)
                    value = pmxArray.GetValue(i) * rock_dict[mat_id-1]['per_1']
                    sgr = rock_dict[mat_id-1]['sgr']
                else:
                    rock_item = [rock for rock in rock_dict if rock['rock_name'] == mat]
                    #if mat in rock_dict:
                    value = pmxArray.GetValue(i) * rock_item[0]['per_1']
                    sgr = rock_item[0]['sgr']
                
                per_array.InsertNextValue(value)
                sgr_array.InsertNextValue(sgr)
            self.rock_dict = rock_dict



        '''
            create connection cell array from conne
        '''
        d1_array = vtkDoubleArray()
        d1_array.SetName('D1')
        d2_array = vtkDoubleArray()
        d2_array.SetName('D2')
        area_array = vtkDoubleArray()
        area_array.SetName('AREAX')

        line_cell_array = vtkCellArray()
        for i in range(0, len(conn_df.values)):
            elem_1_id = conn_df['ELEM_1'][i].strip()
            point_1_id = elem_id_dist[elem_1_id]
            elem_2_id = conn_df['ELEM_2'][i].strip()
            point_2_id = elem_id_dist[elem_2_id]
            # elem_conne_dist[point_id]
            cell = vtkLine()
            cell.GetPointIds().SetNumberOfIds(2)
            cell.GetPointIds().SetId(0, point_1_id)
            cell.GetPointIds().SetId(1, point_2_id)
            line_cell_array.InsertNextCell(cell)
            d1_array.InsertNextValue(conn_df['D1'][i])
            d2_array.InsertNextValue(conn_df['D2'][i])
            area_array.InsertNextValue(conn_df['AREAX'][i])

        '''
            create vtu to display elem and conne 
        '''
        self.elem_conne_path = os.path.join(
            self.setting.vis_dir, "elem_conne.vtu")
        elem_conne_vtu = vtkUnstructuredGrid()

        elem_conne_vtu.SetPoints(vtk_points)
        elem_conne_vtu.GetPointData().AddArray(elemIDArray)
        elem_conne_vtu.GetPointData().AddArray(volxArray)
        elem_conne_vtu.GetPointData().AddArray(matArray)
        elem_conne_vtu.GetPointData().AddArray(matIDArray)

        elem_conne_vtu.SetCells(4, line_cell_array)
        elem_conne_vtu.GetCellData().AddArray(d1_array)
        elem_conne_vtu.GetCellData().AddArray(d2_array)
        elem_conne_vtu.GetCellData().AddArray(area_array)
        vtu_writer = vtkXMLUnstructuredGridWriter()
        vtu_writer.SetFileName(self.elem_conne_path)
        vtu_writer.SetInputData(elem_conne_vtu)
        vtu_writer.Write()

        if os.path.exists(self.elem_conne_path):
            print(f'    ✓ Elements and connections created: {self.elem_conne_path}')
            
        self.number_of_connections = elem_conne_vtu.GetNumberOfCells()

    def __create_main_geometry(self):
       

        '''
            find number of elements in x, y, z directions 
            TODO: check if vtu bound is inside user input bounds
        '''
       

       # prepare the vtu file
        vtu_reader = vtkXMLUnstructuredGridReader()
        vtu_reader.SetFileName(self.elem_conne_path)
        vtu_reader.Update()
        elem_conne_vtu = vtu_reader.GetOutput()

        d1_array = elem_conne_vtu.GetCellData().GetArray('D1')
        d2_array = elem_conne_vtu.GetCellData().GetArray('D2')
        #elemIDArray = elem_conne_vtu.GetPointData().GetArray('ELEME')
        volxArray = elem_conne_vtu.GetPointData().GetArray('VOLX')
        matArray = elem_conne_vtu.GetPointData().GetArray('Material')
        matIDArray = elem_conne_vtu.GetPointData().GetArray('Material_ID')
        pmxArray = elem_conne_vtu.GetPointData().GetArray('PMX')
        if self.rock_dict is not None:
            per_array = elem_conne_vtu.GetCellData().GetArray('Permeability')
            sgr_array = elem_conne_vtu.GetCellData().GetArray('sgr')
        


        # get connection bound
        vtu_bounds = elem_conne_vtu.GetBounds()

        # create array to keep x, y, z elements
        xyz_elem = []
        xyz_elem.append(0)  # add x eleme
        xyz_elem.append(0)  # add y eleme
        xyz_elem.append(0)  # add z eleme

        if vtu_bounds[0] == vtu_bounds[1]:
            xyz_elem[0] = 1
        if vtu_bounds[2] == vtu_bounds[3]:
            xyz_elem[1] = 1
        if vtu_bounds[4] == vtu_bounds[5]:
            xyz_elem[2] = 1

        # find x, y , z number of  structured points
        for i in range(0, elem_conne_vtu.GetNumberOfPoints()):
            point = elem_conne_vtu.GetPoint(i)
            if xyz_elem[0] == 0 and point[0] == vtu_bounds[1]:
                xyz_elem[0] = i+1
            if xyz_elem[1] == 0 and point[0] == vtu_bounds[1] and point[1] == vtu_bounds[3]:
                if xyz_elem[0] != 0:
                    xyz_elem[1] = int((i+1)/xyz_elem[0])
                    break

        if xyz_elem[1] != 0 and xyz_elem[0] != 0:
            xyz_elem[2] = int(elem_conne_vtu.GetNumberOfPoints() / xyz_elem[0] / xyz_elem[1])
        self.xyz_elem = xyz_elem

        range_ratio = 1
        np_xyz_elem = np.array(xyz_elem)
        if xyz_elem[0] != 0 and xyz_elem[1] != 0 and xyz_elem[2] != 0:
            range_ratio = np.max(np_xyz_elem)/np.min(np_xyz_elem)



        if all(xyz_elem) and range_ratio < 1000:
            if os.path.exists(self.setting.corners_file):
                self.setting.mesh_type = MeshType.StructuredGridOrth
            else:
                self.setting.mesh_type = MeshType.RegularGrid
                
        else:
            is_parallel = self.__checkParallel(elem_conne_vtu)
            # check if polygonal mesh
            if os.path.exists(self.setting.corners_file):

                if is_parallel:
                    self.setting.mesh_type = MeshType.StructuredGridFree
                else:
                    self.setting.mesh_type = MeshType.PolygonalMesh
            else:
                print('Error: Your mesh type is not supported')
                sys.exit(1)

        print(f'    Mesh type: {self.setting.mesh_type.name}')

        # Read corners file to dataframe
        if os.path.exists(self.setting.corners_file):
            corners_buffer = io.StringIO()
            csv_headers = []
            line_number = -1
            with open(self.setting.corners_file, encoding="utf-8") as f:
                for line in f:
                    line_number = line_number + 1
                    values = line.strip().split(',')
                    values = [x.replace('"', '') for x in values]
                    if line_number == 0:
                        
                        csv_headers = [x.strip() for x in values]
                        csv_headers = csv_headers[:3]
                        header_string = ','.join(csv_headers)
                        corners_buffer.write(header_string + '\n')
                    else:
                        corners_buffer.write(','.join(values[:3]) + '\n')
            corners_buffer.seek(0)
            corners_df = pd.read_csv(corners_buffer, sep=',', header=0)
 
            # Write four corners to vtu
            all_points = vtkPoints()
            all_cells = vtkCellArray()

            for index, row in corners_df.iterrows():
                all_points.InsertNextPoint(row["X"], row["Y"], row["Z"])
                cell = vtkVertex()
                cell.GetPointIds().SetNumberOfIds(1)
                cell.GetPointIds().SetId(0, index)
                all_cells.InsertNextCell(cell)
            
            corners_vtu = vtkUnstructuredGrid()
            corners_vtu.SetPoints(all_points)
            corners_vtu.SetCells(1, all_cells)
            print(f'    Read corners from {self.setting.corners_file}')
            
            # write four corners to vtu (debugging)
            if self.setting.debug:
                corners_vtu_writer = vtkXMLUnstructuredGridWriter()
                corners_vtu_writer.SetFileName(os.path.join(self.setting.vis_dir, "corners.vtu"))
                corners_vtu_writer.SetInputData(corners_vtu)
                corners_vtu_writer.Write()



        if self.setting.mesh_type == MeshType.RegularGrid:
            '''
                * for RGrid from MeshMaker
                find index for determining x, y, z index
            '''
            xyz_index = []
            xyz_index.append([])  # add x index
            xyz_index.append([])  # add y index
            xyz_index.append([])  # add z index

            for i in range(0, xyz_elem[0]):
                xyz_index[0].append(i)
            for i in range(0, xyz_elem[1]):
                xyz_index[1].append(i * xyz_elem[0])
            for i in range(0, xyz_elem[2]):
                xyz_index[2].append(i * xyz_elem[0] * xyz_elem[1])
                xyz_coordinates = []
                xyz_coordinates.append([])  # add x coordinates
                xyz_coordinates.append([])  # add y coordinates
                xyz_coordinates.append([])  # add z coordinates

            for key in range(0, len(xyz_index)):
                for index in xyz_index[key]:
                    point = elem_conne_vtu.GetPoint(index)
                    cellIDs = vtkIdList()
                    # find all cells connect to this point
                    elem_conne_vtu.GetPointCells(index, cellIDs)
                    d1 = 0
                    d2 = 0
                    find_next = False

                    for i in range(0, cellIDs.GetNumberOfIds()):
                        cellID = cellIDs.GetId(i)
                        cell = elem_conne_vtu.GetCell(cellID)
                        # find next id in line element

                        next_id = cell.GetPointId(1)
                        if next_id == index:
                            next_id = cell.GetPointId(0)
                        if next_id in xyz_index[key]:
                            d1 = d1_array.GetValue(cellID)
                            d2 = d2_array.GetValue(cellID)
                            find_next = True
                            break

                    # if it has any connection to other node
                    if find_next:
                        # add first node
                        if len(xyz_coordinates[key]) == 0:
                            first_value = point[key] - d1
                            if self.setting.known_bounds:
                                first_value = self.setting.bounds[key*2]
                            xyz_coordinates[key].append(first_value)

                        # add current node
                        xyz_coordinates[key].append(point[key] + d1)

                        # add last node
                        if len(xyz_coordinates[key]) == xyz_elem[key]:
                            last_value = point[key] + d1 + (2*d2)
                            if self.setting.known_bounds:
                                last_value = self.setting.bounds[key*2+1]
                            xyz_coordinates[key].append(last_value)

                    # if there is only one element in this dimension
                    elif len(xyz_index[key]) == 1:
                        if self.setting.known_bounds:
                            xyz_coordinates[key].append(self.setting.bounds[key*2])
                            xyz_coordinates[key].append(
                                self.setting.bounds[key*2+1])
                        else:
                            if point[key] == 0:
                                # find max elem
                                xyz_elem_np_array = np.array(
                                    (xyz_elem[0], xyz_elem[1], xyz_elem[2]))
                                max = xyz_elem_np_array.max()
                                index = xyz_elem.index(max)
                                guess_value = (
                                    vtu_bounds[index*2+1] - vtu_bounds[index]) / max
                                xyz_coordinates[key].append(-1 * guess_value)
                                xyz_coordinates[key].append(guess_value)
                            else:
                                xyz_coordinates[key].append(
                                    point[key] - abs(point[key]))
                                xyz_coordinates[key].append(
                                    point[key] + abs(point[key]))

            '''
                create vtk rgid and translate it to vtu
            '''
            # self.rgrid_vtr = os.path.join(self.setting.vis_dir, "temp_rgrid.vtr")
            xyz_coords_array = []
            xyz_coords_array.append(vtkDoubleArray())
            xyz_coords_array.append(vtkDoubleArray())
            xyz_coords_array.append(vtkDoubleArray())

            for key in range(0, len(xyz_coords_array)):
                for value in xyz_coordinates[key]:
                    xyz_coords_array[key].InsertNextValue(value)

            rGrid = vtkRectilinearGrid()
            rGrid.SetDimensions(xyz_elem[0]+1, xyz_elem[1]+1, xyz_elem[2]+1)

            rGrid.SetXCoordinates(xyz_coords_array[0])
            rGrid.SetYCoordinates(xyz_coords_array[1])
            rGrid.SetZCoordinates(xyz_coords_array[2])
            rGrid.GetCellData().AddArray(self.elemIDArray)
            rGrid.GetCellData().AddArray(volxArray)
            rGrid.GetCellData().AddArray(matArray)

            rGrid.GetCellData().AddArray(matIDArray)
            if self.rock_dict is not None:
                rGrid.GetCellData().AddArray(per_array)
                rGrid.GetCellData().AddArray(sgr_array)
            rGrid.GetCellData().AddArray(pmxArray)

            self.main_geometry = os.path.join(
                self.setting.vis_dir, "main_geometry.vtr")
            self.__write_vtk_file(rGrid, self.main_geometry)
            

        if self.setting.mesh_type == MeshType.StructuredGridOrth:

            #corners_df.to_csv(os.path.join(self.setting.vis_dir, "corners.csv"), index=False)
            # Step 1: Group by `x` and `y`, and sort `z` within each group
            corners_df = corners_df.groupby(['X', 'Y'], group_keys=False).apply(lambda group: group.sort_values(by='Z'))
            # Step 3: Set the new index using `x` and `y` columns
            corners_df = corners_df.set_index(['X', 'Y']).sort_index()

            distinct_x = corners_df.index.get_level_values('X').unique()
            distinct_y = corners_df.index.get_level_values('Y').unique()

            vts = vtkStructuredGrid()
            vts.SetDimensions(self.xyz_elem[0]+1, self.xyz_elem[1]+1, self.xyz_elem[2]+1)
            vts_points = vtkPoints()

            for z_index in range(0, self.xyz_elem[2]+1):
                for y_index in range(0, len(distinct_y)):
                    for x_index in range(0, len(distinct_x)):
                        x = distinct_x[x_index]
                        y = distinct_y[y_index]
                        z_value = corners_df.loc[(x, y), 'Z'].iloc[z_index]
                        vts_points.InsertNextPoint(x, y, z_value)
            
            vts.SetPoints(vts_points) 
            vts.GetCellData().AddArray(self.elemIDArray)
            vts.GetCellData().AddArray(volxArray)
            vts.GetCellData().AddArray(matArray)

            vts.GetCellData().AddArray(matIDArray)
            if self.rock_dict is not None:
                vts.GetCellData().AddArray(per_array)
                vts.GetCellData().AddArray(sgr_array)
            self.main_geometry = os.path.join(self.setting.vis_dir, "main_geometry.vts")
            self.__write_vtk_file(vts, self.main_geometry)
            
        
        if self.setting.mesh_type == MeshType.StructuredGridFree:
            #initialize the locator
            pointTree = vtkPointLocator()
            pointTree.SetDataSet(corners_vtu)
            pointTree.BuildLocator()
            
            cell_array = vtkCellArray()

            for i in range(0, elem_conne_vtu.GetNumberOfPoints()):
                point = elem_conne_vtu.GetPoint(i)
                result = vtkIdList()
                #find the closest point to the the center of each element
                pointTree.FindClosestNPoints(8, point, result)
                result.Sort()

                cell = vtkHexahedron()
                cell.GetPointIds().SetNumberOfIds(8)
                # need to sort the points in the rigth order
                points_array = []

                for j in range(0, 8):
                    points_array.append(corners_vtu.GetPoint(result.GetId(j)))

                points_array = np.array(points_array)
                result_index = self.__reorder_hexahedron(points_array)
                
                for j in range(0, 8):
                    cell.GetPointIds().SetId(j, result.GetId(result_index[j]))
                cell_array.InsertNextCell(cell)
        
            auto_corner_vtu = vtkUnstructuredGrid()
            auto_corner_vtu.SetPoints(all_points)
            auto_corner_vtu.SetCells(12, cell_array)
            
            # TODO: compute mesh quality and fix bad cells
            
            
            auto_corner_vtu.GetCellData().AddArray(self.elemIDArray)
            auto_corner_vtu.GetCellData().AddArray(volxArray)
            auto_corner_vtu.GetCellData().AddArray(matArray)
            if self.rock_dict is not None:
                auto_corner_vtu.GetCellData().AddArray(per_array)
                auto_corner_vtu.GetCellData().AddArray(sgr_array)
            auto_corner_vtu.GetCellData().AddArray(matIDArray)
            self.main_geometry = os.path.join(self.setting.vis_dir, "main_geometry.vtu")
            self.__write_vtk_file(auto_corner_vtu, self.main_geometry)
            

        if self.setting.mesh_type == MeshType.PolygonalMesh:
            
            # == Create `distinct_points` and `labeled_temp_elem` == 
            # Extract points from the grid
            points = np.array([elem_conne_vtu.GetPoint(i) for i in range(elem_conne_vtu.GetNumberOfPoints())])
            # Convert to Pandas DataFrame for easier manipulation
            df = pd.DataFrame(points, columns=["x", "y", "z"])
            # Round (x, y) values to avoid floating-point precision issues
            df[["x", "y"]] = df[["x", "y"]].round(10)
            
            #df.to_csv(os.path.join(self.setting.vis_dir, 'all_points.csv'))
            # Find distinct (x, y) sets and create an index mapping
            distinct_xy = df[["x", "y"]].drop_duplicates().reset_index(drop=True)
            distinct_xy["Elem_Index"] = distinct_xy.index  # Assign an index to each unique (x, y)
            #distinct_xy.to_csv(os.path.join(self.setting.vis_dir, 'distinct_xy.csv'))

            # add distinct_xy to a vtkpoints object
            all_points = vtkPoints()
            all_points.SetDataTypeToDouble()
            for i in range(len(distinct_xy)):
                values = distinct_xy.iloc[i].values
                all_points.InsertNextPoint(values[0], values[1], 0)

            # create a polydata object
            distinct_points = vtkPolyData()
            distinct_points.SetPoints(all_points)

            cell_array = vtkCellArray()
            for i in range(all_points.GetNumberOfPoints()):
                vertex = vtkVertex()
                vertex.GetPointIds().SetId(0, i)
                cell_array.InsertNextCell(vertex)

            distinct_points.SetVerts(cell_array)
            xy_index_labels = distinct_xy["Elem_Index"].to_numpy()
            elem_id_array = vtkIntArray()
            elem_id_array.SetName("Elem_Index")
            for i in range(len(xy_index_labels)):
                elem_id_array.InsertNextValue(int(xy_index_labels[i]))
            distinct_points.GetPointData().AddArray(elem_id_array)

            if self.setting.debug:
                # Write the distinct points to a VTU file for debugging
                writer = vtkXMLPolyDataWriter()
                writer.SetInputData(distinct_points)
                writer.SetFileName(os.path.join(self.setting.vis_dir, 'distinct_points.vtp'))
                writer.Write()


            # Merge the index back to the original DataFrame
            df = df.merge(distinct_xy, on=["x", "y"], how="left")

            # Compute Z descending order within each (x, y) group
            df["Horizon_ID"] = df.groupby(["x", "y"])["z"].rank(method="first", ascending=True).astype(int) - 1

            # Convert the labels to NumPy arrays

            z_order_labels = df["Horizon_ID"].to_numpy()
            xy_index_labels = df["Elem_Index"].to_numpy()

            # Add labels to the VTU file
            xy_index_array = vtkIntArray()
            xy_index_array.SetName("Elem_Index")
            xy_index_array.SetNumberOfComponents(1)
            xy_index_array.SetNumberOfTuples(len(xy_index_labels))

            z_order_array = vtkIntArray()
            z_order_array.SetName("Horizon_ID")
            z_order_array.SetNumberOfComponents(1)
            z_order_array.SetNumberOfTuples(len(z_order_labels))

            for i, (xy_idx, z_ord) in enumerate(zip(xy_index_labels, z_order_labels)):
                xy_index_array.SetValue(i, int(xy_idx))
                z_order_array.SetValue(i, int(z_ord))

            labeled_temp_elem = vtkUnstructuredGrid()
            labeled_temp_elem.DeepCopy(elem_conne_vtu)
            labeled_temp_elem.GetPointData().AddArray(xy_index_array)
            labeled_temp_elem.GetPointData().AddArray(z_order_array)
            # Write the modified VTU file with labels
            if self.setting.debug:
                writer = vtkXMLUnstructuredGridWriter()
                writer.SetFileName(os.path.join(self.setting.vis_dir, "labeled_temp_elem.vtu"))
                writer.SetInputData(labeled_temp_elem)
                writer.Write()


            # == Create a VTK 2D `voronoi` mesh ==
            # Create a Voronoi diagram from the cell centers
            print("crating voronoi...")
            voro = vtkVoronoi2D()
            voro.SetInputData(distinct_points)
            voro.SetMaximumNumberOfTileClips(distinct_points.GetNumberOfPoints())
            #voro.set
            voro.Update()
            voronoi = voro.GetOutput()

            if self.setting.debug:
                # Write the Voronoi mesh to a VTU file for debugging
                voronoi_writer = vtkXMLPolyDataWriter()
                voronoi_writer.SetInputData(voronoi)
                voronoi_writer.SetFileName(os.path.join(self.setting.vis_dir, 'voronoi.vtp'))
                voronoi_writer.Write()
                print(f'    ✓ Main voronoi created: {os.path.join(self.setting.vis_dir, "voronoi.vtp")}')


            # Count Layer
            
            number_of_layers = elem_conne_vtu.GetNumberOfPoints() // distinct_points.GetNumberOfPoints()
            print(f'number_of_layers: {number_of_layers}')
    
            # == Create `distinct_corners_points` and `labeled_corners` ==
            # Clean the grid
            clean_filter = vtkCleanUnstructuredGrid()
            clean_filter.SetInputData(corners_vtu)
            clean_filter.Update()
            labeled_corners = clean_filter.GetOutput()

            # Extract points from the grid
            points = np.array([labeled_corners.GetPoint(i) for i in range(labeled_corners.GetNumberOfPoints())])

            # Convert to Pandas DataFrame for easier manipulation
            df = pd.DataFrame(points, columns=["x", "y", "z"])

            # Round (x, y) values to avoid floating-point precision issues
            df[["x", "y"]] = df[["x", "y"]].round(6)

            # Find distinct (x, y) sets and create an index mapping
            distinct_xy = df[["x", "y"]].drop_duplicates().reset_index(drop=True)

            distinct_xy["XY_Index"] = distinct_xy.index  # Assign an index to each unique (x, y)


            # add distinct_xy to a vtkpoints object
            index_array = vtkIntArray()
            index_array.SetName("XY_Index")
            all_points = vtkPoints() 
            all_points.SetDataTypeToDouble()
            for i in range(len(distinct_xy)):
                values = distinct_xy.iloc[i].values
                all_points.InsertNextPoint(values[0], values[1], 0)
                index_array.InsertNextValue(int(values[2]))
            # create a polydata object
            distinct_corners_points = vtkPolyData()
            distinct_corners_points.SetPoints(all_points)
            distinct_corners_points.GetPointData().AddArray(index_array)

            cell_array = vtkCellArray()
            for i in range(all_points.GetNumberOfPoints()):
                vertex = vtkVertex()
                vertex.GetPointIds().SetId(0, i)
                cell_array.InsertNextCell(vertex)

            distinct_corners_points.SetVerts(cell_array)

            if self.setting.debug:
                # Write the distinct points to a VTU file for debugging
                writer = vtkXMLPolyDataWriter()
                writer.SetInputData(distinct_corners_points)
                writer.SetFileName(os.path.join(self.setting.vis_dir, 'distinct_corners_points.vtp'))
                writer.Write()



            # Merge the index back to the original DataFrame
            df = df.merge(distinct_xy, on=["x", "y"], how="left")

            # Compute Z descending order within each (x, y) group
            df["Z_Order"] = df.groupby(["x", "y"])["z"].rank(method="first", ascending=True).astype(int) - 1

            # Convert the labels to NumPy arrays
            xy_index_labels = df["XY_Index"].to_numpy()
            z_order_labels = df["Z_Order"].to_numpy()

            # Add labels to the VTU file
            xy_index_array = vtkIntArray()
            xy_index_array.SetName("XY_Index")
            xy_index_array.SetNumberOfComponents(1)
            xy_index_array.SetNumberOfTuples(len(xy_index_labels))

            z_order_array = vtkIntArray()
            z_order_array.SetName("Layer_ID")
            z_order_array.SetNumberOfComponents(1)
            z_order_array.SetNumberOfTuples(len(z_order_labels))

            for i, (xy_idx, z_ord) in enumerate(zip(xy_index_labels, z_order_labels)):
                xy_index_array.SetValue(i, int(xy_idx))
                z_order_array.SetValue(i, int(z_ord))

            # Attach the label arrays to the unstructured grid
            labeled_corners.GetPointData().AddArray(xy_index_array)
            labeled_corners.GetPointData().AddArray(z_order_array)
            # Write the modified VTU file with labels
            if self.setting.debug:
                writer = vtkXMLUnstructuredGridWriter()
                writer.SetFileName(os.path.join(self.setting.vis_dir, "labeled_corners.vtu"))
                writer.SetInputData(labeled_corners)
                writer.Write()

        
            # == Create `distinct_corners_points_voronoi` == 
                #- use `distinct_points` as index, `voronoi` as map, search `distinct_corners_points` to recreate the correct voronoi mesh
           
            distinct_corners_points_locator = vtkPointLocator()
            distinct_corners_points_locator.SetDataSet(distinct_corners_points)
            distinct_corners_points_locator.BuildLocator()

            correct_voronoi_cell_array = vtkCellArray()
            elem_id_array = vtkIntArray()
            elem_id_array.SetName("Elem_Index")
            # go through each points in distinct_points
            for i in range(distinct_points.GetNumberOfPoints()):
                point = distinct_points.GetPoint(i)
                voronoi_cell = voronoi.GetCell(i)
                # go through each points in voronoi cell
                polygon = vtkPolygon()
                center_point_inserted = False
                center_point_id = distinct_corners_points_locator.FindClosestPoint(point)
                
                for j in range(voronoi_cell.GetNumberOfPoints()):
                    cell_point_id = voronoi_cell.GetPointId(j)
                    cell_point = voronoi.GetPoint(cell_point_id)
                    dist2 = reference(0)
                    corners_point_id = distinct_corners_points_locator.FindClosestPointWithinRadius(1, [cell_point[0],  cell_point[1], cell_point[2]], dist2)

                    if corners_point_id == -1:
                        closest_corners_point_id = distinct_corners_points_locator.FindClosestPoint(cell_point)
                        if (not center_point_inserted) and j+1 < voronoi_cell.GetNumberOfPoints():
                            next_cell_point_id = voronoi_cell.GetPointId(j+1)
                            next_cell_point = voronoi.GetPoint(next_cell_point_id)
                            dist2 = reference(0)
                            next_corners_point_id = distinct_corners_points_locator.FindClosestPointWithinRadius(1, [next_cell_point[0],  next_cell_point[1], next_cell_point[2]], dist2)
                            # next point on boundary, so insert the center point after this point
                            if next_corners_point_id == -1:
                                polygon.GetPointIds().InsertNextId(closest_corners_point_id)
                                polygon.GetPointIds().InsertNextId(center_point_id)
                            # next point is not on boundary, so insert the center point before this point
                            else:
                                polygon.GetPointIds().InsertNextId(center_point_id)
                                polygon.GetPointIds().InsertNextId(closest_corners_point_id)
                            center_point_inserted = True

                        else:
                            polygon.GetPointIds().InsertNextId(closest_corners_point_id)
                            
                    else:
                        polygon.GetPointIds().InsertNextId(corners_point_id)
                correct_voronoi_cell_array.InsertNextCell(polygon)
                elem_id_array.InsertNextValue(i)

            distinct_corners_points_voronoi = vtkPolyData()
            distinct_corners_points_voronoi.SetPoints(distinct_corners_points.GetPoints())
            distinct_corners_points_voronoi.SetPolys(correct_voronoi_cell_array)
            distinct_corners_points_voronoi.GetCellData().AddArray(elem_id_array)
            distinct_corners_points_voronoi.GetPointData().AddArray(distinct_corners_points.GetPointData().GetArray("XY_Index"))

            if self.setting.debug:
                # Write the Voronoi mesh to a VTU file for debugging
                voronoi_writer = vtkXMLPolyDataWriter()
                voronoi_writer.SetInputData(distinct_corners_points_voronoi)
                voronoi_writer.SetFileName(os.path.join(self.setting.vis_dir, 'distinct_corners_points_voronoi.vtp'))
                voronoi_writer.Write()

            # == create the geometry == 
            #- use `labeled_temp_elem` points as index (cell sequecne)
            #- from layer 0 to layer max, horizon 0 to horizon max-1
            #- use `distinct_corners_points_voronoi` as 2D polygon map to find the actual points from `labeled_corners`
            #- create each polyhedron by adding top, buttom and side surfaces

            main_geometray = vtkUnstructuredGrid()
            main_geometray.SetPoints(labeled_corners.GetPoints())

            labeled_corners_points = np.array([labeled_corners.GetPoint(i) for i in range(labeled_corners.GetNumberOfPoints())])
            labeled_corners_df = pd.DataFrame(labeled_corners_points, columns=["x", "y", "z"])
            for i in range(labeled_corners.GetPointData().GetNumberOfArrays()):
                array_name = labeled_corners.GetPointData().GetArrayName(i)
                array = labeled_corners.GetPointData().GetArray(i)
                array_values = np.array([array.GetValue(j) for j in range(array.GetNumberOfTuples())])
                labeled_corners_df[array_name] = array_values
            #labeled_corners_df.describe()

            horizon_id_array = labeled_temp_elem.GetPointData().GetArray("Horizon_ID")
            elem_id_array = labeled_temp_elem.GetPointData().GetArray("Elem_Index")

            for index in range(labeled_temp_elem.GetNumberOfPoints()):
            #for index in range(10):
                # get voronoi cell
                voronoi_cell = distinct_corners_points_voronoi.GetCell(elem_id_array.GetValue(index))
                cell_xy_index = [ voronoi_cell.GetPointId(i) for i in range(voronoi_cell.GetNumberOfPoints())]

                horizon_id = horizon_id_array.GetValue(index)
                # top face

                polyhedron_faces = [] # top, bottom, sides
                top_face = []
                for xy_index in cell_xy_index:
                    # find point in labeled_corners_df
                    matching_indexes = labeled_corners_df.index[(labeled_corners_df["Layer_ID"] == horizon_id + 1) & (labeled_corners_df["XY_Index"] == xy_index)]
                    top_face.append(matching_indexes[0])
                polyhedron_faces.append(top_face)

                bottom_face = []
                for xy_index in cell_xy_index:
                    # find point in labeled_corners_df
                    matching_indexes = labeled_corners_df.index[(labeled_corners_df["Layer_ID"] == horizon_id) & (labeled_corners_df["XY_Index"] == xy_index)]
                    bottom_face.append(matching_indexes[0])
                polyhedron_faces.append(bottom_face)

                for j in range(len(cell_xy_index)):
                    if j == len(cell_xy_index) -1:
                        side_face = [top_face[0], top_face[j], bottom_face[j], bottom_face[0]]
                    else:
                        side_face = [top_face[j+1], top_face[j], bottom_face[j], bottom_face[j+1]]
                    polyhedron_faces.append(side_face)

                # create a polyhedron
                number_of_faces = voronoi_cell.GetNumberOfPoints() + 2
                polyhedron_faces_idlist = vtkIdList()
                # Number faces that make up the cell.
                polyhedron_faces_idlist.InsertNextId(number_of_faces)
                for face in polyhedron_faces:
                    # Number of points in the face == numberOfFaceVertices
                    polyhedron_faces_idlist.InsertNextId(len(face))
                    # Insert the pointIds for that face.
                    [polyhedron_faces_idlist.InsertNextId(i) for i in face]

                main_geometray.InsertNextCell(VTK_POLYHEDRON, polyhedron_faces_idlist)
                

            main_geometray.GetCellData().AddArray(self.elemIDArray)
            main_geometray.GetCellData().AddArray(volxArray)
            main_geometray.GetCellData().AddArray(matArray)
            if self.rock_dict is not None:
                main_geometray.GetCellData().AddArray(per_array)
                main_geometray.GetCellData().AddArray(sgr_array)

            main_geometray.GetCellData().AddArray(matIDArray)
            main_geometray.GetCellData().AddArray(horizon_id_array)
            self.main_geometry = os.path.join(
                self.setting.vis_dir, "main_geometry.vtu")
            self.__write_vtk_file(main_geometray, self.main_geometry)
        
        if os.path.exists(self.main_geometry):
            print(f'    ✓ Main geometry created: {self.main_geometry}')

    def __reorder_hexahedron(self, points):
        # Step 1: Sort points by Z coordinate to separate bottom and top layers
        sorted_indices = np.argsort(points[:, 2])  # Sort indices by z-coordinate
        bottom_indices = sorted_indices[:4]  # 4 lowest Z values
        top_indices = sorted_indices[4:]  # 4 highest Z values

        # Step 2: Compute centroid of bottom plane for angle sorting
        centroid = np.mean(points[bottom_indices, :2], axis=0)  # Only x and y

        # Step 3: Compute angles from centroid and sort counterclockwise
        def angle_from_centroid(idx):
            p = points[idx]
            return np.arctan2(p[1] - centroid[1], p[0] - centroid[0])
        
        bottom_order = sorted(bottom_indices, key=angle_from_centroid)
        top_order = sorted(top_indices, key=angle_from_centroid)

        # Step 4: Assign correct VTK order
        reordered_indices = np.array(bottom_order + top_order)

        return reordered_indices

    def __checkParallel(self, elem_conne):
        dir1 = self.__get_direction_from_polyline(elem_conne.GetCell(0))
        dir2 = self.__get_direction_from_polyline(elem_conne.GetCell(1))
        if self.__are_parallel(dir1, dir2):
            return True
        return False

    def __get_direction_from_polyline(self, polyline):
        """
        Given a vtkPolyLine, compute a representative normalized direction vector.
        Here we use the vector from the first point to the last point.
        """
        points = polyline.GetPoints()
        num_points = points.GetNumberOfPoints()
        if num_points < 2:
            return None  # Not enough points to define a direction.
        
        first_pt = np.array(points.GetPoint(0))
        first_pt[2] = 0
        last_pt = np.array(points.GetPoint(num_points - 1))
        last_pt[2] = 0
        direction = last_pt - first_pt
        norm = np.linalg.norm(direction)
        if norm == 0:
            return None  # Degenerate polyline
        return direction / norm

    def __are_parallel(self, dir1, dir2, tol=1e-6):
        """
        Two vectors are parallel if their cross product is nearly zero
        (i.e., the magnitude of the cross product is less than a tolerance)
        """
        cross_prod = np.cross(dir1, dir2)
        return np.linalg.norm(cross_prod) < tol

    def __check_isReverse(self, elem_df):
        """
        Checks if the given DataFrame has a reverse sequence and determines the mesh plane.
        This method performs the following steps:
        1. Checks the real plane by analyzing the standard deviation of the 'X', 'Y', and 'Z' columns.
        2. Determines if the increasement sequence is in the order of X -> Y -> Z.
        3. If the sequence is not in the correct order, it re-indexes.
        Parameters:
        elem_df (pandas.DataFrame): The DataFrame containing the elements to be checked.
        Returns:
        bool: True if the sequence is reversed, False otherwise.
        """
        describe = elem_df.describe()

        #    1. check real plane
        mesh_plane = MeshPlane.unknown
        still_col = [1, 1, 1]
        if describe['X']['count'] == 0 or describe['X']['std'] == 0:
            still_col[0] = 0
        if describe['Y']['count'] == 0 or describe['Y']['std'] == 0:
            still_col[1] = 0
        if describe['Z']['count'] == 0 or describe['Z']['std'] == 0:
            still_col[2] = 0
        

        if still_col == [1, 1, 1]:
            mesh_plane = MeshPlane.XYZ
        elif still_col == [1, 0, 1]:
            mesh_plane = MeshPlane.XZ
        elif still_col == [1, 0, 0]:
            mesh_plane = MeshPlane.X
        elif still_col == [1, 1, 0]:
            mesh_plane = MeshPlane.XY
        elif still_col == [0, 1, 1]:
            mesh_plane = MeshPlane.YZ
        elif still_col == [0, 0, 1]:
            mesh_plane = MeshPlane.Z
        elif still_col == [0, 1, 0]:
            mesh_plane = MeshPlane.Y

        self.setting.mesh_plane = mesh_plane

        # check increase sequence
        map = ['X', 'Y', 'Z']
        head = elem_df.head()
        head_describe = head.describe()

        
        is_reverse = False
        # find increasement in each col
        for i in range(0, 3):
            if still_col[i] == 1:
                if head_describe[map[i]]['std'] == 0:
                    is_reverse = True
                    break
                else:
                    break
        
        #self.setting.isReverse = is_reverse
        return is_reverse

    def __write_vtk_file(self, file, file_path):

        extension = os.path.splitext(self.main_geometry)[1]
        writer = None
        if extension == '.vtr':
            writer = vtkXMLRectilinearGridWriter()

        elif extension == '.vts':
            writer = vtkXMLStructuredGridWriter()

        elif extension == '.vtu':
            writer = vtkXMLUnstructuredGridWriter()

        writer.SetFileName(file_path)
        writer.SetInputData(file)
        writer.SetDataModeToBinary()
        writer.Write()

    def __read_vtk_file(self, file_path):
        
        extension = os.path.splitext(self.main_geometry)[1]
        if extension == '.vtr':
            reader = vtkXMLRectilinearGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()    
        elif extension == '.vts':
            reader = vtkXMLStructuredGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()
        elif extension == '.vtu':
            reader = vtkXMLUnstructuredGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()
    
    def __parse_float(self, s):
        try:
            value = float(s)
            if np.isnan(value):
                return 0
            return value

        except ValueError:
            if '-' in s:
                segments = s.split('-')
                if len(segments) == 2:
                    return float(segments[0] + 'E-' + segments[1])
                if len(segments) == 3:
                    return float('-0' + segments[1] + 'E-' + segments[2])
            if '+' in s:
                segments = s.split('+')
                if len(segments) == 2:
                    return float(segments[0] + 'E+' + segments[1])
                if len(segments) == 3:
                    return float('0' + segments[1] + 'E+' + segments[2])
            else:
                print(f'{s} can\'t parse to float.')
                return 0
            
    def __isInt(self, s):
        try:
            value = int(s)
            if np.isnan(value):
                return False
            return True

        except ValueError:
            return False
        
    def __check_TOUGH_version(self):
        out_file_path = self.current_out_file
        extension = os.path.splitext(out_file_path)[1].lower()
        if extension == '.tec':
            self.setting.out_format_type = OutType.TEC
            self.setting.tough_version = ToughVersion.TOUGHReact
            return
            #return OutType.TEC
        elif extension == '.csv':
            self.setting.out_format_type = OutType.CSV
            line_number = 0
            with open(out_file_path, encoding="utf-8") as f:
                for line in f:
                    if line_number == 0:
                        first_col = line.split(',')[0].strip().lower()
                        if 'time' in first_col:
                            self.setting.tough_version = ToughVersion.TOUGH2                            
                            return
                    if line_number == 2:
                        values = line.strip().split(',')
                        if len(values) == 1 and 'time' in values[0].strip().lower():
                            self.setting.tough_version = ToughVersion.TOUGH3
                            return
                        print(f'The format of your output file, {out_file_path}, is not correct. Please double-check your file.')
                        sys.exit(1)
                    line_number = line_number + 1
        
        else:
            print(f'The format of your output file, {out_file_path}, is not supported.\nPlease use either .csv or .tec file format instead.')
            sys.exit(1)

    def __check_if_block_end(self, line, line_number):

        if 'ENDCY' in line:
            return True
        
        if len(line) < 10 and line_number == 1:
            return False
        
        if len(line) < 10:
            return True        
        if line.startswith('\n') or line.startswith(' \n'):
            return True
        if line.startswith('\r') or line.startswith(' \r'):
            return True

        trimmed = line.lstrip()
        if len(trimmed)>6 and trimmed[5] == "-" and trimmed[6] == "-":
            return True
        return False

    def __write_json(self):
        # Convert each object to a dict
        # Assume variable_list is a list of visVariable objects
        variable_list_dicts = []
        for key in self.variable_list:
            for variable in self.variable_list[key]:
                 variable_list_dicts.append(variable.to_dict())


        # Write to JSON file
        path = os.path.join(self.setting.vis_dir, "variable_list.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(variable_list_dicts, f, indent=2)

        timestep_list_dicts = [timestep.__dict__ for timestep in self.time_steps_list]
        

        # Write to JSON file
        path = os.path.join(self.setting.vis_dir, "timestep_list.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(timestep_list_dicts, f, indent=2)

    def __fix_negative_zero(self, x):
        return 0.0 if x == 0 else x
    
class vis_charting:
    def __init__(self, case_dir):
        self.vis_dir = None
        self.variable_list = None
        vis_dir = os.path.join(case_dir, "tough_vis", "paraview")
        

        if os.path.isdir(vis_dir):
            print("vis_dir:", vis_dir)
        else:
            print(f'Case vis_dir({vis_dir}) not found.')
            sys.exit(0)

        variable_list_path = os.path.join(case_dir, "tough_vis", "variable_list.json")
        if os.path.isfile(variable_list_path):
            with open(variable_list_path, "r", encoding="utf-8") as f:
                self.variable_list = json.load(f)
        else:
            print(f'Case variable_list.json({variable_list_path}) not found.')
            sys.exit(0)

        timestep_list_path = os.path.join(case_dir, "tough_vis", "timestep_list.json")
        if os.path.isfile(timestep_list_path):
            with open(timestep_list_path, "r", encoding="utf-8") as f:
                self.time_steps_list = json.load(f)
        else:
            print(f'Case timestep_list.json({timestep_list_path}) not found.')
            sys.exit(0)
        
        self.vis_dir = vis_dir
        


    def return_dataframe(self, element_id_list = None, scalar_variable_list = None, time_step_id_list = None, vector_variable_list = []):
        if self.vis_dir is None:
            print("vis_dir not set.")
            sys.exit(0)
        if self.variable_list is None:
            print("variable_list not set.")
            sys.exit(0)
        if self.time_steps_list is None:
            print("time_steps_list not set.")
            sys.exit(0)
        
        # 1. find timesteps
        query_time_step_list = []
        if time_step_id_list == None:
            query_time_step_list = self.time_steps_list
        else:
            for time_step in self.time_steps_list:
                if time_step["time_step"] in time_step_id_list:
                    query_time_step_list.append(time_step)
        
        # 2. find scalar variables
        query_variables = []
        if scalar_variable_list == None:
            query_variables = self.variable_list
        else:
            for variable in self.variable_list:
                if variable["variable_name"] in scalar_variable_list:
                    if variable["value_type"] == "Scalar":
                        query_variables.append(variable)

        # 3. find vector variables

        for variable in self.variable_list:
            if variable["variable_name"] in vector_variable_list:
                if variable["value_type"] == "Vector":
                    query_variables.append(variable)
        
        
        # create dataframe that contains all variables and timesteps
        df = pd.DataFrame()
        rows = []
        for time_step in query_time_step_list:
            time_step_id = time_step["time_step"]
            time = time_step["time"]
            vtk = self.__read_vtk_file(time_step["vtu_file_name"])
            #print(f"Reading  time: {time_step['time']}")

            for i in (range(vtk.GetNumberOfCells()) if element_id_list is None else element_id_list):
                if i >= vtk.GetNumberOfCells():
                    print(f"Element ID {i} is out of range for the current VTK file.")
                    sys.exit(1)

                new_row = {"element_id": i, "time_step_id": time_step_id, "time": time}
                for variable in query_variables:
                    variable_name = variable["variable_name"]
                    vtk_array = vtk.GetCellData().GetArray(variable_name)
                    if vtk_array is None:
                        print(f"Variable '{variable_name}' not found in the VTK file.")
                        continue
                    if variable["value_type"] == "Scalar":
                        new_row[variable_name] = vtk_array.GetValue(i)
                    elif variable["value_type"] == "Vector":
                        new_row[variable_name + "_x"] = vtk_array.GetComponent(i, 0)
                        new_row[variable_name + "_y"] = vtk_array.GetComponent(i, 1)
                        new_row[variable_name + "_z"] = vtk_array.GetComponent(i, 2)

                #df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                rows.append(new_row)
        
        df = pd.DataFrame(rows)
        return df
            
            


            
    def __read_vtk_file(self, file_path):
        
        extension = os.path.splitext(file_path)[1]
        if extension == '.vtr':
            reader = vtkXMLRectilinearGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()    
        elif extension == '.vts':
            reader = vtkXMLStructuredGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()
        elif extension == '.vtu':
            reader = vtkXMLUnstructuredGridReader()
            reader.SetFileName(file_path)
            reader.Update()
            return reader.GetOutput()
        

    