'''
    RawSliceImage.py

    Example code to demonstrate basic raw imaging and tracking
    with the Walabot Creator or Developer.

    Created on 3 Nov 2017

    @author: Ohad Tzafrir <ohad.tzafrir@vayyar.com>
'''

import matplotlib
import time
import sys
import os

if os.name == 'nt':
    from msvcrt import getch, kbhit
else:
    import curses

matplotlib.use('tkagg')

import matplotlib.pyplot as plt
import WalabotAPI as wb
import numpy as np

from matplotlib.cm import ScalarMappable
from matplotlib import patches
from matplotlib import animation

# Select scan arena
#             R             Phi          Theta
ARENA = [(40, 300, 4), (-60, 60, 5), (-15, 15, 5)]


def pol2cart(theta, r):
    '''Convert polar coordinates, in radians, to cartesian'''
    return(r * np.sin(theta), r * np.cos(theta))


def pol2cart_deg(theta, r):
    '''Convert polar coordinates, in degrees, to cartesian'''
    return pol2cart(np.deg2rad(theta), r)


def GenPosMap():
    '''Create position coordinates map for plotting'''
    # Phi range vector
    arrP = list(range(*ARENA[1])) + [ARENA[1][1]]

    # R range vector
    arrR = list(range(*ARENA[0])) + [ARENA[0][1]]

    # Format of pmap is [[list of X],[list of Y],[list of dot size]]
    pmap = np.array([list(pol2cart_deg(p, ra)) + [ra * 0.75] for ra in arrR for p in arrP]).transpose()
    return pmap


def prep_plot(stdscr, posmap):
    '''Animated plot'''

    if stdscr is not None:
        stdscr.nodelay(1)

    # Capture first image
    wb.Trigger()
    M, _, _, _, _ = wb.GetRawImageSlice()
    s = np.array([val for phi in M for val in phi], dtype=np.float32)

    fig = plt.figure()
    sm = ScalarMappable(cmap='coolwarm')
    ax = fig.add_subplot(111, facecolor=sm.to_rgba(0))
    sm = ScalarMappable(cmap='coolwarm')
    p = ax.scatter(posmap[0], posmap[1], s=posmap[2], c=s, cmap='coolwarm')

    def plot_update(image):
        '''Update plot colors'''

        # Update image colors according to return signal strength
        p.set_color(sm.to_rgba(image))

        return (p,)

    def get_image():
        '''Get image from Walabot server'''
        threshold = 1.0
        active = True

        while active:
            wb.Trigger()
            M, _, _, _, _ = wb.GetRawImageSlice()

            image = np.array([val for phi in M for val in phi], dtype=np.float32)

            yield image

            if os.name == 'nt':
                if kbhit():
                    key = ord(getch())
                else:
                    key = -1
            else:
                key = stdscr.getch()

            if key != -1:
                if key == ord('q'):
                    active = False

                elif key == 224:
                    if os.name == 'nt':
                        key = ord(getch())
                    else:
                        key = stdscr.getch()

                    if key == 72:
                        threshold += 0.1
                    elif key == 73:
                        threshold += 1.0
                    elif key == 80:
                        threshold -= 0.1
                    elif key == 81:
                        threshold -= 1.0

#                if is_set == 'set':
#                    print("Tracker threshold = {0:f}".format(threshold))

    ani = animation.FuncAnimation(fig, func=plot_update, frames=get_image,
                                  repeat=False, interval=0, blit=True)
    try:
        plt.show()
    except:
        pass


if __name__ == '__main__':

    # Star Walabot capture process
    print("Initialize API")
    wb.Init()

    # Check if a Walabot is connected
    try:
        wb.ConnectAny()

    except wb.WalabotError as err:
        print("Failed to connect to Walabot.\nerror code: " + str(err.code))
        sys.exit(1)

    ver = wb.GetVersion()
    print("Walabot API version: {}".format(ver))

    print("Connected to Walabot")
    wb.SetProfile(wb.PROF_SENSOR)

    # Set scan arena
    wb.SetArenaR(*ARENA[0])
    wb.SetArenaPhi(*ARENA[1])
    wb.SetArenaTheta(*ARENA[2])
    print("Arena set")

    # Set image filter
    wb.SetDynamicImageFilter(wb.FILTER_TYPE_MTI)

    # Start scan
    wb.Start()
    wb.StartCalibration()

    stat, prog = wb.GetStatus()

    while stat == wb.STATUS_CALIBRATING and prog < 100:
        print("Calibrating " + str(prog) + "%")
        wb.Trigger()
        stat, prog = wb.GetStatus()

    posmap = GenPosMap()

    print("Setting plot")
    if os.name == 'nt':
        prep_plot(None, posmap)
    else:
        curses.wrapper(prep_plot, posmap)

    wb.Stop()
    wb.Disconnect()

    print("Done!")

    sys.exit(0)
