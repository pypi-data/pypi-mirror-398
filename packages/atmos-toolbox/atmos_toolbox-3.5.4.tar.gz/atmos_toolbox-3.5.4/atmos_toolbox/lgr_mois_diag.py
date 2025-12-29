import numpy as np

def watersip(q_raw, thod=0.1):
    
    '''
    dimensionless time is used.
    q_raw is an 1-D array.
    q_raw is the SH of a backward trajectory.
    '''
    
    # thod  = 0.1 #under which uptakes are ignored
    # q_raw = np.random.rand(10) #specific humidity
    t_raw = np.arange(0, -len(q_raw), -1) #dimensionless time
    
    q1 = np.flip(q_raw)
    dq = np.diff(q1)
    dq = np.where((dq>0)&(dq<thod), 0, dq)
    
    q = q1[1:]
    t = np.flip(t_raw)[1:]
    
    e = np.zeros(dq.shape)
    f = e.copy()
    
    for ti in t:
        if dq[t==ti]>0:
            e[t==ti] = dq[t==ti]
            f[t==ti] = e[t==ti] / q[t==ti]
            
            for tj in t[ti>t]:
                if e[t==tj]>0:
                    f[t==tj] = e[t==tj] / q[t==ti]
        
        elif dq[t==ti]<0:
            for tj in t[ti>t]:
                if e[t==tj]>0:
                    e[t==tj] += dq[t==ti] * f[t==tj] 
    
                    # since the threshold, so we need:
                    if e[t==tj]<0:
                        e[t==tj]=0 
                        f[t==tj]=0 
                
    attrq = -dq[-1] * f
    attrq = np.flip(attrq)
    attrq = np.append(attrq,0)
    
    return attrq