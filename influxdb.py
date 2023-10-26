import influxdb_client
import numpy as np
import h5py
from datetime import datetime
from influxdb_client.client.exceptions import InfluxDBError
import logging
import logging.config
import rx
from rx import operators as ops


class InfluxBase:
    def __init__(self, url: str, token: str, organization: str):
        self.url = url
        self.token = token
        self.organization = organization

    def _instantiate_client(self):
        client = influxdb_client.InfluxDBClient(
            url=self.url, token=self.token, org=self.organization
        )
        return client


class InfluxQueryManager(InfluxBase):
    def __init__(
        self,
        bucket: str = "interq_kompaki_test",
        organization: str = "PTW TU Darmstadt",
        # token:str ="WhVEu8wlR8pM36OK_NAlzVjRCmDjQ1qeigixFO_Mr4ChgTAHSM9wry3ubVMHRSTmyXqdVFGxVj4ClotuBTNdYw==",
        token: str = "pKTY7F2iuH-bBpuK00l9UuSiWvDfFJey4Vgj8qe-P0g8thvNbz7kH7Gd3ax0QUm77LXHvQZPFFiJG6VQkKc2pg==",
        url: str = "10.10.160.10:8086",
        measurement_name: str = "DMC_sensors",
        field_keys: list = ["Mod1/ai0", "Mod1/ai1", "Mod1/ai2", "Mod1/ai3"],
    ):

        self.measurement_name = measurement_name
        self.bucket = bucket
        self.organization = organization
        self.token = token
        self.url = url
        self.field_keys = field_keys
        super().__init__(url, token, organization)

    def __call__(self, start: datetime, stop: datetime):
        client = self._instantiate_client()
        query_api = client.query_api()
        query_generator = InfluxQueryGenerator(self.bucket, self.measurement_name)
        query = query_generator(start, stop)
        records = query_api.query_stream(query=query)
        return records


class InfluxQueryGenerator:
    def __init__(self, bucket, measurement_name):
        self.bucket = bucket
        self.measurement_name = measurement_name

    def _format_query(self, start="-5m", stop="now()"):

        query = (
            'from(bucket:"DMC")'
            "|> range(start: {0}, stop: {1})"
            '|> filter(fn: (r) => r._measurement == "DMC_sensors")'
            '|> filter(fn: (r) => r._field == "Mod1/ai0" \
				or r._field == "Mod1/ai1"\
				or r._field == "Mod1/ai2"\
				or r._field == "Mod1/ai3")'
            '|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'.format(
                start, stop
            )
        )

        return query

    def __call__(self, start, stop):
        query = self._format_query(start, stop)
        return query


class Influxh5FileWriter(InfluxBase):
    def __init__(
        self,
        bucket: str = "interq_kompaki_test",
        organization: str = "PTW TU Darmstadt",
        # token:str ='WhVEu8wlR8pM36OK_NAlzVjRCmDjQ1qeigixFO_Mr4ChgTAHSM9wry3ubVMHRSTmyXqdVFGxVj4ClotuBTNdYw==',
        token: str = "pKTY7F2iuH-bBpuK00l9UuSiWvDfFJey4Vgj8qe-P0g8thvNbz7kH7Gd3ax0QUm77LXHvQZPFFiJG6VQkKc2pg==",
        url: str = "10.10.160.10:8086",
        measurement_name: str = "DMC_sensors",
        field_keys: list = ["Mod1/ai0", "Mod1/ai1", "Mod1/ai2", "Mod1/ai3"],
    ):

        self.measurement_name = measurement_name
        self.bucket = bucket
        self.organization = organization
        self.token = token
        self.url = url
        self.field_keys = field_keys
        self.batch_size = 50000  # this doesnt work for the Spike DAQ!
        self.flush_interval = 10000
        self.callback = BatchingCallback()
        super().__init__(url=self.url, token=self.token, organization=self.organization)

    def _build_line_protocol(self, data):
        dataset_timestamps = data[0].astype(np.int64)
        dataset_values = data[1:]
        line_protocol_formatter = LineProtocolFormatter(
            measurement_name=self.measurement_name, field_keys=self.field_keys
        )
        dataset = line_protocol_formatter(dataset_values, dataset_timestamps)
        return dataset

    def _retrieve_dataset_from_h5_file(self, data: str):
        with h5py.File(data, "r") as hf:
            n_datasets = len(hf.keys())
            for i in range(n_datasets):
                dataset = hf[str(i)][:]
        return dataset

    def __call__(self, data: str):

        batch = rx.from_iterable(self._retrieve_dataset_from_h5_file(data)).pipe(
            ops.map(lambda data: self._build_line_protocol(data))
        )

        # for writing Spike data to influx, we need to infer batch size (and flush_interval?) from the h5 data!
        # self.batch_size = dataset.shape[0]
        # self.flush_interval = ???

        client = self._instantiate_client()
        with client.write_api(
            write_options=influxdb_client.WriteOptions(
                batch_size=self.batch_size, flush_interval=self.flush_interval
            ),
            success_callback=self.callback.success,
            retry_callback=self.callback.retry,
            error_callback=self.callback.error,
        ) as write_api:

            write_api.write(bucket=self.bucket, record=batch, write_precision="us")


class LineProtocolFormatter:
    def __init__(self, measurement_name: str, field_keys: list):

        self.measurement_name = measurement_name
        self.field_keys = field_keys

    def _format_to_line_protocol(self, field_values, unix_timestamp):

        line_protocol = str(self.measurement_name) + " "
        for i in range(len(self.field_keys)):
            line_protocol += str(self.field_keys[i]) + "=" + str(field_values[i])
            if i < len(self.field_keys) - 1:
                line_protocol += ","
            else:
                line_protocol += " " + str(unix_timestamp)
        return line_protocol

    def __call__(self, field_values, unix_timestamp):
        line_protocols = self._format_to_line_protocol(field_values, unix_timestamp)
        return line_protocols


class BatchingCallback:
    def __init__(self):
        logging.config.fileConfig("logging.conf")
        self.logger = logging.getLogger()

    def success(self, conf: tuple([str, str, str,]), data: str):
        self.logger.info("Received callback from influxdb: BATCH WRITTEN SUCCESSFULLY")
        self.logger.info("Written batch {0}".format(conf))

    def error(self, conf: tuple([str, str, str]), data: str, exception: InfluxDBError):
        self.logger.info("Received callback from influxdb: ERROR WHILE WRITING BATCH")
        self.logger.info("Cannot write batch {0} - {1}".format(conf, exception))

    def retry(self, conf: tuple([str, str, str]), data: str, exception: InfluxDBError):
        self.logger.info("Received callback: RETRY TO WRITE BATCH")
        self.logger.info(
            "Retry error occurs for batch {0} - {1}".format(conf, exception)
        )

