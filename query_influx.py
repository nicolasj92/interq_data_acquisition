import influxdb as inf


query_manager = inf.InfluxQueryManager()
records = query_manager(start = "-25m", stop = "now()")

for record in records:
    print(
        #timestamps are converted to UTC time
        record["_time"],
        record["Mod1/ai0"],
        record["Mod1/ai1"],
        record["Mod1/ai2"],
        record["Mod1/ai3"])


