import paho.mqtt.client as mqtt
import sys
import subprocess
import logging
from datetime import datetime
import logging.config
from bfc import ByteFormatter
from nc_translator import NCTranslator
from segment_time_series import ProcessTimestampExtractor
import os
import json
import console_ctrl

BROKER = "10.10.160.10"
PORT = 1883
DAQX_PROGRAM_NAME = "daq_ni.py"
SPIKE_PROGRAM_NAME = "daq_spike.py"
BFC_DATA_FILE_NAME = "bfc_data.json"
ABSOLUTE_PATH = r"D:\interq_kompaki_milling_data"
#use for KompAKI Evaluation
#ABSOLUTE_PATH = 'C:\\Users\\N.Jourdan_lokal\\Desktop\\pp3-demonstrator\\Production'
DURATION_PART_1 = "199"
FILE_NAME_PART_1 = "part1.h5"
DURATION_PART_2 = "113"
FILE_NAME_PART_2 = "part2.h5"
TOPIC = "bfc/hbep03t2pd/iotclient/dataset/Default"


class Publisher:
    def __init__(self):
        self.__user = "admin"
        self.__password = "admin"
        self.client = mqtt.Client()

    def __call__(self, message):
        def on_publish(client, userdata, result):
            print("Data sent to Broker")

        self.client.on_publish = on_publish
        self.client.username_pw_set(username=self.__user, password=self.__password)
        self.client.connect(BROKER, PORT)
        self.client.publish(TOPIC, message)


class Subscriber:
    def __init__(self):
        self.__user = "admin"
        self.__password = "admin"
        self.client = mqtt.Client()
        self.nc_translator = NCTranslator()
        self.bfc_data_list = []
        self.current_folder_name = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        self.spike_proc = None
        self.ni_proc_part_1 = None
        self.ni_proc_part_2 = None
        self.program_active = False
        logging.config.fileConfig("logging.conf")
        self.logger = logging.getLogger()

    def __write_to_json(self, json_path, bfc_data_list):
        with open(json_path, "a", encoding="utf-8") as jsonfile:
            jsonfile.write(json.dumps(bfc_data_list, ensure_ascii=False, indent=4))

    def __call__(self):
        def on_connect(client, userdata, flags, rc):
            """
			Call back for connect event. Error messages retrieved from:
			https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php 
			"""
            if rc == 0:
                self.logger.info(
                    "Established new connection to broker {0}".format(BROKER)
                )
                self.client.subscribe(TOPIC)
                self.logger.info("Listening to topic {0}".format(TOPIC))
            else:
                self.logger.warning(
                    "Connection refused - see error code for rc: {0}".format(rc)
                )
                self.logger.info("Exiting script now")
                sys.exit()

        def on_disconnect(client, userdata, rc):
            self.logger.info("Disconnected - see error code for rc: {0}".format(rc))

        def on_message(client, userdata, msg):
            byte_formatter = ByteFormatter(msg.payload)
            bfc_data = byte_formatter._format_byte_to_dict()
            ncline = byte_formatter._extract_nc_line(bfc_data)
            program_state = self.nc_translator(ncline)

            if program_state is None and not self.program_active:
                return
            try:
                ni_poll_part_1 = self.ni_proc_part_1.poll()
            except:
                ni_poll_part_1 = 1

            if program_state is not None:
                if program_state["trigger"] == "program_start" and ni_poll_part_1 != None:
                    self.logger.info("Triggering start of NI DAQ for the first part")
                    self.program_active = True
                    self.current_folder_name = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
                    try:
                        os.mkdir(os.path.join(ABSOLUTE_PATH, self.current_folder_name))
                    except:
                        self.logger.info("Creating folder for data storage has failed")

                    self.ni_proc_part_1 = subprocess.Popen(
                        [
                            "python",
                            DAQX_PROGRAM_NAME,
                            "--duration",
                            DURATION_PART_1,
                            "--file_name",
                            FILE_NAME_PART_1,
                            "--path",
                            os.path.join(ABSOLUTE_PATH, self.current_folder_name),
                        ]
                    )

                try:
                    ni_poll_part_2 = self.ni_proc_part_2.poll()
                except:
                    ni_poll_part_2 = 1

                if (
                    program_state["process"] == "planfraesen"
                    and program_state["part"] == "bauteil_2"
                    and ni_poll_part_2 != None
                ):
                    self.logger.info("Triggering start of NI DAQ for the second part")
                    self.ni_proc_part_2 = subprocess.Popen(
                        [
                            "python",
                            DAQX_PROGRAM_NAME,
                            "--duration",
                            DURATION_PART_2,
                            "--file_name",
                            FILE_NAME_PART_2,
                            "--path",
                            os.path.join(ABSOLUTE_PATH, self.current_folder_name),
                        ]
                    )

                if (
                    program_state["trigger"] == "program_start"
                    or program_state["trigger"] == "spike_start"
                ):
                    self.logger.info("Triggering start of spike DAQ")
                    self.spike_proc = subprocess.Popen(
                        [
                            "python",
                            SPIKE_PROGRAM_NAME,
                            "--spike",
                            program_state["tool"],
                            "--section",
                            program_state["part"] + "_" + program_state["process"],
                            "--path",
                            os.path.join(ABSOLUTE_PATH, self.current_folder_name),
                        ],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )

                elif program_state["trigger"] == "spike_stop":
                    self.logger.info("Triggering termination of Spike DAQ")
                    try:
                        console_ctrl.send_ctrl_c(self.spike_proc.pid)
                    except:
                        self.logger.info("spike DAQ termination has failed")

                    self.spike_proc = None

            if self.program_active:
                if (
                    program_state is not None
                    and program_state["part"] == "bauteil_2"
                    and program_state["process"] == "planfraesen"
                    and program_state["trigger"] == "spike_start"
                ):
                    json_path = os.path.join(
                        ABSOLUTE_PATH,
                        self.current_folder_name,
                        "part_1_" + BFC_DATA_FILE_NAME,
                    )
                    self.__write_to_json(json_path, self.bfc_data_list)
                    process_timestamp_extractor_part_1 = ProcessTimestampExtractor(
                        json_path,
                        ABSOLUTE_PATH,
                        self.current_folder_name,
                        "part_1"
                    )
                    process_timestamp_extractor_part_1()
                    self.bfc_data_list = []
                    
                nc_inferred_information = {"nc_inferred_information": program_state}
                bfc_data.update(nc_inferred_information)
                self.bfc_data_list.append(bfc_data)

                if program_state is not None and program_state["trigger"] == "program_end":
                    self.program_active = False
                    json_path = os.path.join(
                        ABSOLUTE_PATH,
                        self.current_folder_name,
                        "part_2_" + BFC_DATA_FILE_NAME,
                    )
                    self.__write_to_json(json_path, self.bfc_data_list)
                    process_timestamp_extractor_part_2 = ProcessTimestampExtractor(
                        json_path,
                        ABSOLUTE_PATH,
                        self.current_folder_name,
                        "part_2"
                    )
                    process_timestamp_extractor_part_2()
                    self.bfc_data_list = []

        self.client.username_pw_set(username=self.__user, password=self.__password)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.connect(BROKER, PORT, keepalive=60)
        self.client.on_message = on_message
        self.client.loop_forever()

