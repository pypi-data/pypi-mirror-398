from datetime import date

def record(num,Fmat,Amat,Bmat,Cmat,Dmat,Emat):
    with open('./steps.txt','a+') as f:
        f.write('##################\n#   Tableau-%s   #\n##################\n            '%(num))
        for i in range(0,len(Fmat)):
            f.write('%s    '%(Fmat[i]['var']))
        f.write('\nBasis  Cj   ')
        for i in range(0,len(Fmat)):
            f.write('%.2f   '%(Fmat[i]['val']))
        f.write('  b    ratio\n')
        for i in range(0,len(Amat)):
            f.write(' %s  %.2f  '%(Bmat[i]['var'],Bmat[i]['val']))
            for j in range(0,len(Amat[i])):
                f.write('%.2f   '%(Amat[i][j]))
            f.write('%.2f   %.1f\n'%(Bmat[i]['con'],Bmat[i]['rat']))
        f.write('       Zj   ')
        for i in range(0,len(Cmat)):
            f.write('%.2f   '%(Cmat[i]))
        f.write('%.2f\n'%(Emat))
        f.write('     Cj-Zj  ')
        for i in range(0,len(Dmat)):
            f.write('%.2f   '%(Dmat[i]))
        f.write('\n')

def simplex(Aug,Z_err,Max_iter):
    Nx = len(Aug[0])-len(Aug)
    Ns = len(Aug)-1
    Fmat  = [{'var':'X%s'%(str(j).zfill(2)),'val':Aug[0][j]} for j in range(0,Nx)]+[{'var':'S%s'%(str(j).zfill(2)),'val':Aug[0][Nx+j]} for j in range(0,Ns)]
    Vopt  = [{'var':'X%s'%(str(j).zfill(2)),'val':0.0} for j in range(0,Nx)]+[{'var':'S%s'%(str(j).zfill(2)),'val':0.0} for j in range(0,Ns)]
    Amat  = [[Aug[i+1][j] for j in range(0,Nx+Ns)] for i in range(0,Ns)]
    Bmat  = [{'var':'S%s'%(str(j).zfill(2)),'val':0.0,'con':Aug[j+1][Nx+Ns],'rat':0.0} for j in range(0,Ns)]
    Cmat  = [sum([Amat[i][j]*Bmat[i]['val'] for i in range(0,Ns)]) for j in range(0,Nx+Ns)]
    Dmat  = [Fmat[j]['val']-Cmat[j] for j in range(0,Nx+Ns)]
    Emat  = sum([Bmat[i]['con']*Bmat[i]['val'] for i in range(0,Ns)])
    check = [Dmat[j]>Z_err for j in range(0,Nx+Ns)]
    count = 0
    while any(check)==True:
        col  = Dmat.index(max(Dmat))
        for i in range(0,Ns):
            aij = Amat[i][col]
            if aij>Z_err:
                Bmat[i]['rat'] = Bmat[i]['con']/aij
            else:
                Bmat[i]['rat'] = float('inf')
        record(str(count).zfill(2),Fmat,Amat,Bmat,Cmat,Dmat,Emat)
        if all(b['rat'] == float('inf') for b in Bmat):
            raise Exception('👉 Problem is unbounded!')
        rat = [Bmat[i]['rat'] for i in range(0,Ns)]
        min_rat = min(rat)
        row = rat.index(min_rat)
        vrc = Amat[row][col]
        if vrc<=Z_err:
            raise Exception('👉 Zero encountered!')
        Bmat[row]['var'] = Fmat[col]['var']
        Bmat[row]['val'] = Fmat[col]['val']
        Bmat[row]['con'] = Bmat[row]['con']/vrc
        for j in range(0,Nx+Ns):
            Amat[row][j] = Amat[row][j]/vrc
        for i in range(0,Ns):
            if i!=row:
                coef = Amat[i][col]
                Bmat[i]['con'] = Bmat[i]['con']-coef*Bmat[row]['con']
                for j in range(0,Nx+Ns):
                    Amat[i][j] = Amat[i][j]-coef*Amat[row][j]
        Cmat = [sum([Amat[i][j]*Bmat[i]['val'] for i in range(0,Ns)]) for j in range(0,Nx+Ns)]
        Dmat = [Fmat[j]['val']-Cmat[j] for j in range(0,Nx+Ns)]
        Emat = sum([Bmat[i]['con']*Bmat[i]['val'] for i in range(0,Ns)])
        check = [True if Dmat[j]>Z_err else False for j in range(0,Nx+Ns)]
        count = count+1
        if count>Max_iter:
            raise Exception('👉 Max iterations exceeded!')
    record(str(count).zfill(2),Fmat,Amat,Bmat,Cmat,Dmat,Emat)
    for i in range(0,Nx+Ns):
        for j in range(0,Ns):
            if Vopt[i]['var']==Bmat[j]['var']: Vopt[i]['val'] = Bmat[j]['con']
    return Emat,Vopt

def main(Aug,Z_err=0.00001,Max_iter=100):
    with open('./steps.txt','w') as f:
        f.write('#####################################\n')
        f.write('# Giannis Serafeim       %s #\n'%(date.today()))
        f.write('# PhD Mechanical Engineering - NTUA #\n')
        f.write('# Simplex method  ----  version-0.1 #\n')
        f.write('#####################################\n')
    Opt,Val = simplex(Aug,Z_err,Max_iter)
    with open('./steps.txt','a+') as f:
        f.write('#####################################\n')
        for i in range(0,len(Val)):
            f.write('%s: %.2f\n'%(Val[i]['var'],Val[i]['val']))
        f.write('-------------\nOptimum: %.2f'%(Opt))
    print('Opt4Deck: SIMPLEX 👍')
    print('---------------')
    for i in range(0,len(Val)):
        print('%s: %.2f'%(Val[i]['var'],Val[i]['val']))
    print('Optimum: %.2f'%(Opt))
    return Opt,[Val[i]['val'] for i in range(0,len(Val))]

if __name__=='__main__':
    print('This file is the module of SIMPLEX method, not executed as the main program! 😢')
