import numpy as np
from ezc3d import c3d
from collections import defaultdict

import matplotlib.pyplot as plt

Angles = [
    "LHipAngles",
    "LKneeAngles",
    "LAbsAnkleAngle",
    "LAnkleAngles",
    "RHipAngles",
    "RKneeAngles",
    "RAnkleAngles",
    "RAbsAnkleAngle",
    "LPelvisAngles",
    "RPelvisAngles",
    "LFootProgressAngles",
    "RFootProgressAngles",
    "RNeckAngles",
    "LNeckAngles",
    "RSpineAngles",
    "LSpineAngles",
    "LShoulderAngles",
    "LElbowAngles",
    "LWristAngles",
    "RShoulderAngles",
    "RElbowAngles",
    "RWristAngles",
    "RThoraxAngles",
    "LThoraxAngles",
    "RHeadAngles",
    "LHeadAngles"
]
Markers = [
    "LFHD",
    "RFHD",
    "LBHD",
    "RBHD",
    "C7",
    "T10",
    "CLAV",
    "STRN",
    "RBAK",
    "LSHO",
    "LELB",
    "LWRA",
    "LWRB",
    "LFIN",
    "RSHO",
    "RELB",
    "RWRA",
    "RWRB",
    "RFIN",
    "LASI",
    "RASI",
    "LPSI",
    "RPSI",
    "LTHI",
    "LKNE",
    "LTIB",
    "LANK",
    "LTOE",
    "LBTO",
    "LHEE",
    "LMMA",
    "LMEC",
    "RTHI",
    "RKNE",
    "RTIB",
    "RANK",
    "RTOE",
    "RBTO",
    "RHEE",
    "RMMA",
    "RMEC"
]
VirtualMarkers = [
    "PELO",
    "PELA",
    "PELL",
    "PELP",
    "LFEO",
    "LFEA",
    "LFEL",
    "LFEP",
    "LTIO",
    "LTIA",
    "LTIL",
    "LTIP",
    "LFOO",
    "LFOA",
    "LFOL",
    "LFOP",
    "LTOO",
    "LTOA",
    "LTOL",
    "LTOP",
    "RFEO",
    "RFEA",
    "RFEL",
    "RFEP",
    "RTIO",
    "RTIA",
    "RTIL",
    "RTIP",
    "RFOO",
    "RFOA",
    "RFOL",
    "RFOP",
    "RTOO",
    "RTOA",
    "RTOL",
    "RTOP",
    "HEDO",
    "HEDA",
    "HEDL",
    "HEDP",
    "LCLO",
    "LCLA",
    "LCLL",
    "LCLP",
    "RCLO",
    "RCLA",
    "RCLL",
    "RCLP",
    "TRXO",
    "TRXA",
    "TRXL",
    "TRXP",
    "LHUO",
    "LHUA",
    "LHUL",
    "LHUP",
    "LRAO",
    "LRAA",
    "LRAL",
    "LRAP",
    "LHNO",
    "LHNA",
    "LHNL",
    "LHNP",
    "RHUO",
    "RHUA",
    "RHUL",
    "RHUP",
    "RRAO",
    "RRAA",
    "RRAL",
    "RRAP",
    "RHNO",
    "RHNA",
    "RHNL",
    "RHNP"
]

class PyC3DSample:
    """
    Class that takes a given C3D file (path) and transforms it to a
    "workable" Python object.
    """
    def __init__(self, path):
        self.ID          = str(path)
        self.SampleDict  = c3d(str(path))
        self.FrameRate   = self.SampleDict['header']['points']['frame_rate']
        self.FirstFrame  = self.SampleDict['header']['points']['first_frame']
        self.LastFrame   = self.SampleDict['header']['points']['last_frame']
        self.TimeStep    = 1 / self.FrameRate
        self.TotalFrames = (self.LastFrame - self.FirstFrame) + 1

        # Initialize dictionary to map marker names onto their data points
        MarkerNames = self.SampleDict['parameters']['POINT']['LABELS']['value']
        Marker_Name_DataPoints = defaultdict(np.array)
        for i, name in enumerate(MarkerNames):
            Marker_Name_DataPoints[name] = self.SampleDict[
                'data'
            ]['points'][0:3,i,:]

        # Get time-progression of
        # 1. biomechanical angles,
        # 2. markers, and
        # 3. virtual markers.
        self.BiomechanicalAngles       = {}
        self.MarkerTrajectories        = {}
        self.VirtualMarkerTrajectories = {}

        for marker in Marker_Name_DataPoints:
            if marker in Angles:
                self.BiomechanicalAngles[f"{marker}_X"] = Marker_Name_DataPoints[marker][0,:]
                self.BiomechanicalAngles[f"{marker}_Y"] = Marker_Name_DataPoints[marker][1,:]
                self.BiomechanicalAngles[f"{marker}_Z"] = Marker_Name_DataPoints[marker][2,:]
            elif marker in Markers:
                self.MarkerTrajectories[f"{marker}_X"] = Marker_Name_DataPoints[marker][0,:]
                self.MarkerTrajectories[f"{marker}_Y"] = Marker_Name_DataPoints[marker][1,:]
                self.MarkerTrajectories[f"{marker}_Z"] = Marker_Name_DataPoints[marker][2,:]
            elif marker in VirtualMarkers:
                self.VirtualMarkerTrajectories[f"{marker}_X"] = Marker_Name_DataPoints[marker][0,:]
                self.VirtualMarkerTrajectories[f"{marker}_Y"] = Marker_Name_DataPoints[marker][1,:]
                self.VirtualMarkerTrajectories[f"{marker}_Z"] = Marker_Name_DataPoints[marker][2,:]

        self.__dict__.update(self.BiomechanicalAngles)
        self.__dict__.update(self.MarkerTrajectories)
        self.__dict__.update(self.VirtualMarkerTrajectories)

        # Get initialize events
        self.initializeEvents()

    def __str__(self):
        _str = (
            f"ID          : {self.ID}\n" +
            f"FrameRate   : {self.FrameRate}\n" +
            f"TimeStep    : {self.TimeStep}\n" +
            f"FirstFrame  : {self.FirstFrame}\n" +
            f"LastFrame   : {self.LastFrame}\n" +
            f"TotalFrames : {self.TotalFrames}"
        )
        return _str

    def initializeEvents(self):
        """
        One can obtain the "time" at which an event is set, example:
        [[0. ] [1.22]]
        An event (f not mistaken) is always returned as a pair. In the
        example above, [0] refers to the event's index, which is followed
        by the time [1.22].
        """
        self.Events = []
        EventTimes = self.SampleDict["parameters"]["EVENT"]["TIMES"]['value']
        EventLabel = self.SampleDict["parameters"]["EVENT"]["LABELS"]['value']

        for i in range(EventTimes.shape[1]):
            self.Events.append(
                (EventLabel[i], round(float(EventTimes[1,i]), 2))
            )
        self.Events.sort(key=lambda x:x[1])

    def get_TimeProgress(self, _variable, plot=False):
        """
        Returns a np.array of the _variable's progress with respect to
        time.
        """
        StartTime = (self.FirstFrame - 1) * self.TimeStep
        FinalTime = (self.LastFrame - 1) * self.TimeStep

        TimeProgress = np.linspace(
            StartTime, FinalTime, self.TotalFrames
        ).round(2)

        if plot:
            self.plot_Curve(
                _variable, TimeProgress, self.__dict__[_variable], 'd'
            )

        return np.array([TimeProgress, self.__dict__[_variable]]).T

    def get_TimeProgressRange(self, _variable, _start, _end):
        """
        Returns a np.array of the _variable's progress with respect to
        time, for the specified range.

        Units for
         - Position : mm
         - Angle    : deg
        """
        # To account for floating-point erros
        _start = round(_start, 2)
        _end   = round(_end, 2)

        TimeProgress = np.linspace(
            _start, _end, int(round((_end-_start), 2)/self.TimeStep + 1)
        ).round(2)
        FullProgress = self.get_TimeProgress(_variable)

        # Must account for floating-point errors!
        _start_idx = np.where(FullProgress[:,0]==_start)[0][0]
        _end_idx   = np.where(FullProgress[:,0]==_end)[0][0]

        return np.array(
            [TimeProgress, FullProgress[_start_idx:_end_idx+1, 1]]
        ).T

    def get_TimeProgress1D(self, _variable, plot=False):
        """
        Returns a np.array of the first numerical derivative of _variable.
        Computed using numpy.gradient, which computes the gradient using the
        second order accurate central differences in the interior points,
        and the first order accurate one-sides differences at the boundaries.

        Units for
         - Position : mm/s
         - Angle    : deg/s
        """
        StartTime = (self.FirstFrame - 1) * self.TimeStep
        FinalTime = (self.LastFrame - 1) * self.TimeStep

        TimeProgress = np.linspace(
            StartTime, FinalTime, self.TotalFrames
        ).round(2)

        TimeProgress1D = np.gradient(self.__dict__[_variable], self.TimeStep)

        if plot:
            self.plot_Curve(_variable, TimeProgress, TimeProgress1D, 'v')

        return np.array([TimeProgress, TimeProgress1D]).T

    def get_TimeProgress2D(self, _variable, plot=False):
        """
        Returns a np.array of the second numerical derivative of _variable.
        Computed using numpy.gradient, which computes the gradient using the
        second order accurate central differences in the interior points,
        and the first order accurate one-sides differences at the boundaries.

        Units for
         - Position : mm/s
         - Angle    : deg/s
        """
        StartTime = (self.FirstFrame - 1) * self.TimeStep
        FinalTime = (self.LastFrame - 1) * self.TimeStep

        TimeProgress = np.linspace(
            StartTime, FinalTime, self.TotalFrames
        ).round(2)

        TimeProgress1D = np.gradient(self.__dict__[_variable], self.TimeStep)
        TimeProgress2D = np.gradient(TimeProgress1D, self.TimeStep)

        if plot:
            self.plot_Curve(_variable, TimeProgress, TimeProgress2D, 'a')
            
        return np.array([TimeProgress, TimeProgress2D]).T

    def get_TimeProgress3D(self, _variable, plot=False):
        """
        Returns a np.array of the third numerical derivative of _variable.
        Computed using numpy.gradient, which computes the gradient using the
        second order accurate central differences in the interior points,
        and the first order accurate one-sides differences at the boundaries.

        Units for
         - Position : mm/s
         - Angle    : deg/s
        """
        StartTime = (self.FirstFrame - 1) * self.TimeStep
        FinalTime = (self.LastFrame - 1) * self.TimeStep

        TimeProgress = np.linspace(
            StartTime, FinalTime, self.TotalFrames
        ).round(2)

        TimeProgress1D = np.gradient(self.__dict__[_variable], self.TimeStep)
        TimeProgress2D = np.gradient(TimeProgress1D, self.TimeStep)
        TimeProgress3D = np.gradient(TimeProgress2D, self.TimeStep)

        if plot:
            self.plot_Curve(_variable, TimeProgress, TimeProgress3D, '4')
            
        return np.array([TimeProgress, TimeProgress3D]).T

    def get_TimeProgress4D(self, _variable, plot=False):
        """
        Returns a np.array of the fourth numerical derivative of _variable.
        Computed using numpy.gradient, which computes the gradient using the
        second order accurate central differences in the interior points,
        and the first order accurate one-sides differences at the boundaries.

        Units for
         - Position : mm/s
         - Angle    : deg/s
        """
        StartTime = (self.FirstFrame - 1) * self.TimeStep
        FinalTime = (self.LastFrame - 1) * self.TimeStep

        TimeProgress = np.linspace(
            StartTime, FinalTime, self.TotalFrames
        ).round(2)

        TimeProgress1D = np.gradient(self.__dict__[_variable], self.TimeStep)
        TimeProgress2D = np.gradient(TimeProgress1D, self.TimeStep)
        TimeProgress3D = np.gradient(TimeProgress2D, self.TimeStep)
        TimeProgress4D = np.gradient(TimeProgress3D, self.TimeStep)

        if plot:
            self.plot_Curve(_variable, TimeProgress, TimeProgress4D, '4')
            
        return np.array([TimeProgress, TimeProgress4D]).T

    def plot_Curve(self, _variable, _time, _progress, _type):
        fig, ax = plt.subplots(1, 1)

        if _type == 'd':
            if not _variable.split('_')[0] in Angles:
                yLabel = r"Displacement $[mm / s]$"
            else:
                yLabel = r"Angle $[\circ]$"
        elif _type == 'v':
            if not _variable.split('_')[0] in Angles:
                yLabel = r"Velocity $[mm / s]$"
            else:
                yLabel = r"Ang. Velocity $[\circ / s]$"

        elif _type == 'a':
            if not _variable.split('_')[0] in Angles:
                yLabel = r"Acceleration $[mm / s^2]$"
            else:
                yLabel = r"Ang. Acceleration $[\circ / s^2]$"

        elif _type == 'j':
            if not _variable.split('_')[0] in Angles:
                yLabel = r"Jerk $[mm / s^3]$"
            else:
                yLabel = r"Ang. Jerk $[\circ / s^3]$"

        elif _type == 's':
            if not _variable.split('_')[0] in Angles:
                yLabel = r"Snap $[mm / s^4]$"
            else:
                yLabel = rf"Ang. Jerk $[\circ / s^4]$"

        ax.plot(_time, _progress)
        ax.set_xlabel(r"Time $[s]$")
        ax.set_ylabel(yLabel)
        ax.set_title(f"{_variable}", loc="left")
        ax.axvline(x=0.53, linestyle='--')
        ax.axvline(x=0.63, linestyle='--')
        ax.axvline(x=1.62, linestyle='--')
        ax.grid()
        plt.tight_layout()

    def get_VelocitySignChange(self, _variable):
        """
        Returns a list of tuples (<time-step before>, <time-step after>),
        containing the pair of time-steps, where the sign changes.
        """
        signchanges = []
        velocity = self.get_TimeProgress1D(_variable)

        staggered_v2 = velocity[:-1, 1] * velocity[1:, 1]
        # Negative elements indicate a sign change
        # Example: If staggered_v2[1] < 0, that means a sign change occured
        #          between velocity[1] and velocity[2]
        signchange_indices = np.where(staggered_v2 < 0)

        for i in signchange_indices[0]:
            signchanges.append(velocity[i:i+2,:])

        return signchanges

    def get_AccelerationSignChange(self, _variable):
        """
        Returns a list of tuples (<time-step before>, <time-step after>),
        containing the pair of time-steps, where the sign changes.
        """
        signchanges = []
        acc = self.get_TimeProgress2D(_variable)

        staggered_v2 = acc[:-1, 1] * acc[1:, 1]
        # Negative elements indicate a sign change
        # Example: If staggered_v2[1] < 0, that means a sign change occured
        #          between acc[1] and acc[2]
        signchange_indices = np.where(staggered_v2 < 0)

        for i in signchange_indices[0]:
            signchanges.append(acc[i:i+2,:])

        return signchanges

    def get_SnapSignChange(self, _variable):
        """
        Returns a list of tuples (<time-step before>, <time-step after>),
        containing the pair of time-steps, where the sign changes.
        """
        signchanges = []
        snap = self.get_TimeProgress4D(_variable)

        staggered_v2 = snap[:-1, 1] * snap[1:, 1]
        # Negative elements indicate a sign change
        # Example: If staggered_v2[1] < 0, that means a sign change occured
        #          between snap[1] and snap[2]
        signchange_indices = np.where(staggered_v2 < 0)

        for i in signchange_indices[0]:
            signchanges.append(snap[i:i+2,:])

        return signchanges

    def get_DisplacementHeelFromTrunk(self, _side, _forwardaxis):
        """
        Get absolute displacement of heel marker from sacrum marker.

        Idea: Heel strikes typically occurs with the heel in front of the trunk
        """
        STRN = self.get_TimeProgress(f"STRN_{_forwardaxis}")
        HEEL = self.get_TimeProgress(f"{_side}HEE_{_forwardaxis}")

        absDistance = HEEL[:,1] - STRN[:,1]
        absDistance = np.array([STRN[:,0], absDistance]).T

        return absDistance

    def get_TimeSteps_wSignChanges(
            self, _signchanges, _heelsternum, neg_to_pos=True
    ):
        """
        Functions takes two arrays:
        1. Array with pair of elements that indicate where the sign changes
           occurs
        2. Array with distances of heel marker from the sternum marker

        Function then
        1. selects the pairs where sign changes in specified direction and
        2. returns the selected pairs, where the heel markers is located in
           front of the sternum marker
        """
        return_list = []
        sel_pairs   = []
        
        if neg_to_pos:
            sel_pairs = [
                _pair for _pair in _signchanges if (
                    (_pair[1,1] >= 0.0) and (_pair[0,1] < 0.0)
                )
            ]
            selidx = 0
        else:
            sel_pairs = [
                _pair for _pair in _signchanges if (
                    (_pair[1,1] < 0.0) and (_pair[0,1] >= 0.0)
                )
            ]
            selidx = 1
    
        # Add corresponding distance of heel from sternum
        for _pair in sel_pairs:
            return_list.append(
                _heelsternum[
                    np.where(_heelsternum[:,0]==round(_pair[selidx,0], 2)),:
                ][0]
            )

        return return_list

    def get_HeelStrike(self, _side, _forwardaxis='Y', _method="zHeelVelocity"):
        """
        Get the heel strike based on two conditions that must be fulfilled:
        1. Velocity of heel marker switches from negative to positive, in 
           z-direction
        2. Maximum distance between heel and sacrum marker in _forwardaxis
           direction

        Returns time-step where heel-strike occurs

        Parameters
        ----------
        _side : {'R', 'L'}
        Option of right or left heel marker

        _forwardaxis = str (default: 'Y')
        Option of anterior axis

        _method : {'zHeelVelocity', 'yHeelAcceleration', 'yHeelSnap'}
        Option of determining heel strikes. All the methods have a
        common condition that the heel marker must be in front of the
        sternum marker. The other conditions are as the following:
        'zHeelVelocity'     : z-axis velocity of the heel marker changes from
                              negative to positive
        'yHeelAcceleration' : y-axis acceleration of the heel marker changes
                              from negative to positive
        'yHeelSnap'         : y-axis snap of the heel marker changes from
                              positive to negative
        """
        possible_sides = ['R', 'L']
        if not _side in possible_sides:
            raise ValueError(f"Invalid input: {_side}, possible inputs: 'R' or 'L'")

        heelstrn_distance = self.get_DisplacementHeelFromTrunk(_side, _forwardaxis)

        if _method == "zHeelVelocity":
            signChanges = self.get_VelocitySignChange(f"{_side}HEE_Z")
            neg_to_posInput = True

        elif _method == 'yHeelAcceleration':
            signChanges = self.get_AccelerationSignChange(
                f"{_side}HEE_{_forwardaxis}"
            )
            neg_to_posInput = True

        elif _method == 'yHeelSnap':
            signChanges = self.get_SnapSignChange(
                f"{_side}HEE_{_forwardaxis}"
            )
            neg_to_posInput = False

        # Get time-steps with respective sign-changes
        timesteps_wDisplacementHeelStrn = self.get_TimeSteps_wSignChanges(
            signChanges, heelstrn_distance, neg_to_pos=neg_to_posInput
        )

        # Only retain time-steps, where heel is in front of the sternum
        heelstrikes = [
            i for i in timesteps_wDisplacementHeelStrn if i[0,1] >= 0
        ]
        heelstrikes_timesteps = [
            round(float(pair[0,0]), 2) for pair in heelstrikes
        ]
        heelstrikes_timesteps.sort()

        return heelstrikes_timesteps
