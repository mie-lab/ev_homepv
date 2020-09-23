'''
Created on Aug 29, 2018

@author: rene
'''
from _collections import defaultdict
import csv
from datetime import date
import datetime
import json
import os
import pprint

import pint


ureg = pint.UnitRegistry()


def missing_energy_from_soc(soc):
    """
    Calculates the energy to reach a full battery

    soc: percentage of state of charge [0, 100]

    """
    e = 0.266428 + (100.0 - soc) * 0.328096
    return e


def aggregate_mobility_data():

    users = defaultdict(list)

    current_user = None
    with open(os.path.join("..", "data_PV_Solar", "Car_is_at_home_table.csv"), 'r') as f:
        reader = csv.DictReader(f, delimiter=',')

        for row in reader:

            user_id = row['vin']
            if current_user is None:
                current_user = user_id

            if not current_user == user_id:
#                 with open("traces/user_{}.json".format(current_user), "w") as f:
#                     json.dump(users[current_user], f, indent=4)
                current_user = user_id

            segment = {}
            segment['start'] = row['start']
            segment['end'] = row['end']
            segment['missing_power_kwh'] = float(row['missing_power_kwh'])
            segment['is_home'] = row['is_home'] == "True"

#             print(row['start'], row['end'], row['is_home'], row['missing_power_kwh'])
            # Check if last segment was already at home
            if segment['is_home'] and len(users[user_id]) > 0 and users[user_id][-1]['is_home']:
#                 print("merge", segment['is_home'], len(users[user_id]) > 0, users[user_id][-1]['is_home'])
                users[user_id][-1]['end'] = row['end']
                users[user_id][-1]['missing_power_kwh'] = max(users[user_id][-1]['missing_power_kwh'], float(row['missing_power_kwh']))
            else:
                users[user_id].append(segment)

    with open("traces.json", "w") as f:
        json.dump(users, f, indent=4)

def get_slot(d):
    month = d.month
    day = d.day
    hour = d.hour
    minute = int(d.minute / 30) * 30
    return month, day, hour, minute


days = [
    31.0,
    28.0,
    31.0,
    30.0,
    31.0,
    30.0,
    31.0,
    31.0,
    30.0,
    31.0,
    30.0,
    31.0]


def pv_home_coverage():

    MIN_SOLAR_RAD = 0.0
    PV_EFF = 0.12

    # load traces
    with open("traces.json", "r") as f:
        traces = json.load(f)

    # iterate over each user    
    with open(os.path.join('..', 'data_PV_Solar', 'matching.csv'), 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            bfsnr = row['GWR_gdenr']
            bid = int(row['bid'])
            btype = row['btype']

            vid = row['BMW_vid']

            if not vid == "004c4ba86e77149b9bfe2dfebb4057a4":
                continue


            print("Processing {}".format(vid))
            print(btype, bid)

#             if vid not in traces:
#                 print("VID not in traces data_PV_Solar: {}".format(vid))
#                 continue

            solar_rad_path = os.path.join("..", "data_PV_Solar", "solarrad", "{}_{}.json".format(btype, bid))
            if not os.path.exists(solar_rad_path):
                print("no solar rad data_PV_Solar available: {}".format(solar_rad_path))
                continue

            # Load solar irrad data_PV_Solar
            with open(solar_rad_path, 'r') as ff:
                sol_rad = json.load(ff)

            tot_el = 0.0 * ureg.watthour
            el_solar = defaultdict(lambda: defaultdict(lambda: 0.0 * ureg.watthour))

            # Parse solar irrad data_PV_Solar and convert to electricity
            for k in sol_rad:
                vs = k.split("_")
                month = int(vs[0])
                hour = int(vs[1])
                minute = int(vs[2])
                rad_cat = int(vs[3])
                if rad_cat >= MIN_SOLAR_RAD:
                    tot_el += float(sol_rad[k]) * ureg.watthour
                    # solar irrad is for month, we need to convert to half hour interval
                    el_solar[month][(hour, minute)] += float(sol_rad[k]) / days[month - 1] / 0.5 * PV_EFF * ureg.watthour

            # Parse traces
#             segments = []
#             with open(os.path.join("..", "data_PV_Solar", "Car_is_at_home_table.csv"), 'r') as ff:
#                 reader = csv.DictReader(ff, delimiter=',')
# 
#                 for row in reader:
#                     if not row['vin'] == vid:
#                         continue
# 
#                     s = {}
#                     #2017-01-26 09:42:00
#                     s['start'] = datetime.datetime.strptime(row['start'], '%Y-%m-%d %H:%M:%S')
#                     s['end'] = datetime.datetime.strptime(row['end'], '%Y-%m-%d %H:%M:%S')
#                     s['is_home'] = row['is_home'] == 'True'
#                     s['missing_power_kwh'] = float(row['missing_power_kwh'])
#                     s['zustand'] = json.loads(row['zustand'].replace("'", '"'))
# 
#                     # We merge when we are multiple time at home
#                     if s['is_home'] and len(segments) > 0 and segments[-1]['is_home']:
#                         segments[-1]['end'] = s['end']
#                         segments[-1]['missing_power_kwh'] = max(segments[-1]['missing_power_kwh'], s['missing_power_kwh'])
#                     else:
#                         segments.append(s)

#             tot_energy_home = defaultdict(lambda: 0.0 * ureg.kilowatthour)
#             covered_energy_home = defaultdict(lambda: 0.0 * ureg.kilowatthour)

            def get_pv(start, end):
                pv_pot = 0.0 * ureg.kilowatthour

                _d = start
                while _d <= end:
                    month, day, hour, minute = get_slot(_d)
                    # Divide by 30 as el is for 30 minute, but we operate in 1 minute interval
                    pv_pot += el_solar[month][(hour, minute)] / 30.0

                    _d += datetime.timedelta(minutes=1)
                return pv_pot

            virtual_power_demand = None

            with open(os.path.join("..", "data_PV_Solar", "Car_is_at_home_table.csv"), 'r') as ff:
                reader = csv.DictReader(ff, delimiter=',')
                for row in reader:

                    if not vid == row['vin']:
                        continue 

                    start = datetime.datetime.strptime(row['start'], '%Y-%m-%d %H:%M:%S')
                    end = datetime.datetime.strptime(row['end'], '%Y-%m-%d %H:%M:%S')
                    is_home = row['is_home'] == 'True'
                    e_start = missing_energy_from_soc(float(row['soc_start']))
                    e_end = missing_energy_from_soc(float(row['soc_end']))
                    zustand = json.loads(row['zustand'].replace("'", '"'))

                    print(("\t".join([str(start), str(end), str(is_home), row['soc_start'], str(round(e_start, 2)), row['soc_end'], str(round(e_end, 2))])))
                    if virtual_power_demand is None:
                        virtual_power_demand = e_start

                    # When we are away, we add the power demand of the segment to the virtual power demand
                    if not is_home:
                        virtual_power_demand += (e_end - e_start)

                    print(round(virtual_power_demand, 2))
#                     if is_home:
#                         if start > end:

#             for i, s in enumerate(segments):
#                 if i == 0:
#                     virtual_power_demand = s['missing_power_kwh']
# 
#                 # When we are away, we add the power demand of the segment to the virtual power demand 
#                 if i > 0: # and not s['is_home']:
#                     virtual_power_demand += (s['missing_power_kwh'] - segments[i - 1]['missing_power_kwh'])
# 
#                     # Driver can have charged away, but it would be not necessary when charging at home through pv
#                     virtual_power_demand = max(0.0, virtual_power_demand)
# 
#                 # When we are home, we reduce the virtual power demand by as much as we can charge
#                 if s['is_home']:
#                     print(str(s['start']), str(s['end']), get_pv(s['start'], s['end']))
#                     pv = get_pv(s['start'], s['end']).to(ureg.kilowatthour).magnitude
#                     print(pv)
# 
#                     virtual_power_demand -= pv
#                     # We can not charge more than 0
#                     virtual_power_demand = max(0.0, virtual_power_demand)
#                 print(s, virtual_power_demand)

            break




if __name__ == '__main__':
#     aggregate_mobility_data()
    pv_home_coverage()


