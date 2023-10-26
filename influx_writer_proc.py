import argparse
import logging
from influxdb import Influxh5FileWriter

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=str)
parser.add_argument("--filename", type=str)
args = parser.parse_args()

logging.config.fileConfig("logging.conf")
logger = logging.getLogger()

SOURCE = args.source
FILENAME = args.filename


field_keys_table = {
    "ni": ["Mod1/ai0", "Mod1/ai1", "Mod1/ai2", "Mod1/ai3"],
    "spike": ["Bending Moment", "x", "y", "ax", "tors"],
}
buckets_table = {"spike": "interq_kompaki_prod", "ni": "interq_kompaki_prod"}

measurement_names_table = {"spike": "spike_sensors", "ni": "DMC_sensors"}

field_keys = None
bucket = None
measurement_name = None

if SOURCE not in field_keys_table:
    logger.log.info(
        "influx writer proc has been given an invalid measurement source argument"
    )
    exit(-1)
else:
    field_keys = field_keys_table[SOURCE]
    bucket = buckets_table[SOURCE]
    measurement_name = measurement_names_table[SOURCE]

influx_h5_file_writer = Influxh5FileWriter(bucket, measurement_name, field_keys)

influx_h5_file_writer(FILENAME)
logger.info(
    "File "
    + FILENAME
    + " has been written to InfluxDB to measurement "
    + measurement_name
    + " in Bucket "
    + bucket
)
exit(1)
