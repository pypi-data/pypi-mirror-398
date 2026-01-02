import math
import numpy as np
from datetime import date
from numpy.linalg import inv

def number(num):
    return str(int(num)).zfill(2)

def record(num,OptVal,Fun,Jmat,Hmat):
    with open('./steps.txt','a+') as f:
        f.write('  %d    '%(num))
        for i in range(0,len(OptVal)):
            f.write('%.5f   '%(OptVal[i]))
        f.write('[')
        for i in range(0,len(Jmat)):
            f.write('%.5f, '%(Jmat[i][0]))
        f.write('] [')
        for i in range(0,len(Hmat)):
            f.write('[')
            for j in range(0,len(Hmat[i])):
                f.write('%.5f, '%(Hmat[i][j]))
            f.write('],')
        f.write(']   %.5f\n'%(Fun))

def jaco(Fun,OptVal,Argume,Bound):
    Bcoef = [min([1.0-math.exp(-(OptVal[i]-Bound[i][1])**2.0),1.0-math.exp(-(OptVal[i]-Bound[i][2])**2.0)]) if Bound[i][0]==True else 1.0 for i in range(0,len(Bound))]
    delta = [(Bound[i][2]-Bound[i][1])/1000.0 for i in range(0,len(Bound))]
    F0,Jmat = [],[]
    for i in range(0,len(OptVal)):
        F1 = Fun([OptVal[j]-delta[j] if i==j else OptVal[j] for j in range(0,len(OptVal))],Argume)
        F2 = Fun([OptVal[j]+delta[j] if i==j else OptVal[j] for j in range(0,len(OptVal))],Argume)
        F0.append((F1+F2)/2.0)
        Jmat.append([Bcoef[i]*(F2-F1)/(2.0*delta[i]),])
    return sum(F0)/len(F0),np.array(Jmat)

def jac_hes0(Fun,OptVal,Argume,Bound,F0):
    delta = [(Bound[i][2]-Bound[i][1])/1000.0 for i in range(0,len(Bound))]
    Jmat,Hmat = [],[]
    for i in range(0,len(OptVal)):
        F1 = Fun([OptVal[j]-delta[j] if i==j else OptVal[j] for j in range(0,len(OptVal))],Argume)
        F2 = Fun([OptVal[j]+delta[j] if i==j else OptVal[j] for j in range(0,len(OptVal))],Argume)
        Jmat .append([(F2-F1)/(2.0*delta[i]),])
        Hmat.append([(F2-2.0*F0+F1)/(delta[i]**2.0) if i==j else 0.0 for j in range(0,len(OptVal))])
    return np.array(Jmat),np.array(Hmat)

def hess(OptVal,Jmat,Hmat,OptVal_new,Jmat_new):
    try:
        Smat = [[OptVal_new[j]-OptVal[j],] for j in range(0,len(OptVal_new))]
        Ymat = [[Jmat_new[j][0]-Jmat[j][0],] for j in range(0,len(Jmat_new))]
        Hmat_new = Hmat-np.matmul(np.matmul(np.matmul(Hmat,Smat),np.transpose(Smat)),Hmat)/np.matmul(np.matmul(np.transpose(Smat),Hmat),Smat)[0][0]+np.matmul(Ymat,np.transpose(Ymat))/np.matmul(np.transpose(Ymat),Smat)[0][0]
    except ZeroDivisionError:
        print('👉 Hessian: Division by zero!')
        Hmat_new = np.identity(len(OptVal))
    except Exception as e:
        print('👉 Hessian: Failure at estimation!')
        Hmat_new = np.identity(len(OptVal))
    return np.array(Hmat_new)

def bfgs(Fun,OptVal,Argume,Bound,Conver,Max_iter):
    num = 0
    Fcur = Fun(OptVal,Argume)
    Jmat, Hmat = jac_hes0(Fun,OptVal,Argume,Bound,Fcur)
    record(num,OptVal,Fcur,Jmat,Hmat)
    check = True
    while check==True and num<Max_iter:
        num = num+1
        p_mat = np.matmul(inv(Hmat),Jmat)
        OptVal_new = [2.0*Bound[i][2]-(OptVal[i]-p_mat[i][0]) if OptVal[i]-p_mat[i][0]>Bound[i][2] and Bound[i][0]==True else 2.0*Bound[i][1]-(OptVal[i]-p_mat[i][0]) if OptVal[i]-p_mat[i][0]<Bound[i][1] and Bound[i][0]==True else OptVal[i]-p_mat[i][0] for i in range(0,len(OptVal))]
        Fnew,Jmat_new = jaco(Fun,OptVal_new,Argume,Bound)
        Hmat_new = hess(OptVal,Jmat,Hmat,OptVal_new,Jmat_new)
        record(num,OptVal_new,Fnew,Jmat_new,Hmat_new)
        if abs(Fcur-Fnew)<Conver:
            check = False
        else:
            OptVal = [OptVal_new[i] for i in range(0,len(OptVal_new))]
            Fcur  = Fnew
            Jmat  = [[Jmat_new[i][j] for j in range(0,len(Jmat_new[i]))] for i in range(0,len(Jmat_new))]
            Hmat  = [[Hmat_new[i][j] for j in range(0,len(Hmat_new[i]))] for i in range(0,len(Hmat_new))]
    return Fnew,OptVal_new

def main(Fun,OptVal,Argume,Bound,Conver=0.001,Max_iter=100):
    with open('./steps.txt','w') as f:
        f.write('#####################################\n')
        f.write('# Giannis Serafeim       %s #\n'%(date.today()))
        f.write('# PhD Mechanical Engineering - NTUA #\n')
        f.write('# BFGS method    ----   version-0.1 #\n')
        f.write('#####################################\n')
        f.write('#num   ')
        for i in range(0,len(OptVal)):
            f.write('val-%s    '%(number(i)))
        f.write('Jacobian    Hessian           evaluation\n')
    Opt,Val = bfgs(Fun,OptVal,Argume,Bound,Conver,Max_iter)
    with open('./steps.txt','a+') as f:
        f.write('#####################################\n')
        for i in range(0,len(Val)):
            f.write('val-%s: %.5f\n'%(number(i),Val[i]))
        f.write('-------------\nOptimum: %.5f'%(Opt))
    print('Opt4Deck: BFGS 👍')
    print('---------------')
    for i in range(0,len(Val)):
        print('val-%s: %.5f'%(number(i),Val[i]))
    print('Optimum: %.5f'%(Opt))
    return Opt,[Val[i] for i in range(0,len(Val))]

if __name__=='__main__':
    print('This file is the module of BFGS method, not executed as the main program! 😢')
