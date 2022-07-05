import threading
from datetime import datetime
import geopy.distance as gd
from main import out_traffic
from main import field_experiment
from gps.gps import GPSReceiver

import simpleaudio as sa
import os


gtim = 96  # green time (with 120 sec cycle)
tcyc = 120  # cycle length is 120 sec
tdwl = 30  # bus dwelling time
dbus = 20  # distance between bus station and the signal

lane_change_sound = sa.WaveObject.from_wave_file(os.path.join(os.path.dirname(__file__), r'LCAudio.wav'))

last_speed = 0
last_lat = 0
last_lon = 0

gps = None

if field_experiment:
    gps = GPSReceiver()
    gps.connect()


def lane_change_algo(b_dist):
    gps_dict = gps.get_data_frame()
    print(gps_dict)
    if gps_dict is not None:
        lane_change_algo_lat_lon(b_dist, gps_dict['speed'], gps_dict['lat'], gps_dict['lon'])

def get_last_speed():
    global last_speed
    print(last_speed)
    return last_speed

def get_last_lat():
    global last_lat
    return last_lat

def get_last_lon():
    global last_lon
    return last_lon


def lane_change_algo_lat_lon(b_dist, speed, lat, lon):
    global last_speed
    global last_lat
    global last_lon

    coor1 = (lat, lon)
    coor0 = (43.26131216666667, -79.930344166667)  # ---------------signal coordination, to be modified ---------------#
    s_dist = gd.distance(coor0, coor1).km * 1000
    s_vel = speed

    last_speed = speed
    last_lat = lat
    last_lon = lon

    # sveh=15/3.6 # speed of individual vehicles
    # s_dist=s_dist+dbus

    if s_dist - b_dist > dbus:  # the bus is not stopping yet
        dateTimeObj = datetime.now()
        tcur = int((dateTimeObj.minute % 2) * 60 + dateTimeObj.second)

        # estimate the expected time when the car pass the intersection without bus stop
        tim0 = s_dist / s_vel + tcur
        tim1 = tim0 % tcyc
        if tim1 < gtim:
            timc0 = tim0
        else:
            timc0 = tim0 - tim1 + tcyc

        # estimate the expected time when the car pass the intersection with bus stop
        tmp0 = s_dist / s_vel + tdwl + tcur
        tmp1 = tmp0 % tcyc
        if tmp1 < gtim:
            timc1 = tmp0
        else:
            timc1 = tmp0 - tmp1 + tcyc

        if timc0 + 4.0 < timc1 and tcur % 5 == 0:
            sound_thread = threading.Thread(target=notify_driver)
            sound_thread.start()  # play lane changing instruction

            info = "Lane Changing Instruction is Generated" + "\n"
            out_traffic.write(info)


def notify_driver():
    play_sound = lane_change_sound.play()
    play_sound.wait_done()
