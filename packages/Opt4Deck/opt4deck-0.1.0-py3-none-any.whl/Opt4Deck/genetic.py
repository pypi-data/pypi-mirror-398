import random
import time
from datetime import date

def number(num,Max_iter):
    num = ['0' for i in range(0,len(str(Max_iter))-len(str(num)))]+list(str(num))
    return ''.join(num)

def record(num,opt,gen_dec,gen_bin,value):
    with open('./steps.txt','a+') as f:
        f.write('# generation-%s: %.5f\n'%(num,opt))
        for i in range(0,len(gen_dec)):
            for j in range(0,len(gen_dec[i])):
                f.write('   %.5f   '%(gen_dec[i][j]))
            for j in range(0,len(gen_bin[i])):
                f.write('   %s   '%(gen_bin[i][j]))
            f.write('   %.5f\n'%(value[i]))

def ran():
    return round(random.random(),5)

def dec2bin(dec_val,lower,upper,decim):
    bits = 0
    while (upper-lower)*(10.0**decim)-2.0**bits+1.0>0.0:
        bits = bits+1
    binary = bin(int((dec_val-lower)*(2.0**bits-1.0)/(upper-lower)))[2:]
    while len(binary)<bits:
        binary = '0'+binary
    return str(binary)

def bin2dec(bin_val,lower,upper,decim):
    bits = 0
    while (upper-lower)*(10.0**decim)-2.0**bits+1.0>0.0:
        bits = bits+1
    dec = float(lower+int(bin_val,2)*(upper-lower)/(2.0**bits-1.0))
    return round(dec,decim)

def cross_over(genetype1,genetype2,p_mut):
    genesize1,genesize2 = [len(genetype1[i]) for i in range(0,len(genetype1))],[len(genetype2[i]) for i in range(0,len(genetype2))]
    chromoso1,chromoso2 = ''.join(genetype1),''.join(genetype2)
    chromoso1,chromoso2 = [chromoso1[i] for i in range(0,len(chromoso1))],[chromoso2[i] for i in range(0,len(chromoso2))]
    rand = ran()
    dp = 1.0/(len(chromoso1)-1)
    pro = [(round(n*dp,3),round((n+1)*dp-0.0,3)) for n in range(0,len(chromoso1)-1)]
    crpo = random.randint(1,len(chromoso1)-1)
    for i in range(0,len(pro)):
        if rand>=pro[i][0] and rand<pro[i][1]:
            crpo = i+1
            break
    chromoso_1,chromoso_2 = chromoso1[0:crpo]+chromoso2[crpo:],chromoso2[0:crpo]+chromoso1[crpo:]
    chromoso_1,chromoso_2 = mutation(chromoso_1,p_mut),mutation(chromoso_2,p_mut)
    genetype1,genetype2 = [],[]
    for spl in genesize1:
        genetype1.append(''.join(chromoso_1[0:spl]))
        del chromoso_1[0:spl]
    for spl in genesize2:
        genetype2.append(''.join(chromoso_2[0:spl]))
        del chromoso_2[0:spl]
    return genetype1,genetype2

def mutation(chromoso,p_mut):
    rand = [ran() for i in range(0,len(chromoso))]
    for i in range(0,len(rand)):
        if rand[i]<p_mut: chromoso[i] = '1' if chromoso[i]=='0' else '0'
    return chromoso

def similarity(GenPopul,gen_bin):
    for i in range(0,len(GenPopul)):
        if GenPopul[i]['gen_bin']==gen_bin:
            return True
    return False

def bounds(Bound,gen_dec):
    check = [True if gen_dec[i]>=Bound[i][0] and gen_dec[i]<=Bound[i][1] else False for i in range(0,len(Bound))]
    return all(check)

def evaluation(GenPopul):
    Sum = sum([GenPopul[i]['value'] for i in range(0,len(GenPopul))])
    pro = [GenPopul[i]['value']/Sum for i in range(0,len(GenPopul))]
    cumul = 0.0
    for i in range(0,len(GenPopul)):
        start = cumul
        cumul = cumul+GenPopul[i]['value']/Sum
        GenPopul[i]['eval'] = (start,cumul)
    opt = 0.0
    for i in range(0,len(GenPopul)):
        if GenPopul[i]['value']>opt:
            opt = GenPopul[i]['value']
            sol_dec = GenPopul[i]['gen_dec']
            sol_bin = GenPopul[i]['gen_bin']
    return GenPopul,opt,sol_dec,sol_bin

def genetic(Fun,Argume,Bound,Decimal,P_mut,Max_iter,Max_pop):
    # create Adam & Eva
    gen_bin1,gen_bin2 = [],[]
    for i in range(0,len(Bound)):
        gen1,gen2 = [],[]
        while (Bound[i][1]-Bound[i][0])*(10.0**Decimal)-2.0**len(gen1)+1.0>0.0:
            rand = ran()
            if rand<0.50:
                gen1.append('0')
                gen2.append('1')
            else:
                gen1.append('1')
                gen2.append('0')
        gen_bin1.append(''.join(gen1))
        gen_bin2.append(''.join(gen2))
    gen_dec1 = [bin2dec(gen_bin1[i],Bound[i][0],Bound[i][1],Decimal) for i in range(0,len(Bound))]
    gen_dec2 = [bin2dec(gen_bin2[i],Bound[i][0],Bound[i][1],Decimal) for i in range(0,len(Bound))]
    value1 = Fun(gen_dec1,Argume)
    value2 = Fun(gen_dec2,Argume)
    GenPopul = [{'gen_dec':gen_dec1,'gen_bin':gen_bin1,'value':value1},{'gen_dec':gen_dec2,'gen_bin':gen_bin2,'value':value2}]
    GenPopul,opt,sol_dec,sol_bin = evaluation(GenPopul)
    record(number(0,Max_iter),opt,[gen_dec1,gen_dec2],[gen_bin1,gen_bin2],[value1,value2])
    # next generation
    for num in range(1,Max_iter):
        # select genetype-1
        rand,selected = ran(),None
        for i in range(0,len(GenPopul)):
            if rand>=GenPopul[i]['eval'][0] and rand<GenPopul[i]['eval'][1]: selected = GenPopul[i]['gen_bin']
        if selected is None:
            print("👉 The first genetype isn't selected!")
            selected = GenPopul[-1]['gen_bin']
        genetype1 = selected
        # select genetype-2
        check,count = True,0
        while check==True and count<100:
            rand,selected = ran(),None
            for i in range(0,len(GenPopul)):
                if rand>=GenPopul[i]['eval'][0] and rand<GenPopul[i]['eval'][1]: selected = GenPopul[i]['gen_bin']
            if selected is None:
                print("👉 The first genetype isn't selected!")
                selected = GenPopul[-1]['gen_bin']
            genetype2 = selected
            check = True if genetype1==genetype2 else False
            count = count+1
        if check==True:
            print('👉 Same genotypes selected!')
            genetype2 = genetype1
        gen_bin1,gen_bin2 = cross_over(genetype1,genetype2,P_mut)
        Gen_dec,Gen_bin,Value = [],[],[]
        for gen_bin in [gen_bin1,gen_bin2]:
            check = similarity(GenPopul,gen_bin)
            if check==False:
                gen_dec = [round(bin2dec(gen_bin[i],Bound[i][0],Bound[i][1],Decimal),5) for i in range(0,len(Bound))]
                if bounds(Bound,gen_dec)==True:
                    value = Fun(gen_dec,Argume)
                    GenPopul.append({'gen_dec':gen_dec,'gen_bin':gen_bin,'value':value})
                    Gen_dec.append(gen_dec)
                    Gen_bin.append(gen_bin)
                    Value.append(value)
        if Max_pop is not None and len(GenPopul)>Max_pop:
            GenPopul = sorted(GenPopul, key=lambda ind: ind['value'], reverse=True)[:Max_pop]
        GenPopul,opt,sol_dec,sol_bin = evaluation(GenPopul)
        record(number(num,Max_iter),opt,Gen_dec,Gen_bin,Value)
    return opt,sol_dec

def main(Fun,Argume,Bound,Decimal,P_mut=0.025,Max_iter=1000,Max_pop=100):
    with open('./steps.txt','w') as f:
        f.write('#####################################\n')
        f.write('# Giannis Serafeim       %s #\n'%(date.today()))
        f.write('# PhD Mechanical Engineering - NTUA #\n')
        f.write('# Genetic method  ----  version-0.1 #\n')
        f.write('#####################################\n')
        f.write('#')
        for i in range(0,len(Bound)):
            f.write('   val-%s    '%(number(i,Max_iter)))
        for i in range(0,len(Bound)):
            f.write('   bin-%s    '%(number(i,Max_iter)))
        f.write('evaluation\n')
    random.seed(time.time())
    Opt,Val = genetic(Fun,Argume,Bound,Decimal,P_mut,Max_iter,Max_pop)
    with open('./steps.txt','a+') as f:
        f.write('#####################################\n')
        for i in range(0,len(Val)):
            f.write('val-%s: %.5f\n'%(number(i,Max_iter),Val[i]))
        f.write('-------------\nOptimum: %.5f'%(Opt))
    print('GBO: GENETIC 👍')
    print('---------------')
    for i in range(0,len(Val)):
        print('val-%s: %.5f'%(number(i,Max_iter),Val[i]))
    print('Optimum: %.5f'%(Opt))
    return Opt,[Val[i] for i in range(0,len(Val))]

if __name__=='__main__':
    print('This file is the module of GA method, not executed as the main program! 😢')
