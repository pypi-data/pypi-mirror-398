import pytest
import os
from pathlib import Path
from pyc3dsample import PyC3DSample

def test_initializeobject():
    Test = PyC3DSample(Path("data/testsample.c3d"))

    # Get general information about C3D file
    print(Test)

def test_get_Events():
    Test = PyC3DSample(Path("data/testsample.c3d"))

    # Get events -> List of (<label>, <time [s]>)
    assert Test.Events == [('Event', 0.99)]
    print(Test.Events)

def test_getTimeProgressRange():
    Test = PyC3DSample(Path("data/testsample.c3d"))

    EventEvent = [e for e in Test.Events if e[0] == 'Event'][0][1]
    print(
        Test.get_TimeProgressRange("LKneeAngles_X", EventEvent-0.1, EventEvent)
    )

def test_getTimeProgress1D():
    Test = PyC3DSample(Path("data/testsample.c3d"))

    print(Test.get_TimeProgress1D("LKneeAngles_X"))

def test_getHeelStrikes():
    Test = PyC3DSample(Path("data/testsample.c3d"))

    rHeelStrike_Time = Test.get_HeelStrike('R')
    lHeelStrike_Time = Test.get_HeelStrike('L')
    print(f"Right heel strike at : {rHeelStrike_Time}")
    print(f"Left heel strike at  : {lHeelStrike_Time}")
