import numpy as np
import pint
ureg = pint.UnitRegistry()

def soc2remainingCharge(soc):
    charge = 0.29182217878746003 * (100.0 - soc) + 0.24606563337628493 * np.sqrt(100.0 - soc) #formula to calc charge from soc
    assert charge >= 0.0
    #return charge * ureg.kilowatthour
    return charge


def remainingCharge2soc(charge):
    # wolfram alpha magic
    soc = -3.42674 * (-29.0785 + charge) + 1.6478263810833557*10**-44 * np.sqrt(4.654229268178746*10**86 + 8.972720402977183*10**87 * charge)
    assert soc >= 0 and soc <= 100.0
    return soc

