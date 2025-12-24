import os, sys
from pathlib import Path
from pyc3dsample import PyC3DSample

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

if len(sys.argv) < 2:
    print("Possible usage: uv run test_heelstrikes.py <c3d>")
    sys.exit(1)
else:
    c3dfile = Path(sys.argv[1])

Test = PyC3DSample(Path(c3dfile))

print("===========================================================")
print("Experimenting with different methods to detect heel strikes")
print("===========================================================")
print(
    "All different methods have a common condition that the heel marker " +
    "should be in front of the sternum marker."
)
print("")

# Velocity sign change in z-direction from - to +
rHeelStrike_Time = Test.get_HeelStrike('R', _method='zHeelVelocity')
lHeelStrike_Time = Test.get_HeelStrike('L', _method='zHeelVelocity')
print("Method zHeelVelocity: '-' to '+' sign change of heel marker z-velocity")
print(f"Right heel strike at : {rHeelStrike_Time}")
print(f"Left heel strike at  : {lHeelStrike_Time}")
print("")

# Acceleration sign change in y-direction - to +
rHeelStrike_Time_m1 = Test.get_HeelStrike('R', _method='yHeelAcceleration')
lHeelStrike_Time_m1 = Test.get_HeelStrike('L', _method='yHeelAcceleration')
print("Method yHeelAcceleration: '-' to '+' sign change of heel marker y-acceleration")
print(f"(m1) Right heel strike at : {rHeelStrike_Time_m1}")
print(f"(m1) Left heel strike at  : {lHeelStrike_Time_m1}")
print("")

# Snap sign change in y-direction + to -
rHeelStrike_Time_m2 = Test.get_HeelStrike('R', _method='yHeelSnap')
lHeelStrike_Time_m2 = Test.get_HeelStrike('L', _method='yHeelSnap')
print("Method yHeelSnap: '+' to '-' sign change of heel marker y-snap")
print(f"(m2) Right heel strike at : {rHeelStrike_Time_m2}")
print(f"(m2) Left heel strike at  : {lHeelStrike_Time_m2}")
print("")

# Plot
fig, axs = plt.subplots(2, 4, figsize=(17.5, 7.5), sharex=True)

# Get RHEE in z-axis
RHEE_z   = Test.get_TimeProgress("RHEE_Z")
RHEE_zd  = Test.get_TimeProgress1D("RHEE_Z")
RHEE_zdd = Test.get_TimeProgress2D("RHEE_Z")
RHEE_zdddd = Test.get_TimeProgress4D("RHEE_Z")

# Get RHEE in y-axis
RHEE_y   = Test.get_TimeProgress("RHEE_Y")
RHEE_yd  = Test.get_TimeProgress1D("RHEE_Y")
RHEE_ydd = Test.get_TimeProgress2D("RHEE_Y")
RHEE_ydddd = Test.get_TimeProgress4D("RHEE_Y")

axs[0,0].plot((RHEE_z[:,0]*100)+1, RHEE_z[:,1])
axs[0,0].set_title(r"RHEE Translation (z-Axis) $[mm]$", loc="left")
axs[0,0].grid()

axs[1,0].plot((RHEE_y[:,0]*100)+1, RHEE_y[:,1])
axs[1,0].set_title(r"RHEE Translation (y-Axis) $[mm]$", loc="left")
axs[1,0].grid()
axs[1,0].set_xlabel("Frame")

axs[0,1].plot((RHEE_zd[:,0]*100)+1, RHEE_zd[:,1])
axs[0,1].set_title(r"RHEE Velocity (z-Axis) $[mm / s]$", loc="left")
axs[0,1].grid()

axs[1,1].plot((RHEE_yd[:,0]*100)+1, RHEE_yd[:,1])
axs[1,1].set_title(r"RHEE Velocity (y-Axis) $[mm / s]$", loc="left")
axs[1,1].grid()
axs[1,1].set_xlabel("Frame")

axs[0,2].plot((RHEE_zdd[:,0]*100)+1, RHEE_zdd[:,1])
axs[0,2].set_title(r"RHEE Acceleration (z-Axis) $[mm / s^2]$", loc="left")
axs[0,2].grid()

axs[1,2].plot((RHEE_ydd[:,0]*100)+1, RHEE_ydd[:,1])
axs[1,2].set_title(r"RHEE Acceleration (y-Axis) $[mm / s^2]$", loc="left")
axs[1,2].grid()
axs[1,2].set_xlabel("Frame")

axs[0,3].plot((RHEE_zdddd[:,0]*100)+1, RHEE_zdddd[:,1])
axs[0,3].set_title(r"RHEE Snap (z-Axis) $[mm / s^4]$", loc="left")
axs[0,3].grid()

axs[1,3].plot((RHEE_ydddd[:,0]*100)+1, RHEE_ydddd[:,1])
axs[1,3].set_title(r"RHEE Snap (y-Axis) $[mm / s^4]$", loc="left")
axs[1,3].grid()
axs[1,3].set_xlabel("Frame")

for i in range(axs.shape[0]):
    for j in range(axs.shape[1]):
        for strike in rHeelStrike_Time:
            axs[i,j].axvline(x=(strike*100)+1, color='r', linestyle='--')

        for strike in rHeelStrike_Time_m1:
            axs[i,j].axvline(x=(strike*100)+1, color='b', linestyle='--')

        for strike in rHeelStrike_Time_m2:
            axs[i,j].axvline(x=(strike*100)+1, color='g', linestyle='--')

legend_elements = [
    Line2D(
        [0], [0], color='red', lw=2, linestyle=':', label='Velocity sign change (z)'
    ),
    Line2D(
        [0], [0], color='blue', lw=2, linestyle=':', label='Acceleration sign change (y)'
    ),
    Line2D(
        [0], [0], color='green', lw=2, linestyle=':', label='Snap sign change (y)'
    )
]
fig.legend(
    handles=legend_elements, loc='upper center',
    ncol=3, bbox_to_anchor=(0.5, 0.05)
)
fig.tight_layout(rect=[0, 0.025, 1, 1])

plt.show()
