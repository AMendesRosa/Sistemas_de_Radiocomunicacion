import numpy as np
def cap_assign(X,C,cap):
    """Asigna puntos X a centros C respetando capacidad (greedy por arrepentimiento)."""
    D=np.abs(X[:,None,0]-C[None,:,0])+np.abs(X[:,None,1]-C[None,:,1])   # distancia Manhattan
    o=np.sort(D,1); reg=(o[:,1]-o[:,0]) if D.shape[1]>1 else -o[:,0]
    lab=-np.ones(len(X),int); load=np.zeros(len(C),int)
    for i in np.argsort(-reg):
        for j in np.argsort(D[i]):
            if load[j]<cap: lab[i]=j; load[j]+=1; break
    return lab
def cap_kmeans(X,k,cap,init=None,it=15):
    C=np.array(init,float) if init is not None else X[np.random.RandomState(0).choice(len(X),k,replace=False)]
    for _ in range(it):
        lab=cap_assign(X,C,cap)
        Cn=np.array([np.median(X[lab==j],0) if (lab==j).any() else C[j] for j in range(len(C))])
        if np.allclose(Cn,C): break
        C=Cn
    return cap_assign(X,C,cap),C
