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
import pint
import pprint
import datetime
from myplotlib import init_figure, Columnes, Journal, save_figure
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ureg = pint.UnitRegistry()

# get weeks start and end
weeks = {} #: Array with first and last timestamp of every week in datetime format
for i in range(1, 53):
    weeks[i] = (datetime.datetime.strptime('2017-W{}-1'.format(i), "%Y-W%W-%w"),
                datetime.datetime.strptime('2017-W{}-1'.format(i + 1), "%Y-W%W-%w"))


def soc2remainingCharge(soc):
    charge = 0.29182217878746003 * (100.0 - soc) + 0.24606563337628493 * np.sqrt(100.0 - soc) #formula to calc charge from soc
    assert charge >= 0.0
    return charge * ureg.kilowatthour


def remainingCharge2soc(charge):
    # wolfram alpha magic
    soc = -3.42674 * (-29.0785 + charge) + 1.6478263810833557*10**-44 * np.sqrt(4.654229268178746*10**86 + 8.972720402977183*10**87 * charge)
    assert soc >= 0 and soc <= 100.0
    return soc

def aggregate_mobility_data():
    """Merge consecutive home entries in input data.

    This function reads the raw input data (Car_is_at_home_table.csv, every line corresponds to a 
    time span where the car was either at home or not. It is possible (even likely) that there are
    two consecutive lines that correspond to one continuous segment. 
    This function reads in the file line-by-line, stores it in a user (=car) based dictionary
    and merges consecutive home entries."""

    """Todo / possible bugs:
            - does the function only store home entries of users in the "users" dict? Then it would 
                always merge all the entries
            - When merging, the function does not check for temporal gaps.
            - It is not given, that the input data is sorted by date
        """
    users = defaultdict(list) #HM: What is this?
    current_user = None
    
    #-------------------------Explanation of input table 
    #Car_is_at_home_table.csv - is a table henry created. Every line corresponds to a continuous 
    #timespan where a specific car was at home. 
    #Time segments do not overlap (If everything works as inteded...)
    #Every segment has the timestamp for start and end of the segment and the power that is missing
    #in the beginning of the segment.
    
    #The segments were created by aggregating data from the bmw_matching_experiment table (This is 
    #the same as the bmw table but an ID was added).
    
    #! It is possible that two consecutive segments belong together as 1 continuous segment
    
    
    with open(os.path.join("..", "data", "Car_is_at_home_table.csv"), 'r') as f:
        reader = csv.DictReader(f, delimiter=',')

        for row in reader:
            user_id = row['vin'] #vin = the bmw id
            
            #HM: I don't get this... The vin can be none for user that quitted the study. We should 
            #drop all those samples
            if current_user is None: 
                current_user = user_id
            if not current_user == user_id:
                #                 with open("traces/user_{}.json".format(current_user), "w") as f:
                #                     json.dump(users[current_user], f, indent=4)
                current_user = user_id
            
            #read in data in "segment"
            segment = {}
            segment['start'] = row['start'] #start time
            segment['end'] = row['end']  #end time
            segment['missing_power_kwh'] = float(row['missing_power_kwh'])
            segment['is_home'] = row['is_home'] == "True"


#             print(row['start'], row['end'], row['is_home'], row['missing_power_kwh'])
            
            #Merge two consecutive home-segments
            # Check if last segment was already at home
            #HM: comments on checks:
                #len(users[user_id]) > 0: Checks if dictionary was already initialized 
                #                           (user_id already appeared)
            if segment['is_home'] and len(users[user_id]) > 0 and users[user_id][-1]['is_home']:
                #                 print("merge", segment['is_home'], len(users[user_id]) > 0, users[user_id][-1]['is_home'])
                users[user_id][-1]['end'] = row['end'] #set new time stamp
                users[user_id][-1]['missing_power_kwh'] = max(
                    users[user_id][-1]['missing_power_kwh'], float(row['missing_power_kwh']))
            else:
                users[user_id].append(segment)

    with open("traces.json", "w") as f:
        json.dump(users, f, indent=4)


def get_slot(d):
    """Return integer representation for month, day, hour, minute of a datestring object"""
    month = d.month
    day = d.day
    hour = d.hour
    minute = int(d.minute / 30) * 30 #round minute to 30 minutes
    return month, day, hour, minute

#days stores the number of days per month
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


def res_plot(states, vid):
    f, ax = init_figure(nrows=1,
                        ncols=1,
                        columnes=Columnes.TWO,
                        journal=Journal.ELSEVIER)

    xs = [s[0] for s in states]
    ys_org = [remainingCharge2soc(s[1]) for s in states]
    ys_pv = [remainingCharge2soc(s[2]) for s in states]
    ax.plot(xs, ys_org, label="raw")
    ax.plot(xs, ys_pv, label="PV")
    ax.legend()
    ax.set_xlabel("Time")
#     ax.set_ylabel("Energy demand [$\si{\kilo\watthour}$]")
    ax.set_ylabel("State of charge [\%]")

    for i in range(1, 36):

        ax.set_xlim(weeks[i][0], weeks[i][1])

        plt.savefig(os.path.join("charge_plots", "plot_vid_{}_week_{}.png".format(i, vid)),
                    dpi=600,
                    transparent=False)
#         save_figure(os.path.join("charge_plots", "plot_vid_{}_week_{}.png".format(i, vid)),
#                     dpi=600,
#                     tight_layout=True,
#                     close_plot=False)

    plt.close()


def pv_home_coverage():

    MIN_SOLAR_RAD = 0.0
    PV_EFF = 0.12

    # load traces
#    with open("traces.json", "r") as f:
#        traces = json.load(f)

    seen_vins = set()

    #open simulation data
    with open(os.path.join("..", "data", "Car_is_at_home_table.csv"), 'r') as data_file:
        all_data_df = pd.read_csv(data_file)
        all_data_df.sort_values(['vin','start'], inplace=True)
        #transform to date type
#         all_data_df['timestamp'] = all_data_df['timestamp'].astype('datetime64[ns]')
        all_data_df['start'] = all_data_df['start'].astype('datetime64[ns]')
        all_data_df['end'] = all_data_df['end'].astype('datetime64[ns]')

        # iterate over each user (via the csv with the different ids)
        with open(os.path.join('..', 'data', 'matching.csv'), 'r') as userid_file:
            reader = csv.DictReader(userid_file, delimiter=';')
            for row in reader:
                # %%initizalize user data

                bfsnr = row['GWR_gdenr']
                bid = row['bid']
                btype = row['btype']
                vin_this = row['BMW_vid']
                userid = row['BMW_userid']

                if len(vin_this) < 5:
                    continue

#                 if (vin_this,userid) in seen_vins:
#                     print("double", vin_this,userid)
#                 seen_vins.add((vin_this,userid))
#                 
#                 continue


#                 #HM: I think there was 1 Car that could not be matched...
#                 if not vin_this == "004c4ba86e77149b9bfe2dfebb4057a4":
#                     continue

                # %% load (user specific) solar data 
                solar_rad_path = os.path.join(
                    "..",
                    "data",
                    "solarrad",
                    "{}_{}.json".format(
                        btype,
                        bid))
                if not os.path.exists(solar_rad_path):
                    print("no solar rad data available: {}".format(solar_rad_path))
                    continue

                # Load solar irrad data
                with open(solar_rad_path, 'r') as ff:
                    sol_rad = json.load(ff)

                #HM: el_solar seems to allow to geht the power production for every half hour segment. 
                # el_solar is user_specific because the filename (solar_rad_path) is constructed 
                # user specific
                el_solar = defaultdict(
                    lambda: defaultdict(
                        lambda: 0.0 * ureg.watthour))

                # Parse solar irrad data and convert to electricity
                for k in sol_rad:
                    vs = k.split("_")
                    month = int(vs[0])
                    hour = int(vs[1])
                    minute = int(vs[2])
                    rad_cat = int(vs[3]) #HM: What is rad_cat
                    if rad_cat >= MIN_SOLAR_RAD:
                        el_solar[month][(hour, minute)] += float(sol_rad[k]) / \
                            days[month - 1] / 0.5 * PV_EFF * ureg.watthour

                def get_pv(start, end):
                    pv_pot = 0.0 * ureg.kilowatthour

                    _d = start
                    while _d <= end:
                        month, day, hour, minute = get_slot(_d)
                        # Divide by 30 as el is for 30 minute, but we operate in 1
                        # minute interval
                        pv_pot += el_solar[month][(hour, minute)] / 30.0

                        _d += datetime.timedelta(minutes=1)
                    return pv_pot

                # %%start simulation
                #filter data dataframe
                user_data_df = all_data_df[all_data_df['vin'] == vin_this]
#                 print(vin_this)

                tot_power_demand_home = 0.0 * ureg.kilowatthour
                tot_power_demand = 0.0 * ureg.kilowatthour
                tot_pv_covered_power_demand = 0.0 * ureg.kilowatthour

                #check if user_data_df is still sorted?
                for userdf_ix, userdf_row in user_data_df.iterrows():
                    start = userdf_row['start']
                    end = userdf_row['end']
                    soc_start = userdf_row['soc_start']
                    soc_end = userdf_row['soc_end']
                    is_home = userdf_row['is_home']

                    e_start = soc2remainingCharge(soc_start)
                    e_end = soc2remainingCharge(soc_end)

                    power_demand = e_start - e_end
                    
                    if power_demand > 0 * ureg.watthour:
                        tot_power_demand += power_demand
                    
                    # When we are away, we do nothing
                    if not is_home:
                        pass


                    # We are at home now
                    else:
#                       # if we consume energy while at home, we add that to
#                       # the virtual power demand
                        if e_end > e_start:
                            #TODO
                            pass

                        else:
                            # When we are home, we reduce the virtual power demand
                            # by as much as we can charge
                            pv = get_pv(start, end)

                            tot_power_demand_home += power_demand
                            # we can only consume as much pv as we would have charged
                            tot_pv_covered_power_demand += min(power_demand, pv)

#                             print(soc_start, soc_end, power_demand, pv)
#                             print("pv", pv.to(ureg.kilowatthour).magnitude)
#                             virtual_power_demand -= pv.to(ureg.kilowatthour).magnitude

                if tot_power_demand.magnitude == 0.0:
                    print(vin_this, "no power demand???")
                else:
                    pv_cover_ratio = (tot_pv_covered_power_demand / tot_power_demand).magnitude * 100.0
    
                    if tot_power_demand_home.magnitude > 0.0:
                        pv_cover_home_ratio = (tot_pv_covered_power_demand / tot_power_demand_home).magnitude * 100.0
                        print(vin_this, round(pv_cover_ratio,1), round(pv_cover_home_ratio, 1))
                    else:
                        print(vin_this, round(pv_cover_ratio,1), "tot_power_demand == 0 !!!!!")


#                     # %% I stopped writing code here...
#                     #do something with userdf_row
#                     #HM: Now the actual simulation starts 
# 
# 
#                             vin = row['vin']
# 
#                             if not vin == vid:
#                                 continue
# 
#                             tstart = datetime.datetime.strptime(
#                                 row['start'], '%Y-%m-%d %H:%M:%S')
#                             tend = datetime.datetime.strptime(
#                                 row['end'], '%Y-%m-%d %H:%M:%S')
# 
#         #                     if tend > datetime.datetime(2017, 1, 28, 0, 0):
#         #                         break
#         
#                             is_home = row['is_home'] == 'True'
#                             soc_start = float(row['soc_start'])
#                             soc_end = float(row['soc_end'])
#                             zustand = json.loads(row['zustand'].replace("'", '"'))
#         
#                             e_start = soc2remainingCharge(soc_start)
#                             e_end = soc2remainingCharge(soc_end)
#         
#                             res.append((tstart,
#                                         e_start,
#                                         virtual_power_demand,
#                                         is_home))
#         
#                             print("\t".join(list(map(str, ("s", tstart, soc_start, round(e_start, 1), round(virtual_power_demand, 1), is_home)))))
#         

#         
#                             virtual_power_demand = max(0, virtual_power_demand)
#                             print("\t".join(list(map(str, ("e", tend, soc_end, round(e_end, 1), round(virtual_power_demand, 1), is_home)))))
#         #                     print(tend, round(remainingCharge2soc(e_end), 1), round(remainingCharge2soc(virtual_power_demand), 1))
#         
#         
#                             res.append((tend, e_end, virtual_power_demand, is_home))
#     
#                 res_plot(res, vin)
#                 break


if __name__ == '__main__':
    #     aggregate_mobility_data()
    pv_home_coverage()
