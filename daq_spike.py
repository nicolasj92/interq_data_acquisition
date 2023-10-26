import asyncio
from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
import time
import signal
import json
import logging
import logging.config
import argparse
import os
import numpy as np
import h5py

parser = argparse.ArgumentParser()
parser.add_argument("--spike", type=str)
parser.add_argument("--section", type=str)
parser.add_argument("--path", type=str)
args = parser.parse_args()

SPIKES = {"SPIKE_D50": "0xA444", "SPIKE_D10": "0xA400", "SPIKE_D6": "0xA42A"}

EQUIPPED_SPIKE = SPIKES[args.spike]
SECTION = args.section
PATH = args.path

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("spike_daq")


async def main():
    transport = WebsocketsTransport(url="ws://localhost:8021/graphql")
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:

        def mount_spike_mutation(spikeId="0xA400"):
            return gql(
                'mutation mount1 {mountSensor(number:"'
                + spikeId
                + '"){success message}}'
            )

        def unmount_spike_mutation():
            return gql(
                'mutation unmount {unmountSpindle(spindleNumber:"workstation_1"){success message}}'
            )

        async def subscribe_spike_data(session, freq="f25hz"):
            result_data = {}
            try:
                subscription = gql(
                    "subscription data {\
                        onSpindleUpdate(updateInterval: "
                    + freq
                    + ', spindleNumber: "workstation_1") {\
                            primarySensor {\
                                number\
                                sensorType\
                                currentSensorValue{signalType value }\
                                currentRawData{\
                                    values\
                                    signalType\
                                    unit\
                                }\
                            }\
                        }\
                    }'
                )
                async for result in session.subscribe(subscription):
                    # print("receiving spike data")
                    for i in range(
                        len(
                            result["onSpindleUpdate"]["primarySensor"]["currentRawData"]
                        )
                    ):
                        signalType = result["onSpindleUpdate"]["primarySensor"][
                            "currentRawData"
                        ][i]["signalType"]
                        values = np.array(
                            result["onSpindleUpdate"]["primarySensor"][
                                "currentRawData"
                            ][i]["values"]
                        )
                        unit = result["onSpindleUpdate"]["primarySensor"][
                            "currentRawData"
                        ][i]["unit"]
                        if len(values) > 0:
                            if signalType in result_data.keys():
                                result_data[signalType]["values"] = np.append(
                                    result_data[signalType]["values"], values, axis=0
                                )
                            else:
                                result_data[signalType] = {
                                    "values": values,
                                    "unit": unit,
                                }

            finally:
                if len(result_data) == 0:
                    print("Exiting without new data")
                    logger.info(
                        "spike subscription got cancelled without receiving samples, returning..."
                    )
                else:
                    with h5py.File(
                        os.path.join(PATH, SECTION + "spikedata.h5"), "a"
                    ) as hf:
                        for signalType in result_data.keys():
                            hf.create_dataset(
                                signalType,
                                data=result_data[signalType]["values"].astype(
                                    np.float32
                                ),
                            )
                        hf.close()
                        logger.info(
                            "spike daq subscription task got cancelled, returning..."
                        )
                    print(
                        "Spike file saved to ",
                        os.path.join(PATH, SECTION + "spikedata.h5"),
                    )
                return len(result_data)

        # Safety: Unmount potential spikes
        result = await session.execute(unmount_spike_mutation())
        logger.info(result)
        # Mount spike
        result = await session.execute(mount_spike_mutation(EQUIPPED_SPIKE))
        logger.info(result)

        subscription_task = asyncio.create_task(subscribe_spike_data(session))

        def handler(signum, frame):
            print("got ctrlc")
            subscription_task.cancel()

        signal.signal(signal.SIGINT, handler)

        result_data = await subscription_task
        logger.info("spike daq received " + str(result_data))

        result = await session.execute(unmount_spike_mutation())
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
