import numpy as np
from scipy.linalg import block_diag

class Projection(object):
    """
    This class is used to specify the manual projection matrix
    for CMA. It is stored as an object and is only needed when
    self.options.man_proj = True.
    """

    def __init__(self,  options):

        self.options = options

    def run(self):

        stretch = np.array([
        1/np.sqrt(2)*np.array([1, 1]),
        1/np.sqrt(2)*np.array([1,-1]),
        ]).T

        HA_angles = np.eye(2)

        angles = np.array([
        1/np.sqrt(20)*np.array([ 4,-1,-1,-1,-1, 0]),
        1/np.sqrt( 4)*np.array([ 0, 1, 1,-1,-1, 0]),
        1/np.sqrt( 4)*np.array([ 0, 1,-1, 1,-1, 0]),
        1/np.sqrt( 4)*np.array([ 0, 1,-1,-1, 1, 0]),
        1/np.sqrt(30)*np.array([-1,-1,-1,-1,-1, 5]),
        ]).T


        #raise RuntimeError

        Proj = block_diag(stretch,stretch,angles)


        self.Proj = Proj

