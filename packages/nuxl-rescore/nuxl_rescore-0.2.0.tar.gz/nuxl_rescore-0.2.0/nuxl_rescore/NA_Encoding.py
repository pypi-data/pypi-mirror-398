import pandas as pd
import numpy as np 

RNA = {
    "A": "C10|H14|N5|O7|P1|S0", 
    "C": "C9|H14|N3|O8|P1|S0",
    "G": "C10|H14|N5|O8|P1|S0",
    "U": "C9|H13|N2|O9|P1|S0",
    "S": "C9|H13|N2|O8|P1|S1",
    "X": "C10|H14|N5|O7|P1|S1"
}

DNA = {
    "A": "C10|H14|N5|O6|P1|S0",
    "C": "C9|H14|N3|O7|P1|S0", 
    "G": "C10|H14|N5|O7|P1|S0", 
    "T": "C10|H15|N2|O8|P1|S0", 
    "d": "C5|H9|N0|O6|P1|S0"
    }

def mod_manipulation(RNA_seq = ''):
    Heading = ['Chem', 'C', 'Cn', 'H', 'Hn', 'N', 'Nn', 'O', 'On', 'P', 'Pn', 'S', 'Sn']
    C = H = N = O = P = S = 0
    temp_chem = ' '
    sign = '+'
    last_int = False
    for i in range(len(RNA_seq)):
        x = RNA_seq[i]
        #print(x, last_int, sign)
        if (x.isalpha()):
            last_int = False
            temp_chem = x
        elif (x == '-'):
            sign = '-'
        elif (x == '+'):
            sign = '+'
        else:
            if (temp_chem == 'C'):
                if (sign == '-'):
                    if (last_int == False):
                        C -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        C = C + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        C -= value
                else:
                    if (last_int == False):
                        C += int(x)
                        last_int = True
                    else:
                        last_int = False
                        C = C - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        C += value
        
            if (temp_chem == 'H'):
                if (sign == '-'):
                    if (last_int == False):
                        H -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        H = H + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        H -= value
                else:
                    if (last_int == False):
                        H += int(x)
                        last_int = True
                    else:
                        last_int = False
                        H = H - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        H += value

                #print('H', H)
            if (temp_chem == 'N'):
                if (sign == '-'):
                    if (last_int == False):
                        N -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        N = N + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        N -= value
                else:
                    if (last_int == False):
                        N += int(x)
                    else:
                        last_int = False
                        N = N - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        N += value

            if (temp_chem == 'O'):
                if (sign == '-'):
                    if (last_int == False):
                        O -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        O = O + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        O -= value
                else:
                    if (last_int == False):
                        O += int(x)
                        last_int = True
                    else:
                        last_int = False
                        O = O - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        O += value

            if (temp_chem == 'P'):
                if (sign == '-'):
                    if (last_int == False):
                        P -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        P = P + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        P -= value
                else:
                    if (last_int == False):
                        P += int(x)
                        last_int = True
                    else:
                        last_int = False
                        P = P - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        P += value

            if (temp_chem == 'S'):
                if (sign == '-'):
                    if (last_int == False):
                        S -= int(x)
                        last_int = True
                    else:
                        last_int = False
                        S = S + int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        S -= value
                else:
                    if (last_int == False):
                        S += int(x)
                        last_int = True
                    else:
                        last_int = False
                        S = S - int(RNA_seq[(i-1)])
                        value = int(str(RNA_seq[(i-1)]) + str(RNA_seq[(i)]))
                        S += value
                        
    mod_last = []
    for i in Heading:
        if (i == 'Chem'):
            mod_last.append('mod')

        if (i == 'C'):
            mod_last.append('C')
        if (i == 'Cn'):
            mod_last.append(C)

        if (i == 'H'):
            mod_last.append('H')
        if (i == 'Hn'):
            mod_last.append(H)

        if (i == 'N'):
            mod_last.append('N')
        if (i == 'Nn'):
            mod_last.append(N)

        if (i == 'O'):
            mod_last.append('O')
        if (i == 'On'):
            mod_last.append(O)

        if (i == 'P'):
            mod_last.append('P')
        if (i == 'Pn'):
            mod_last.append(P)

        if (i == 'S'):
            mod_last.append('S')
        if (i == 'Sn'):
            mod_last.append(S)

    return mod_last
             


def seq_encoding(rRNA, DNA_ = False):
    """
      generate atomic composition of different XL modifications
    """
    Encoding = []
    Heading = ['Chem', 'C', 'Cn', 'H', 'Hn', 'N', 'Nn', 'O', 'On', 'P', 'Pn', 'S', 'Sn']
  
    #print(rRNA)
    RNA_p = ''
    find_sign = '*'
    for i in rRNA:
        if(i == '+'):
            RNA_p = rRNA.split('+')
            NA_ = RNA_p[0]
            mod = RNA_p[1]
            find_sign = '+'
            break
        elif(i == '-'):
            RNA_p_s = rRNA.split('-')
            RNA_p = ''
            for i in range(len(RNA_p_s)):
                if (i>0):
                    RNA_p =RNA_p + ('-'+RNA_p_s[i])
            NA_ = RNA_p_s[0] 
            mod = RNA_p
            find_sign = '-'
            break
    
    if (find_sign == '*'):
        NA_ = rRNA
        mod = ''

    #print(Encoding, RNA_p, NA_)
    #print(rRNA, find_sign, NA_, mod)

    if ((DNA_ == True) & (NA_ != 'none')):
        for NA in NA_:
            z = DNA[NA].split('|')
            this_R = []
            if(NA == 'A'):
                    this_R.append('A_D')
            elif(NA == 'G'):
                    this_R.append('G_D')
            elif(NA == 'C'):
                    this_R.append('C_D')
            elif(NA == 'T'):
                    this_R.append('T_D')
            elif(NA == 'd'):
                    this_R.append('d_D')
            for i in range(len(z)):
                        x = z[i]
                        if len(x) == 2:
                            this_R.append(x[0])
                            this_R.append(int(x[1]))
                        if len(x) == 3:
                            this_R.append(x[0])
                            this_R.append(int(x[1:])) 

            Encoding.append(this_R)
        
    elif ((NA_ != 'none')):
        for NA in NA_:
            z = RNA[NA].split('|')
            this_R = []
            if(NA == 'C'):
                    this_R.append('C_R')
            elif(NA == 'G'):
                    this_R.append('G_R')
            elif(NA == 'A'):
                    this_R.append('A_R')
            elif(NA == 'U'):
                    this_R.append('U_R')
            elif(NA == 'S'):
                    this_R.append('S_R')
            elif(NA == 'X'):
                    this_R.append('X_R')
            for i in range(len(z)):
                        x = z[i]
                        if len(x) == 2:
                            #print(x)
                            this_R.append(x[0])
                            this_R.append(int(x[1]))
                        if len(x) == 3:
                            #print(x)
                            this_R.append(x[0])
                            this_R.append(int(x[1:])) 

            Encoding.append(this_R)

    if (mod != ''):
        mod_last = mod_manipulation(mod)

        #print(mod_last)
        last_element = Encoding[len(Encoding)-1]
        #print(last_element)

        NA_mod = [str(last_element[0]) + '_' +str(mod_last[0])]
        for i in range(len(Heading)-1):
            i=i+1
            if(str(last_element[i]).isalpha()):
                NA_mod.append(last_element[i])
            else:
                NA_mod.append(last_element[i] + mod_last[i])
        #print(NA_mod)
        
        Encoding.pop()
        Encoding.append(NA_mod)

    C = H = N = O = P = S = 0
    for i in Encoding:
        for j in range(len(i)):
            if (i[j] == 'C'):
                C = C +  i[j+1]
            if (i[j] == 'H'):
                H = H +  i[j+1]
            if (i[j] == 'N'):
                N = N +  i[j+1]
            if (i[j] == 'O'):
                O = O +  i[j+1]
            if (i[j] == 'P'):
                P = P +  i[j+1]
            if (i[j] == 'S'):
                S = S +  i[j+1] 

    chem_form = ''
    Mod_name = ''
    if (C != 0):
        chem_form = chem_form + 'C(' + str(C) + ')'
    if (H != 0):
        chem_form = chem_form + 'H(' + str(H) + ')'
    if (N != 0):
        chem_form = chem_form + 'N(' + str(N) + ')'
    if (O != 0):
        chem_form = chem_form + 'O(' + str(O) + ')'
    if (P != 0):
        chem_form = chem_form + 'P(' + str(P) + ')'
    if (S != 0):
        chem_form = chem_form + 'S(' + str(S) + ')'
        
    if (rRNA != 'none'):
        if(DNA_ == True):
                Mod_name = str(rRNA) + '@DNA_XL'
        else:
                Mod_name = str(rRNA) + '@RNA_XL'   

    #print(Mod_name, chem_form)
    my_tuple = (Mod_name, chem_form)
    return my_tuple

def NA_Feature(rRNA, DNA_ = False, max_len=4):
    """
      generate atomic composition feature vector; could be help for any analysis (i-e alphapeptdeep)
    """
    Encoding = []
    Heading = ['Chem', 'C', 'Cn', 'H', 'Hn', 'N', 'Nn', 'O', 'On', 'P', 'Pn', 'S', 'Sn']
  
    #print(rRNA)
    RNA_p = ''
    find_sign = '*'
    for i in rRNA:
        if(i == '+'):
            RNA_p = rRNA.split('+')
            NA_ = RNA_p[0]
            mod = RNA_p[1]
            find_sign = '+'
            break
        elif(i == '-'):
            RNA_p_s = rRNA.split('-')
            RNA_p = ''
            for i in range(len(RNA_p_s)):
                if (i>0):
                    RNpA_p =RNA_p + ('-'+RNA_p_s[i])
            NA_ = RNA_p_s[0] 
            mod = RNA_p
            find_sign = '-'
            break
    
    if (find_sign == '*'):
        NA_ = rRNA
        mod = ''

    #print(Encoding, RNA_p, NA_)
    #print(rRNA, find_sign, NA_, mod)

    if ((DNA_ == True) & (NA_ != 'none')):
        for NA in NA_:
            z = DNA[NA].split('|')
            this_R = []
            if(NA == 'A'):
                    this_R.append('A_D')
            elif(NA == 'G'):
                    this_R.append('G_D')
            elif(NA == 'C'):
                    this_R.append('C_D')
            elif(NA == 'T'):
                    this_R.append('T_D')
            elif(NA == 'd'):
                    this_R.append('d_D')
            for i in range(len(z)):
                        x = z[i]
                        if len(x) == 2:
                            this_R.append(x[0])
                            this_R.append(int(x[1]))
                        if len(x) == 3:
                            this_R.append(x[0])
                            this_R.append(int(x[1:])) 

            Encoding.append(this_R)
        
    elif ((NA_ != 'none')):
        for NA in NA_:
            z = RNA[NA].split('|')
            this_R = []
            if(NA == 'C'):
                    this_R.append('C_R')
            elif(NA == 'G'):
                    this_R.append('G_R')
            elif(NA == 'A'):
                    this_R.append('A_R')
            elif(NA == 'U'):
                    this_R.append('U_R')
            elif(NA == 'S'):
                    this_R.append('S_R')
            elif(NA == 'X'):
                    this_R.append('X_R')
            for i in range(len(z)):
                        x = z[i]
                        if len(x) == 2:
                            #print(x)
                            this_R.append(x[0])
                            this_R.append(int(x[1]))
                        if len(x) == 3:
                            #print(x)
                            this_R.append(x[0])
                            this_R.append(int(x[1:])) 

            Encoding.append(this_R)

    if (mod != ''):
        mod_last = mod_manipulation(mod)

        #print(mod_last)
        last_element = Encoding[len(Encoding)-1]
        #print(last_element)

        NA_mod = [str(last_element[0]) + '_' +str(mod_last[0])]
        for i in range(len(Heading)-1):
            i=i+1
            if(str(last_element[i]).isalpha()):
                NA_mod.append(last_element[i])
            else:
                NA_mod.append(last_element[i] + mod_last[i])
        #print(NA_mod)
        
        Encoding.pop()
        Encoding.append(NA_mod)

    temp = ['Chem_t', 'C', 0, 'H', 0, 'N', 0, 'O', 0, 'P', 0, 'S', 0] 
    while(len(Encoding)<max_len):
        Encoding.append(temp)

    #print(Encoding)
    En = pd.DataFrame(Encoding, columns=Heading)
    feat = En[['Cn','Hn', 'Nn', 'On', 'Pn', 'Sn']]
    feat_vector = np.array(feat)

    return feat_vector
