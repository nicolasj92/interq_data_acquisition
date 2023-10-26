import signal
import subprocess
import time
import console_ctrl

spike_proc = subprocess.Popen(
    [
        "python",
        "daq_spike.py",
        "--spike",
        "SPIKE_D50",
        "--section",
        "test",
        "--path",
        r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator\test",
    ],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

time.sleep(5)

print("sending CTRL C to proc 1")
console_ctrl.send_ctrl_c(spike_proc.pid)

time.sleep(5)

print("starting proc 2")

spike_proc = subprocess.Popen(
    [
        "python",
        "daq_spike.py",
        "--spike",
        "SPIKE_D50",
        "--section",
        "test",
        "--path",
        r"C:\Users\N.Jourdan_lokal\DAQ\cip_demonstrator\10_05_2022_17_55_53",
    ],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

time.sleep(5)

print("sending CTRL C to proc 2")
console_ctrl.send_ctrl_c(spike_proc.pid)

print("end")
