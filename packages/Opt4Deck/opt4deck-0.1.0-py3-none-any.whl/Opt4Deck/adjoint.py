import math
import numpy as np
from datetime import date
from numpy.linalg import inv

def number(num):
    return str(int(num)).zfill(2)

def record(num,OptVal,Fun,Jmat,alpha):
    with open('./steps.txt','a+') as f:
        f.write('  %d    '%(num))
        for i in range(0,len(OptVal)):
            f.write('%.5f   '%(OptVal[i]))
        f.write('[')
        for i in range(0,len(Jmat)):
            f.write('%.5f, '%(Jmat[i][0]))
        f.write(']   %.5f   %.5f\n'%(alpha,Fun))

def faim(x_mat,x_aim,time):
    return sum([(sum([(x_mat[i-1][j][0]-x_aim[i-1][j][0])**2.0 for j in range(0,len(x_aim[i-1]))])+sum([(x_mat[i][j][0]-x_aim[i][j][0])**2.0 for j in range(0,len(x_aim[i]))]))*(time[i]-time[i-1])/2.0 for i in range(1,len(time))])/2.0

def solveRK4(Amat,Bmat,Fmat,time,x_ini):
    f = lambda Ainv,Bmat,Fmat,x_mat: np.matmul(Ainv,Fmat-np.matmul(Bmat,x_mat))
    if x_ini[0]==True: Fmat,time = [Fmat[i] for i in range(len(Fmat)-1,-1,-1)],[time[i] for i in range(len(time)-1,-1,-1)]
    Ainv,x_mat = inv(Amat),[x_ini[1],]
    for i in range(1,len(time)):
        dt = time[i]-time[i-1]
        k1 = f(Ainv,Bmat,Fmat[i-1],x_mat[i-1])
        k2 = f(Ainv,Bmat,(Fmat[i-1]+Fmat[i])/2.0,x_mat[i-1]+dt*k1/2.0)
        k3 = f(Ainv,Bmat,(Fmat[i-1]+Fmat[i])/2.0,x_mat[i-1]+dt*k2/2.0)
        k4 = f(Ainv,Bmat,Fmat[i],x_mat[i-1]+dt*k3)
        x_mat.append(x_mat[i-1]+dt*(k1+2.0*k2+2.0*k3+k4)/6.0)
    if x_ini[0]==True: x_mat = [x_mat[i] for i in range(len(x_mat)-1,-1,-1)]
    return x_mat

def gran(Amat,Bmat,Fmat,OptVal,Bound):
    delta = [(Bound[i][2]-Bound[i][1])/1000.0 for i in range(0,len(Bound))]
    dA = [(Amat([OptVal[j]+delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))])-Amat([OptVal[j]-delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))]))/(2.0*delta[i]) for i in range(0,len(OptVal))]
    dB = [(Bmat([OptVal[j]+delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))])-Bmat([OptVal[j]-delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))]))/(2.0*delta[i]) for i in range(0,len(OptVal))]
    dF = [[(Fmat([OptVal[j]+delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))])[k]-Fmat([OptVal[j]-delta[i] if j==i else OptVal[j] for j in range(0,len(OptVal))])[k])/(2.0*delta[i]) for k in range(0,len(Fmat(OptVal)))] for i in range(0,len(OptVal))]
    return dA,dB,dF

def jaco(Amat,Bmat,Fmat,time,x_mat,x_aim,OptVal,Bound):
    Bcoef = [min([1.0-math.exp(-(OptVal[i]-Bound[i][1])**2.0),1.0-math.exp(-(OptVal[i]-Bound[i][2])**2.0)]) if Bound[i][0]==True else 1.0 for i in range(0,len(Bound))]
    dx = [(x_mat[1]-x_mat[0])/(time[1]-time[0]),]+[(x_mat[i+1]-x_mat[i-1])/(time[i+1]-time[i-1]) for i in range(1,len(x_mat)-1)]+[(x_mat[len(x_mat)-1]-x_mat[len(x_mat)-2])/(time[len(x_mat)-1]-time[len(x_mat)-2]),]
    Psi = solveRK4(Amat(OptVal),-Bmat(OptVal),[x_mat[i]-x_aim[i] for i in range(0,len(x_aim))],time,(True,np.array([[0.0,] for i in range(0,len(x_aim[0]))])))
    dA,dB,dF = gran(Amat,Bmat,Fmat,OptVal,Bound)
    Jmat = []
    for i in range(0,len(OptVal)):
        y = [np.matmul(Psi[j].transpose(),np.matmul(dA[i],dx[j])+np.matmul(dB[i],x_mat[j])-dF[i][j])[0][0] for j in range(0,len(Psi))]
        Jmat.append([Bcoef[i]*sum([(y[j-1]+y[j])*(time[j]-time[j-1])/2.0 for j in range(1,len(time))]),])
    return np.array(Jmat)

def adjoint(Amat,Bmat,Fmat,time,x_ini,x_aim,OptVal,Bound,Conver,Max_iter):
    num = 0
    x_mat = solveRK4(Amat(OptVal),Bmat(OptVal),Fmat(OptVal),time,x_ini)
    Fcur = faim(x_mat,x_aim,time)
    Jmat = jaco(Amat,Bmat,Fmat,time,x_mat,x_aim,OptVal,Bound)
    alpha = next((a for a in [10000000.0,1000000.0,100000.0,10000.0,1000.0,100.0,10.0,5.0,1.0,0.5,0.1,0.01,0.001,0.0001,0.00001,0.0000001,0.00000001] if faim(solveRK4(Amat([OptVal[i]-a*Jmat[i][0] for i in range(len(OptVal))]),Bmat([OptVal[i]-a*Jmat[i][0] for i in range(len(OptVal))]),Fmat([OptVal[i]-a*Jmat[i][0] for i in range(len(OptVal))]),time,x_ini),x_aim,time)<Fcur),1.0) #0.1
    record(num,OptVal,Fcur,Jmat,alpha)
    check = True
    while check==True and num<Max_iter:
        num = num+1
        p_mat = [alpha*Jmat[i][0] if abs(alpha*Jmat[i][0])<(Bound[i][2]-Bound[i][1])/10.0 else (Bound[i][2]-Bound[i][1])*Jmat[i][0]/(10.0*(abs(Jmat[i][0])+1e-12)) for i in range(len(Jmat))]
        p_mat = [np.clip(p_mat[i],-(Bound[i][2]-Bound[i][1])/4.0,(Bound[i][2]-Bound[i][1])/4.0) for i in range(0,len(p_mat))]
        OptVal_new = [2.0*Bound[i][2]-(OptVal[i]-p_mat[i]) if (OptVal[i]-p_mat[i])>Bound[i][2] and Bound[i][0]==True else 2.0*Bound[i][1]-(OptVal[i]-p_mat[i]) if (OptVal[i]-p_mat[i])<Bound[i][1] and Bound[i][0]==True else OptVal[i]-p_mat[i] for i in range(0,len(OptVal))] # [max(min(OpVal[i]-p_mat[i],Ranges[i][2]),Ranges[i][1]) if Ranges[i][0]==True else OpVal[i]-p_mat[i] for i in range(0,len(OpVal))]
        x_mat = solveRK4(Amat(OptVal_new),Bmat(OptVal_new),Fmat(OptVal_new),time,x_ini)
        Fnew = faim(x_mat,x_aim,time)
        Jmat_new = jaco(Amat,Bmat,Fmat,time,x_mat,x_aim,OptVal_new,Bound)
        Smat,Ymat = np.array(OptVal_new)-np.array(OptVal),(Jmat_new-Jmat).flatten()
        denom1,denom2,denom3 = np.dot(Smat,Smat),np.dot(Ymat,Ymat),np.dot(Smat,Ymat)
        if abs(denom3)<0.000000001:
            print('👉 Failure during Barzilai-Borwein: Division by zero!')
            alpha_new = alpha/2.0
        else:
            alpha_new = 0.5*denom1/denom3+0.5*denom3/denom2
        if alpha_new<=0:
            print('👉 Failure during Barzilai-Borwein: Negative alpha!')
            alpha_new = alpha/2.0
        alpha = alpha_new
        record(num,OptVal_new,Fnew,Jmat_new,alpha)
        if abs(Fcur-Fnew)<Conver:
            check = False
        else:
            OptVal = [OptVal_new[i] for i in range(0,len(OptVal_new))]
            Fcur   = Fnew
            Jmat   = [[Jmat_new[i][j] for j in range(0,len(Jmat_new[i]))] for i in range(0,len(Jmat_new))]
    with open('./distr.txt','w') as f:
        f.write('#time[s]   ')
        for i in range(0,len(x_ini[1])):
            f.write('x_fit-%s   x_aim-%s   '%(number(i),number(i)))
        f.write('\n')
        for i in range(0,len(time)):
            f.write('%.5f'%(time[i]))
            for j in range(0,len(x_ini[1])):
                f.write('   %.5f   %.5f'%(x_mat[i][j].flatten(),x_aim[i][j].flatten()))
            f.write('\n')
    return Fnew,OptVal_new

def main(Amat,Bmat,Fmat,x_ini,x_aim,OptVal,Bound,Conver=0.001,Max_iter=100):
    with open('./steps.txt','w') as f:
        f.write('#####################################\n')
        f.write('# Giannis Serafeim       %s #\n'%(date.today()))
        f.write('# PhD Mechanical Engineering - NTUA #\n')
        f.write('# ADJOINT method  ----  version-0.1 #\n')
        f.write('#####################################\n')
        f.write('#num   ')
        for i in range(0,len(OptVal)):
            f.write('val-%s    '%(number(i)))
        f.write('Jacobian   alpha   Error\n')
    Err,Val = adjoint(Amat,Bmat,Fmat,[x_aim[i][0] for i in range(0,len(x_aim))],x_ini,[x_aim[i][1] for i in range(0,len(x_aim))],OptVal,Bound,Conver,Max_iter)
    with open('./steps.txt','a+') as f:
        f.write('#####################################\n')
        for i in range(0,len(Val)):
            f.write('val-%s: %.5f\n'%(number(i),Val[i]))
        f.write('-------------\nError: %.5f'%(Err))
    print('Opt4Deck: ADJOINT 👍')
    print('---------------')
    for i in range(0,len(Val)):
        print('val-%s: %.5f'%(number(i),Val[i]))
    print('Error: %.5f'%(Err))
    return Err,[Val[i] for i in range(0,len(Val))]

if __name__=='__main__':
    print('This file is the module of ADJOINT method, not executed as the main program! 😢')
