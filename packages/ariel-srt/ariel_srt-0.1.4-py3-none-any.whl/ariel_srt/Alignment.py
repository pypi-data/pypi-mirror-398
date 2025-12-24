import numpy as np
import thinplate as tps


def rigid_alignment(lm1, lm2, coord2 = None):
    one=np.ones(lm2.shape[0])
    lm2_1=np.insert(lm2,2,one,axis=1)
    M=np.dot(np.dot(np.linalg.inv(np.dot(lm2_1.T,lm2_1)),lm2_1.T),lm1)
    lm2_tran=np.dot(lm2_1,M)
    if coord2 is None :
        return lm2_tran
    else:
        coord2_1=np.c_[coord2,np.ones(coord2.shape[0])]
        coord2_tran=np.dot(coord2_1,M)
        return lm2_tran, coord2_tran            


def non_rigid_alignment(lm1,lm2, coord2 = None):
    theta = tps.tps_theta_from_points(lm1,lm2, reduced=True)
    theta_x = theta[:, 0]
    theta_y = theta[:, 1]
    
    transformed_lm_x = tps.TPS.z(lm2, lm2, theta_x)
    transformed_lm_y = tps.TPS.z(lm2, lm2, theta_y)
    transformed_lm_xy = np.column_stack([transformed_lm_x, transformed_lm_y])
    lm2_tran = lm2 + transformed_lm_xy
    
    if coord2 is None :
        return lm2_tran
    else:
        transformed_x = tps.TPS.z(coord2, lm2, theta_x)
        transformed_y = tps.TPS.z(coord2, lm2, theta_y)
        transformed_xy = np.column_stack([transformed_x, transformed_y])
        coord2_tran = coord2 + transformed_xy
        return lm2_tran, coord2_tran

''' 
old version, has been discarded

def b0(x):
    x=((1-x)**3)/6
    return x

def b1(x):
    x=(3*x**3-6*x**2+4)/6
    return x

def b2(x):
    x=(-3*x**3+3*x**2+3*x+1)/6
    return x

def b3(x):
    x=x**3/6
    return x

def warp(points,grid,gx,gy):
    warp_p=np.zeros(points.shape)
    for i in range(points.shape[0]):
        xleft=int(points[i,0]/gx)
        ylow=int(points[i,1]/gy)
    
        dx=points[i,0]/gx-xleft
        dy=points[i,1]/gy-ylow

        if(xleft==19):
            if(ylow==19):
                warp_p[i,:]=grid[xleft,ylow]
            elif(ylow>0 and ylow<18):
                warp_p[i,:]=grid[xleft,ylow-1]*b0(dy)+grid[xleft,ylow]*b1(dy)+grid[xleft,ylow+1]*b2(dy)+grid[xleft,ylow+2]*b3(dy)
            else:
                warp_p[i,:]=grid[xleft,ylow]*(1-dy)+grid[xleft,ylow+1]*dy
            
        elif(xleft>0 and xleft<18):
            if(ylow==19):
                warp_p[i,:]=grid[xleft-1,ylow]*b0(dx)+grid[xleft,ylow]*b1(dx)+grid[xleft+1,ylow]*b2(dx)+grid[xleft+2,ylow]*b3(dx)
            elif(ylow>0 and ylow<18):
                warp_p[i,:]=grid[xleft-1,ylow-1,:]*b0(dx)*b0(dy)+grid[xleft-1,ylow]*b0(dx)*b1(dy)+grid[xleft-1,ylow+1]*b0(dx)*b2(dy)+grid[xleft-1,ylow+2]*b0(dx)*b3(dy)+grid[xleft,ylow-1]*b1(dx)*b0(dy)+grid[xleft,ylow]*b1(dx)*b1(dy)+grid[xleft,ylow+1]*b1(dx)*b2(dy)+grid[xleft,ylow+2]*b1(dx)*b3(dy)+grid[xleft+1,ylow-1]*b2(dx)*b0(dy)+grid[xleft+1,ylow]*b2(dx)*b1(dy)+grid[xleft+1,ylow+1]*b2(dx)*b2(dy)+grid[xleft+1,ylow+2]*b2(dx)*b3(dy)+grid[xleft+2,ylow-1]*b3(dx)*b0(dy)+grid[xleft+2,ylow]*b3(dx)*b1(dy)+grid[xleft+2,ylow+1]*b3(dx)*b2(dy)+grid[xleft+2,ylow+2]*b3(dx)*b3(dy)
            else:
                warp_p[i,:]=grid[xleft-1,ylow]*b0(dx)*(1-dy)+grid[xleft-1,ylow+1]*b0(dx)*dy+grid[xleft,ylow]*b1(dx)*(1-dy)+grid[xleft,ylow+1]*b1(dx)*dy+grid[xleft+1,ylow]*b2(dx)*(1-dy)+grid[xleft+1,ylow+1]*b2(dx)*(dy)+grid[xleft+2,ylow]*b3(dx)*(1-dy)+grid[xleft+2,ylow+1]*b3(dx)*dy
            
        else:
            if(ylow==19):
                warp_p[i,:]=grid[xleft,ylow]*(1-dx)+grid[xleft+1,ylow]*dx
            elif(ylow>0 and ylow<18):
                warp_p[i,:]=grid[xleft,ylow-1]*(1-dx)*b0(dy)+grid[xleft,ylow]*(1-dx)*b1(dy)+grid[xleft,ylow+1]*(1-dx)*b2(dy)+grid[xleft,ylow+2]*(1-dx)*b3(dy)+grid[xleft+1,ylow-1]*dx*b0(dy)+grid[xleft+1,ylow]*dx*b1(dy)+grid[xleft+1,ylow+1]*dx*b2(dy)+grid[xleft+1,ylow+2]*dx*b3(dy)
            else:
                warp_p[i,:]=grid[xleft,ylow,:]*(1-dx)*(1-dy)+grid[xleft+1,ylow,:]*dx*(1-dy)+grid[xleft+1,ylow+1,:]*dx*dy+grid[xleft,ylow+1,:]*(1-dx)*dy
            
    return warp_p
'''