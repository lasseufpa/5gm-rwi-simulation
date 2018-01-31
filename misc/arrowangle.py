from matplotlib import pyplot as plt
import numpy as np

def arrow_angle(i, j):

    #i = 3 #index of best beam for Tx
    #j = 5 #index of best beam for Rx
    Ni = 16 #number of Tx beams
    Nj = 16 #number of Rx beams
    mag = 50 #magnitude of vector
    deltaI = (2 * np.pi) / Ni #angle for each beam in Tx
    deltaJ = (2 * np.pi) / Nj #angle for each beam in Rx

    #for i in range(Ni):
    #    for j in range(Nj):
    angleI = i * deltaI - (deltaI / 2)
    angleJ = j * deltaJ - (deltaJ / 2)
    vectorI = mag * np.exp(1j * angleI)
    vectorJ = mag * np.exp(1j * angleJ)

    #plot two vectors keeping the aspect ratio to denote a circle.
    #Use different colors

    line1 = np.array([[0, np.real(vectorI)], [0, np.imag(vectorI)]])
    line2 = np.array([[0, np.real(vectorJ)], [0, np.imag(vectorJ)]])
    return line1, line2

    plt.plot([0, np.real(vectorI)], [0, np.imag(vectorI)], '-xb')
    plt.hold(True)
    plt.plot([0, np.real(vectorJ)], [0, np.imag(vectorJ)], '-or')
    plt.title('{} and {}'.format(i, j))
    plt.axis(mag * np.array([-1.2, 1.2, -1.2, 1.2]))
    plt.show()