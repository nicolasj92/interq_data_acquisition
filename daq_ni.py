import nidaqmx
import numpy as np
import time
import logging
import logging.config
from influxdb import Influxh5FileWriter
from datetime import datetime
import mqtt
import os
import h5py
import argparse
import subprocess

SAMPLING_RATE = 2500
DEVICE_AND_CHANNEL_IDENTIFIER = "Mod1/ai0:3"
EXCITATION_VALUE = 0.002
NANOSECONDS_PER_SAMPLE = int(1e9 / SAMPLING_RATE)


class DAQ:
    def __init__(self, processing_time_in_seconds, file_name, path):
        self.processing_time_in_seconds = processing_time_in_seconds
        self.file_name = file_name
        self.path = path
        self.samples_per_channel = SAMPLING_RATE * self.processing_time_in_seconds
        self.current_time = None
        logging.config.fileConfig("logging.conf")
        self.logger = logging.getLogger()

    def __get_timestamps(self, n_samples):
        timestamps = np.arange(
            self.current_time,
            self.current_time + (NANOSECONDS_PER_SAMPLE * n_samples),
            NANOSECONDS_PER_SAMPLE,
        )
        timestamps = timestamps[:, np.newaxis]
        timestamps = (timestamps / 1e3).astype(np.int64)
        return timestamps

    def __write_data_to_h5_file(self, timestamps, data):
        self.logger.info("Write data to file {0}".format(self.file_name))
        data = np.hstack([timestamps, data])
        with h5py.File(os.path.join(self.path, self.file_name), "a") as hf:
            hf.create_dataset(str(0), data=data)
            hf.close()

    def __call__(self):
        self.logger.info(
            "sampling_rate {0}, samples_per_channel {1}\
			device_and_channel_identifier {2}".format(
                SAMPLING_RATE, self.samples_per_channel, DEVICE_AND_CHANNEL_IDENTIFIER
            )
        )

        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(DEVICE_AND_CHANNEL_IDENTIFIER)
        task.timing.cfg_samp_clk_timing(
            rate=SAMPLING_RATE,
            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
            samps_per_chan=self.samples_per_channel,
        )

        task.ai_channels.all.ai_coupling = nidaqmx.constants.Coupling.AC
        task.ai_channels.all.ai_excit_src = nidaqmx.constants.ExcitationSource.INTERNAL
        task.ai_channels.all.ai_excit_voltage_or_current = (
            nidaqmx.constants.ExcitationVoltageOrCurrent.USE_CURRENT
        )
        task.ai_channels.all.ai_excit_val = EXCITATION_VALUE

        task.start()
        self.current_time = time.time_ns()
        self.logger.info("Start recording")
        data = task.read(
            number_of_samples_per_channel=self.samples_per_channel,
            timeout=nidaqmx.constants.WAIT_INFINITELY,
        )
        self.logger.info(
            "Finished recording - total duration {0} s".format(
                (time.time_ns() - self.current_time) * 1e-9
            )
        )
        data = np.array(data)
        n_samples = data.shape[1]
        data = data.T
        self.logger.info("Received {0} samples".format(n_samples))
        timestamps = self.__get_timestamps(n_samples)
        self.__write_data_to_h5_file(timestamps, data)
        task.close()

        """subprocess.Popen([
			'python',
			'influx_writer_proc.py',
			'--source', 
			"ni",
			'--filename',
			self.file_name])"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=str)
    parser.add_argument("--file_name", type=str)
    parser.add_argument("--path", type=str)
    args = parser.parse_args()
    duration = args.duration
    file_name = args.file_name
    path = args.path

    daq = DAQ(processing_time_in_seconds=int(duration), file_name=file_name, path=path)
    daq()
