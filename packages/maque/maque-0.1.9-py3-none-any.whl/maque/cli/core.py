import time
import subprocess
import io
import csv
import collections


def run_job(job, num: int, interval="second"):
    import schedule

    if interval == "second":
        schedule.every(num).seconds.do(job)
    elif interval == "minute":
        schedule.every(num).minutes.do(job)
    elif interval == "hour":
        schedule.every(num).hours.do(job)
    elif interval == "day":
        schedule.every(num).days.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


def commandexists(shellcommand):
    status, output = subprocess.getstatusoutput(shellcommand)
    exists = status == 0
    if not exists:
        print("Could not execute: {0}".format(shellcommand))
    return exists

def command(args):
    # subprocess.call(args)
    # subprocess.getoutput(cmd)
    return subprocess.check_output(args).decode()
