import json
import os
import time
import datetime
import numpy as np
import h5py
import matplotlib.pyplot as plt


class SegmentedTimeSeriesVisualizer:
    PART_1_JSON_FILENAME = "\part_1_timestamp_process_pairs.json"
    PART_2_JSON_FILENAME = "\part_2_timestamp_process_pairs.json"
    PART_1_H5_FILENAME = "\part1.h5"
    PART_2_H5_FILENAME = "\part2.h5"

    def __init__(self, path_to_folder: str, part: str = "part_1"):
        self.part = part
        self.path = path_to_folder
        self.unix_timestamps = []

    def __load_json_data(self):
        if self.part == "part_1":
            json_path = self.path + self.PART_1_JSON_FILENAME
        else:
            json_path = self.path + self.PART_2_JSON_FILENAME
        json_file = open(json_path)
        json_data = json.load(json_file)
        json_file.close()
        return json_data
    
    def __load_h5_data(self):
        if self.part == "part_1":
            h5_path = self.path + self.PART_1_H5_FILENAME
        else:
            h5_path = self.path + self.PART_2_H5_FILENAME
        hf = h5py.File(h5_path, 'r')
        return hf

    def create_plot(self, h5_data, json_data):
        fig, axs = plt.subplots(4,1, figsize = (10,20))
        timestamps_from_json = np.array(
            list(
                json_data.keys()
            )).astype(np.float64)*10**6
        timestamps_from_h5 = h5_data['0'][:,0]

        axs[0].plot(timestamps_from_h5,h5_data['0'][:,1])
        axs[0].set_title('Mod1/ai0')
        axs[0].vlines(
            timestamps_from_json, 
            ymin = np.min(h5_data['0'][:,1]), 
            ymax = np.max(h5_data['0'][:,1]), 
            color = 'r')

        axs[1].plot(timestamps_from_h5, h5_data['0'][:,2])
        axs[1].set_title('Mod1/ai1')
        axs[1].vlines(
            timestamps_from_json, 
            ymin = np.min(h5_data['0'][:,2]), 
            ymax = np.max(h5_data['0'][:,2]), 
            color = 'r')

        axs[2].plot(timestamps_from_h5, h5_data['0'][:,3])
        axs[2].set_title('Mod1/ai2')
        axs[2].vlines(
            timestamps_from_json, 
            ymin = np.min(h5_data['0'][:,3]), 
            ymax = np.max(h5_data['0'][:,3]), 
            color = 'r')

        axs[3].plot(timestamps_from_h5, h5_data['0'][:,4])
        axs[3].set_title('Mod1/ai3')
        axs[3].vlines(
            timestamps_from_json, 
            ymin = np.min(h5_data['0'][:,4]), 
            ymax = np.max(h5_data['0'][:,4]), 
            color = 'r')
        plt.show()

    def __call__(self):
        json_data = self.__load_json_data()
        h5_data = self.__load_h5_data()
        self.create_plot(h5_data, json_data)
        


class ProcessTimestampExtractor:
    def __init__(self, json_file_path, absolute_path, current_folder_name, part):
        self.json_file_path = json_file_path
        self.json_file = open(self.json_file_path)
        self.json_data = json.load(self.json_file)
        self.absolute_path = absolute_path
        self.current_folder_name = current_folder_name
        self.part = part
        self.timestamp_process_pairs = {}

    def __convert_to_unix_timestamp_from_string_timestamp(self,timestamp, include_milliseconds = True):
        if include_milliseconds:
            unix_timestamp = time.mktime(
                    datetime.datetime.strptime(
                        timestamp, "%Y-%m-%dT%H:%M:%S.%f").timetuple())
        else: 
            unix_timestamp = time.mktime(
                    datetime.datetime.strptime(
                        timestamp, "%Y-%m-%dT%H:%M:%S").timetuple())
        return unix_timestamp
            
    def __extract_timestamp_process_pairs(self):
        for entry in range(len(self.json_data)):
            if self.json_data[entry]["nc_inferred_information"] is not None:
                json_dict = self.json_data[entry]
                if (
                    "start" in json_dict["nc_inferred_information"]["trigger"]
                    or "section" in json_dict["nc_inferred_information"]["trigger"]
                    or "program_end" in json_dict["nc_inferred_information"]["trigger"]
                ):
                    process = json_dict["nc_inferred_information"]["process"]
                    timestamp = json_dict["set"]["timestamp"]
                    print(timestamp)
                    try:
                        unix_timestamp = self.__convert_to_unix_timestamp_from_string_timestamp(
                            timestamp,
                            include_milliseconds = True)
                    except ValueError:
                        unix_timestamp = self.__convert_to_unix_timestamp_from_string_timestamp(
                            timestamp, 
                            include_milliseconds = False)
                    self.timestamp_process_pairs[unix_timestamp] = process

    def __write_to_json(self):
        path = os.path.join(
            self.absolute_path,
            self.current_folder_name,
            self.part + "_timestamp_process_pairs.json",
        )
        with open(path, "a", encoding="utf-8") as jsonfile:
            jsonfile.write(
                json.dumps(self.timestamp_process_pairs, ensure_ascii=False, indent=4)
            )

    def __call__(self):
        self.__extract_timestamp_process_pairs()
        self.__write_to_json()
        self.json_file.close()


if __name__ == "__main__":

    test_process_timestamp_extractor = 0
    test_timeseries_visualizer = 1

    if test_process_timestamp_extractor:
        JSON_FILE_PATH_PART_1 = r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator\10_26_2022_18_01_07\part_1_bfc_data.json"
        JSON_FILE_PATH_PART_2 = r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator\10_26_2022_18_01_07\part_2_bfc_data.json"
        ABSOLUTE_PATH = r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator"
        CURRENT_FOLDER_NAME = "10_26_2022_18_01_07"
        PART_1 = "part_1"
        PART_2 = "part_2"

        extractor_part_1 = ProcessTimestampExtractor(
            JSON_FILE_PATH_PART_1, ABSOLUTE_PATH, CURRENT_FOLDER_NAME, PART_1
        )
        extractor_part_1()

        extractor_part_2 = ProcessTimestampExtractor(
            JSON_FILE_PATH_PART_2, ABSOLUTE_PATH, CURRENT_FOLDER_NAME, PART_2
        )
        extractor_part_2()

    if test_timeseries_visualizer:
        PATH_TO_FOLDER = (
            r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator\10_26_2022_18_01_07"
        )
        #WORKS HOWEVER TIMESTAMPS OF BFC GATEWAY AND NI DATA ARE WAY OFF
        visualizer = SegmentedTimeSeriesVisualizer(path_to_folder=PATH_TO_FOLDER, part="part_1")
        visualizer()

