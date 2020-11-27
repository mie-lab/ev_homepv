# EV-Home-PV
A project to analyze how much of our mobility energy demand (induced by electric vehicles) we can cover by using only pv installed on our own home. 

The generated outputs in `data/output` have the following fields:

* `generated_by_pv`: PV generation by segment including kW restriction from E-Car
* `charged_from_pv_unrestricted`: PV generation by segment without restriction
* `needed_by_car`: Energy demand of car
* `charged_from_pv`: PV &rarr; car
* `charged_from_outside`: Grid &rarr; car

All these data are available per timestep.

Scenarios 2 + 3 simulate a charging curve. 
Thus, there are additional state variables that describe the state of charge for the car (and for scenario 3 a description of the SoC of the battery, marked as S3).

* `kWh_start`: Car SoC at the beginning of the segment
* `kWh_end`: Car SoC at the end of the segment
* `max_kWh`: Maximal charge of the car in kWh (constant)
* `battery_start`: State of charge of battery at beginning of segment (S3)
* `battery_end`: State of charge of battery at end of segment (S3)
* `battery_used_by_car`: Battery &rarr; car
* `total_segment_consumption_kWh`: Energy that was used by a car in a segment

As a general rule, `kWh_start - kWh_end + charged_from_pv  + charged_from_outside + min(total_segment_consumption_kWh, max_kWh) == 0`.
In scenario 3, `battery_used_by_car` is included in `charged_from_pv`.
