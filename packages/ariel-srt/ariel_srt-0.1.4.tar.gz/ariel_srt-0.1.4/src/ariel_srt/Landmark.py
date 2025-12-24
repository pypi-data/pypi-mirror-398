import numpy as np
import math


def normalization_spatial(spatial):
    spatial1=np.zeros(spatial.shape)
    maxx=np.max(spatial[:,0])
    minx=np.min(spatial[:,0])
    maxy=np.max(spatial[:,1])
    miny=np.min(spatial[:,1])

    x=(spatial[:,0]-minx)/(maxx-minx)
    y=(spatial[:,1]-miny)/(maxy-miny)
    spatial1[:,0]=x
    spatial1[:,1]=y
    return spatial1


def Rasterization(spatial, embedding,nx=40,ny=40):
    x=spatial[:,0]
    y=spatial[:,1]
    minx=np.min(x)
    maxx=np.max(x)
    miny=np.min(y)
    maxy=np.max(y)

    dx=(maxx-minx)/nx
    dy=(maxy-miny)/ny
    spatial_return=np.zeros([1,2])
    gene_return=np.zeros([1,embedding.shape[1]])
    
    for i in range(nx):
        for j in range(ny):
            xmi=minx+i*dx
            xma=minx+(i+1)*dx
            
            ymi=miny+j*dy
            yma=miny+(j+1)*dy
            
            xarray=np.where((x>=xmi) & (x<xma))[0]
            yarray=np.where((y>=ymi) & (y<yma))[0]
            
            gene1=np.zeros([1,embedding.shape[1]])
            spatial1=np.zeros([1,2])
            if(xarray.shape[0]!=0 and yarray.shape[0]!=0):
                for m in xarray:
                    if(m in yarray):
                        gene1=np.vstack((gene1,embedding[m,:]))
                        spatial1=np.vstack((spatial1,spatial[m,:]))
            if(gene1.shape[0]>1):
                gene1=np.delete(gene1, 0, 0)
                gene1=np.mean(gene1,axis=0)
                spatial1=np.delete(spatial1, 0, 0)
                spatial1=np.mean(spatial1,axis=0)
                spatial_return=np.vstack((spatial_return,spatial1))
                gene_return=np.vstack((gene_return,gene1))
    spatial_return=np.delete(spatial_return, 0, 0)
    gene_return=np.delete(gene_return, 0, 0)
    
    return spatial_return, gene_return


def alternative_landmark(spatial1, spatial2, embedding1, embedding2, n = 'Default', replace1 = False, replace2 = False):
    cor=np.corrcoef(embedding1,embedding2)[range(0,embedding1.shape[0]),:][:,range(embedding1.shape[0],embedding1.shape[0]+embedding2.shape[0])]
    cell1=[]
    cell2=[]
    D=cor.copy()
    if(n == 'Default'):
        n = math.floor(np.min(D.shape)/4)
    if(replace1):
        if(replace2):
            print("\033[31m'replace1' and 'replace2' cannot both be True at the same time.\033[0m")
        else:
            for i in range(n):
                cloc=np.where(D==np.max(cor))
                cell1.append(cloc[0][0])
                cell2.append(cloc[1][0])
                dloc=np.where(cor==np.max(cor))
                cor=np.delete(cor, dloc[1][0], axis=1)
            lm1=spatial1[cell1,:]
            lm2=spatial2[cell2,:]
            return lm1, lm2
    else:
        if(replace2):
            for i in range(n):
                cloc=np.where(D==np.max(cor))
                cell1.append(cloc[0][0])
                cell2.append(cloc[1][0])
                dloc=np.where(cor==np.max(cor))
                cor=np.delete(cor, dloc[0][0], axis=0)
            lm1=spatial1[cell1,:]
            lm2=spatial2[cell2,:]
            return lm1, lm2
        else:
            for i in range(n):
                cloc=np.where(D==np.max(cor))
                cell1.append(cloc[0][0])
                cell2.append(cloc[1][0])
                dloc=np.where(cor==np.max(cor))
                cor=np.delete(cor, dloc[0][0], axis=0)
                cor=np.delete(cor, dloc[1][0], axis=1)
            lm1=spatial1[cell1,:]
            lm2=spatial2[cell2,:]
            return lm1, lm2



def screen_landmark(lm1, lm2, n = 10):
    for i in range(lm2.shape[0]-n):
        one=np.ones(lm2.shape[0])
        lm2_1=np.insert(lm2,2,one,axis=1)
        M=np.dot(np.dot(np.linalg.inv(np.dot(lm2_1.T,lm2_1)),lm2_1.T),lm1)
        lm2_tran=np.dot(lm2_1,M)
        d=np.sum(np.power(lm2_tran-lm1,2),axis=1)
        lm2=np.delete(lm2, np.argmax(d), axis=0)
        lm1=np.delete(lm1, np.argmax(d), axis=0)

    return lm1, lm2

