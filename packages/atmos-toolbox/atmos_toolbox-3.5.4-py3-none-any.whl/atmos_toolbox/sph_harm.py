import pyshtools
import numpy as np

# def sh_smooth_xr(F, trunc=None,):
#     '''
#     Parameters
#     ----------
#     F : xarray
#         global field, has the shape of N*N or N*2N, do not need data on 90S and 360W.
#     trunc : int
#         truncation

#     Returns
#     -------
#     F_sm : xarray
#         smoothed F
#     l_max : int
#         largest truncation number
#     '''
    
#     grid = pyshtools.SHGrid.from_xarray(F, grid='DH')
#     coef = grid.expand()
#     l_max = coef.lmax 
    
#     if trunc==None:
#         coef_adj = coef.copy()
#     else:        
#         coef_temp = coef.pad(lmax=trunc)
#         coef_adj  = coef_temp.pad(lmax=l_max)
    
#     grid_adj = coef_adj.expand() 
#     F_sm = grid_adj.to_xarray()
     
#     return F_sm, l_max 

def sh_smooth_xr(F, trunc=None, damp=None,):
    '''
    Parameters
    ----------
    F : xarray
        global field, has the shape of N*N or N*2N, do not need data on 90S and 360W.
    trunc : int
        truncation, commonly set as 47 or 63.
    damp : int
        half-life wavenumber, commonly set as 24.

    Returns
    -------
    F_sm : xarray
        smoothed F
    '''
    
    grid = pyshtools.SHGrid.from_xarray(F, grid='DH')
    coef = grid.expand()
    coef_arr = coef.coeffs
    l_max = coef.lmax 
    
    if trunc==None:
        wgt = np.ones(l_max+1)
    else:
        if damp==None:
            wgt = np.ones(l_max+1)
            wgt[trunc+1:] = 0.0 
        else:
            kk = -1*np.log(0.5) / (damp*(damp+1)**2)
            l_max_arr = np.arange(0, l_max+1)
            wgt = np.exp(-kk*l_max_arr*(l_max_arr+1)**2)
            wgt[trunc+1:] = 0.0 
    
    wgt_ext = wgt[np.newaxis, :, np.newaxis]
    
    coef_adj_arr = coef_arr * wgt_ext
    coef_adj = pyshtools.SHCoeffs.from_array(coef_adj_arr)
    
    grid_adj = coef_adj.expand() 
    F_sm = grid_adj.to_xarray()
    
    return F_sm