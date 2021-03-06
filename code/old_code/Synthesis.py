"""
- 10/13: modify expression level in coverage file so that:
         expression level per transcript corresponds to # of reads per transcript
"""

from Address import *
#import Bowtie
# import Rules

import os
import subprocess
import re
import time
import sys
from operator import itemgetter, attrgetter
import random
from numpy import array
import math
#from matplotlib import pyplot as plt
import numpy as np
import heapq

import datetime
import pdb
from debug_MACRO import *
from progress.bar import Bar

import csv

from util import *
import pdb

#pdb.set_trace()

#--------------------------------------------------------------------------------------------------------

def BED2ExpressionLevel(BED_address, exp_fn='/exp.txt'):
    #pdb.set_trace() #debug
    b=re.search('([\s\S]+)/([\S]+)\.([\S]+)', BED_address)
    BED_sorted_address = b.group(1) + '/' + b.group(2) + '-sorted.' + b.group(3)
    exp_address = b.group(1) + exp_fn
    # sort BED file
    subprocess.call( 'sort -k 1,1 -k 2,2n ' +  BED_address + ' > ' +  BED_sorted_address,  shell=True )
    
    # generate expression level file (randomly) 
    #pdb.set_trace()
    if en_debug == 0:
        subprocess.call( Python_command + ' ' + SimulPath +  '/genexplvprofile.py ' + BED_address + ' > ' + exp_address , shell=True )
    else:
        subprocess.call( Python_command + ' ' + SimulPath +  '/genexplvprofile.py ' + BED_sorted_address + ' > ' + exp_address , shell=True ) 
    #pdb.set_trace() #debug
    return [BED_sorted_address, exp_address]
 #--------------------------------------------------------------------------------------------------------

def check_BED_EXP_consistency(BED_address, exp_address): #BED_address may be sorted or not
    
    #pdb.set_trace()
    #check if BED_file and Explevel_file are consistent
    
    Explevel_file = open(exp_address, 'rU')
    Explevel_file.readline() # because the first line is just header
    BED_file = open(BED_address, 'rU')
    
    #if en_debug_0812==1:
    idx = 0
    for B_line, E_line in zip(BED_file, Explevel_file):
        #print(B_line)
        #print(E_line)
        blist = B_line.split('\t')
        elist = E_line.split('\t')
        bid = blist[3]
        eid = elist[0]
        
        b_blocks_sz = blist[10].split(',')
        b_blocks_num = int(blist[9])
        b_sz = 0
        for i in range(b_blocks_num):
            b_sz = b_sz + int(b_blocks_sz[i])
        e_sz = int(elist[1])
        
        if bid==eid and b_sz==e_sz:
            continue
            #print('\n%d bid=%s, b_sz=%d; eid=%s, e_sz=%d'%(idx, bid, b_sz, eid, e_sz))
        else:
            print('%d bid=%s, b_sz=%d; eid=%s, e_sz=%d (inconsistent)'%(idx, bid, b_sz, eid, e_sz))
            #pdb.set_trace()
        idx = idx+1
    
    #pdb.set_trace()
    Explevel_file.close() # = open(exp_address, 'rU')
    BED_file.close()
    
def calcExpressionSum(exp_address):
        
    Explevel_file = open(exp_address, 'rU')
    Explevel_file.readline() # because the first line is just header
    
    exp_sum = 0

    for E_line in Explevel_file:
        y = E_line.split()
        explevel = float( y[7] ) #7 #10
        exp_sum += explevel
    
    #debug_1013
    #pdb.set_trace()
    
    return exp_sum

# calculate the sum of generated expressions, to be used for line coverage
def calc_exp_sum(exp_address):
    exp_sum = 0.0
    with open(exp_address, 'r') as ef:
        for line in ef:
            if line[0]=='#' or len(line)<8: continue
            explv = float(line.split()[7]) 
            exp_sum += explv
    #pdb.set_trace()
    return exp_sum


def ExpressionLevel2Coverage(BED_sorted_address, exp_address,
                             cov_fn='/coverage.txt', Stat=None,
                             Lr=100, tot_N=1000000, exp_sum=10):
    #pdb.set_trace()
    #b=re.search('([\S]+)/([\S]+)\.([\S]+)', BED_sorted_address)
    b=re.search('([\S]+)/([\S]+)\.([\S]+)', exp_address)
    coverage_address = b.group(1) + cov_fn

    
    num_lines = sum(1 for line in open(BED_sorted_address))
    bar = Bar('BED and EXP to Vector', max=num_lines)    
    
 #   Explevel_sum = ExpextedCoverage(exp_address, N)
    

    """
    if en_debug_0812 == 1:
        check_BED_EXP_consistency(BED_sorted_address, exp_address)
    """
        
    Explevel_file = open(exp_address, 'rU')
    Explevel_file.readline() # because the first line is just header
    if open(BED_sorted_address, 'rU').readline()[0]=='#':
        BED_file = open(BED_sorted_address, 'rU')
        BED_file.readline() #it's possible that the first line is header
    else:
        BED_file = open(BED_sorted_address, 'rU')
    
    Total_number_segments=0

    vector = []
    for B_line, E_line in zip(BED_file,Explevel_file):
        bar.next()
        
        x = B_line.split()
        tr_start = int( x[1] )
        number_exon = int( x[9] )
        exon_len = x[10].split(',') 
        exon_start = x[11].split(',')
        
        
        y = E_line.split()
        explevel = float( y[7] ) #7 #10  
        transcript_len = int (y[1]) #1 #2 
         # positions 7 and 1 are for synthetic expression level files generated by genexplvprofile.py
         # in some standard formats, positions should be changed to 10 and 2
        
        #pdb.set_trace() #debug_1013
        
        line_cover = Lr * float(tot_N) * explevel / (exp_sum * float(transcript_len)) 
        # true formula for converting RPKM is line_cover = L * float(N) * explevel / (Explevel_sum * float(transcript_len))
        for i in range(number_exon):
            vector.append([tr_start + int(  exon_start[i] ) ,  Total_number_segments + i, line_cover, 1] )
            vector.append([tr_start + int(  exon_start[i] ) + int(exon_len[i]) , Total_number_segments + i, line_cover, -1] )
        Total_number_segments += number_exon

    bar.finish()
    
    #pdb.set_trace()
    non_overlapping_exon = collapse(vector, Stat)
    #pdb.set_trace()
    
    bar = Bar('NON_OVERLAP_EXON to COV_file', max=len(non_overlapping_exon)) 
    
    Cov_file = open( coverage_address, 'w+')
    for item in non_overlapping_exon:
        bar.next()
        Cov_file.write( '\t'.join(map(str, item)) + '\n')
        
    bar.finish()
    Cov_file.close()
    """
    to close other files
    """
    Explevel_file.close()
    BED_file.close()
    #pdb.set_trace() #debug  
    print('%s written'%coverage_address)
    return coverage_address

"""    
    vector_sorted = sorted(vector, key=itemgetter(0,3) )
    vector_sorted_updated = [[vector_sorted[0][0], vector_sorted[0][2] ]]
    index = 0
    #pdb.set_trace() #debug
    for i in range(1,len(vector_sorted)):
        if vector_sorted[i][0]> vector_sorted_updated[index][0]:
            
            #start of exon: explevel added in vector_sorted_updated
            #end   of exon: explevel 0 (or very close to 0, e.g. 2e-8 due to numerical issues)
            
            vector_sorted_updated.append([ vector_sorted[i][0], vector_sorted_updated[index][1] - vector_sorted[i][3]* vector_sorted[i][2]] )
            index += 1
        else:
            
            #if two exons have same start pos (they appear in two different transcripts),
            #they're merged in vector_sorted_updated
            
            #pdb.set_trace() #debug
            vector_sorted_updated[index][1] -= vector_sorted[i][3]* vector_sorted[i][2]


    #pdb.set_trace() #debug
    counter = 0
    Accumul_length = 0 
    Cov_file = open( coverage_address, 'w+')
    for i in range(len(vector_sorted_updated)-1):
        if abs(vector_sorted_updated[i][1])>0.0000001:
            counter +=1
            Accumul_length +=vector_sorted_updated[i+1][0] - vector_sorted_updated[i][0] 
            Cov_file.write( repr(counter) + '\t' + repr(vector_sorted_updated[i][0]) + '\t' + repr(vector_sorted_updated[i+1][0]) + '\t' + repr(Accumul_length) + '\t' + repr(vector_sorted_updated[i][1]) +'\n')   
         
    Cov_file.close()    
"""
    
    

#--------------------------------------------------------------------------------------------------------

def collapse(vector, Stat=None):
    # vector sorted is a sorted list, e.g., [[s1, 1, c1, +1], [e1, 1, c1, -1], [s2, 2, c2, +1], [e2, 2, c2, -1],...]
    # which is sorted w.r.t. to s/e and then +/-1
    # goal is to collapse it into non-overlapping segments
    #pdb.set_trace()
    vector_sorted = sorted(vector, key=itemgetter(0,3) )
    # example:
    #tmp = [[2,0,0,2],[1,0,0,1],[1,0,0,0],[2,0,0,1]]
    #sorted(tmp, key=itemgetter(0,3) )
    #[[1, 0, 0, 0], [1, 0, 0, 1], [2, 0, 0, 1], [2, 0, 0, 2]]
    
    """
    #dmp vector sorted for debug purpose
    if en_debug_0812==1:
        bar = Bar('Collapse Vector -- dmp vector sorted', max=len(vector_sorted)) 
        dmp_file = open(Default_Ref_Path+'dmp_vector_sorted.txt', 'w')
        for i in range(len(vector_sorted)):
            #pdb.set_trace()
            item_str = map(str, vector_sorted[i]) #'\t'.join(pulse_sorted[i])
            dmp_file.write('%10d\t%s\n'%(i,item_str))
            bar.next()
        bar.finish()
        dmp_file.close()
        #pdb.set_trace()
    """

    
    pulse_train ={}
    
    bar = Bar('Collapse Vector 1/2: vector sorted merged to pulse train', max=len(vector_sorted))
    i = 0
    for item in vector_sorted:
        bar.next()
        if item[0] in pulse_train.keys():
            #pdb.set_trace()
            #en_debug_0812 pulse_train[item[0]] += item[3] * item[2]
            pulse_train[item[0]][0] += item[3]*item[2]
            pulse_train[item[0]][1] += item[3] #item 3 is just +1 or -1
        else:
            #en_debug_0812 pulse_train[item[0]] = item[3] * item[2]
            pulse_train[item[0]] = [item[3]*item[2], item[3]]
        i = i+1
    bar.finish()
    
    #pdb.set_trace()
    pulse_list = pulse_train.items()
    pulse_sorted = sorted(pulse_list, key=itemgetter(0) )
    
    """
    #dmp pulse sorted for debug purpose
    if en_debug_0812==1:
        bar = Bar('Collapse Vector -- dmp pulse sorted', max=len(pulse_sorted)) 
        dmp_file = open(Default_Ref_Path+'dmp_pulse_sorted_modified.txt', 'w')
        for i in range(len(pulse_sorted)):
            #pdb.set_trace()
            item_str = map(str, pulse_sorted[i]) #'\t'.join(pulse_sorted[i])
            dmp_file.write('%10d\t%s\n'%(i,item_str))
            bar.next()
        bar.finish()
        dmp_file.close()
        #pdb.set_trace()
    """
    
    """
    #load pulse sorted for debug purpose
    if en_debug_0812==1:
        
        #pdb.set_trace()
        
        pulse_sorted = []
        
        with open(Default_Ref_Path+'dmp_pulse_sorted.txt') as DMP_file:
        
            reader = csv.reader(DMP_file, delimiter='\t')
            for row in reader:
                rlist = row[1].split('\'') #example: ['[', '20088866', ', ', '2127.0281455', ']']
                pulse_sorted.append([int(rlist[1]), float(rlist[3])])
                #pdb.set_trace()
            
        pdb.set_trace()
    """
    
    Aggregate_cover = 0
    Aggregate_sign = 0
    Aggregate_len = 0
    counter =0
    non_overlapping_exon=[]
    
    bar = Bar('Collapse Vector 2/2: pulse sorted aggregated', max=len(pulse_sorted)) 
    for i in range(len(pulse_sorted)-1):
        bar.next()
        #if pulse_sorted[i][0]==74501699:
        #    pdb.set_trace()
        Aggregate_cover += pulse_sorted[i][1][0]
        Aggregate_sign += pulse_sorted[i][1][1]
        """
        if abs(Aggregate_cover) > 0.00001:
            if Aggregate_sign == 0:# debug, compare with previous res
                counter += 1
                Aggregate_len += pulse_sorted[i+1][0] - pulse_sorted[i][0]
                non_overlapping_exon.append([-1, pulse_sorted[i][0], pulse_sorted[i+1][0], Aggregate_len, Aggregate_cover]) #counter==-1 indicates sign==0
        """        
        if Aggregate_sign > 0:
            """            
            if abs(Aggregate_cover) < 0.0001: # and not flag_found:
                #pdb.set_trace()
                print('[debug] abs of agrre cover < threshold')
                #pdb.set_trace()
                #flag_found = 1
            """
            counter += 1
            Aggregate_len += pulse_sorted[i+1][0] - pulse_sorted[i][0]
            non_overlapping_exon.append([counter, pulse_sorted[i][0], pulse_sorted[i+1][0], Aggregate_len, Aggregate_cover])
            #track statistics
            if Stat is not None:
                Stat.acc_cover.append(Aggregate_cover)
                Stat.acc_sign.append(Aggregate_sign)
            #else:
        #    pdb.set_trace()
        #    print('[debug] abs of agrre cover < threshold')
        #    pdb.set_trace()
            
    bar.finish()
    
    #pdb.set_trace()
    
    return non_overlapping_exon

 #--------------------------------------------------------------------------------------------------------

'''

genSNP==False, we just copy ref to tar, and SNP_address is empty. We do this because
we want to avoid the situation that a same pos at m and p are mutated to different SNPs

'''
def GenTarget(ref_address, coverage_address, Num_SNP, tar_address, SNP_address, genSNP=True ):

    if genSNP == False:
        cmd = 'cp %s %s'%(ref_address, tar_address)
        run_cmd(cmd)

        cmd = 'touch %s'%SNP_address
        run_cmd(cmd)

        #pdb.set_trace()
        return

    Exon_start=[]
    Exon_len=[0]
    #progress
    num_lines = sum(1 for line in open(coverage_address))
    bar = Bar('GenTarget -- read coverage', max=num_lines) 
    with open(coverage_address) as cov_file:
        for line in cov_file:
            bar.next()
            x = line.split()
            Exon_start.append( int(x[1]) )
            Exon_len.append( int(x[3]) )
    bar.finish()
    G_eff = Exon_len[-1]
    #pdb.set_trace()    
    
    #progress
    print('read ref DNA')
    #num_lines = sum(1 for line in open(ref_address))
    #bar = Bar('GenTarget -- read ref DNA', max=num_lines) 
    
    ref_file=open(ref_address,'rU')
    REF=''
    counter=0    
    for line in ref_file:
        #bar.next()
        if counter==0:
            header=line
            counter=1
        Segment = re.search(r'([acgtnACGTN]+)',line)
        if Segment!=None: 
            Seg = Segment.group(1)
        if Seg == line[:len(line)-1]:
            REF=REF+Seg
    #bar.finish()
    ref_file.close()    
    
    """
    REF stores string of DNA seq
    """
    G= len(REF)
    #pdb.set_trace()
    
    TARGET_list= list(REF) # convert string to list to be able to make relpacement
    
    SNP_pos = random.sample(range(0,G_eff), Num_SNP) 
    SNP_pos = sorted(SNP_pos)
    
    
    # SNP_pos is the position w.r.t. Transcriptome (G_eff)
    # The next script converts it to w.r.t. reference (G) 
    SNP_pos_eff = [0 for i in range(Num_SNP)]
    Exon_Index = 0
    bar = Bar('GenTarget -- get SNP_pos_eff', max=Num_SNP) 
    for i in range(Num_SNP):
        bar.next()
        while SNP_pos[i] >= Exon_len[Exon_Index]:
            Exon_Index +=1 
        SNP_pos_eff[i] = Exon_start[Exon_Index-1] - Exon_len[Exon_Index-1] + SNP_pos[i]
    bar.finish()
    #pdb.set_trace()
    
    SNP_file = open(SNP_address, 'w+') # SNP imformation will be stored in this file
    bar = Bar('GenTarget -- gen SNP', max=Num_SNP) 
    for i in range(0,Num_SNP):
        bar.next()
        b=random.randint(1,3)
        NewBasis = AddNoise( REF[SNP_pos_eff[i]] , b )
        TARGET_list[SNP_pos_eff[i]] = NewBasis
        SNP_file.write( '%d \t %s \t --> \t %s \n' % ( SNP_pos_eff[i] , REF[SNP_pos_eff[i]] , NewBasis))
    bar.finish()
    SNP_file.close()
    #pdb.set_trace() 
    
    # Write the target sequence  
    print('GenTarget -- write tar DNA')
    #num_lines = sum(1 for line in open(ref_address))
    #bar = Bar('GenTarget -- write tar', max=num_lines) 
    
    TARGET = "".join(TARGET_list) # convert back list to string
    tar_file=open(tar_address , 'w+')
    tar_file.write(header)
    counter = 0
    while 50 * counter <G:
        #bar.next()
        tar_file.write(TARGET[50 * counter : min(50 * counter + 50 ,G)]+'\n')
        counter += 1
    tar_file.close()
    #bar.finish()
    #pdb.set_trace() #debug  
    
    return  tar_address, SNP_address
 #--------------------------------------------------------------------------------------------------------

                   
def AddNoise(Basis,shift):
    '''
    acgt
    '''
    k=Basis
    if shift==1:
        if   Basis=='A' or Basis=='a' : k='C'
        elif Basis=='C' or Basis=='c' : k='G'
        elif Basis=='G' or Basis=='g' : k='T'
        elif Basis=='T' or Basis=='t' : k='A'
    elif shift==2:
        if   Basis=='A' or Basis=='a' : k='G'
        elif Basis=='C' or Basis=='c' : k='T'
        elif Basis=='G' or Basis=='g' : k='A'
        elif Basis=='T' or Basis=='t' : k='C'
    elif shift==3:
        if   Basis=='A' or Basis=='a' : k='T'
        elif Basis=='C' or Basis=='c' : k='A'
        elif Basis=='G' or Basis=='g' : k='C'
        elif Basis=='T' or Basis=='t' : k='G'
    return k   
 #--------------------------------------------------------------------------------------------------------
 
def ReadGeneration(tar_address, BED_address, exp_address,  N, L, error_rate):
    
    #pdb.set_trace() #debug

    # http://alumni.cs.ucr.edu/~liw/rnaseqreadsimulator.html
    b=re.search('([\S]+)/([\S]+)\.([\S]+)', BED_address)
    Path = b.group(1)
    BED_sorted_address = b.group(1) + '/' + b.group(2) + '-sorted.' + b.group(3) 
    c=re.search('([\S]+)/([\S]+)\.([\S]+)', tar_address)
 
    # sort BED file
    subprocess.call( 'sort -k 1,1 -k 2,2n ' +  BED_address + ' > ' +  BED_sorted_address,  shell=True )
    

    # generates simulated RNA-Seq reads
    readBED_address = Path + '/' + c.group(2) + '_read_l' + repr(L) + '.bed' #en_debug_0811
    
    subprocess.call( Python_command + ' ' + SimulPath + '/gensimreads.py -n ' + repr(N) + ' -l ' + repr(L) + ' -e ' + exp_address + ' ' + BED_sorted_address + ' > ' + readBED_address , shell=True )
    
    # extract sequences from bed file
    readFA_address = Path + '/' + c.group(2) + '_read_l' + repr(L) + '.fasta' #en_debug_0811
    if en_debug==0:
        subprocess.call( Python_command + ' ' + SimulPath + '/getseqfrombed.py ' +  '--errorrate ' +  '%.2f' % error_rate + ' '  +   readBED_address + ' ' + tar_address + ' > ' + readFA_address, shell=True )
    else:
        subprocess.call( Python_command + ' ' + SimulPath + '/getseqfrombed.py ' +  '--errorrate ' +  '%.2f' % error_rate + ' -l ' + repr(L) + ' '  +   readBED_address + ' ' + tar_address + ' > ' + readFA_address, shell=True )

    # fasta --> fastq
    readFQ_address = Path + '/' + c.group(2) + '_read_l' + repr(L) + '.fastq'
    subprocess.call( 'perl ' + FA2FQ_address + ' ' + readFA_address + ' > '  + readFQ_address, shell=True )
    #pdb.set_trace() #debug
    return [readBED_address, readFA_address, readFQ_address]
 #--------------------------------------------------------------------------------------------------------
 
def main():
    pdb.set_trace() #debug
    Path = Default_Ref_Path
    ref_address = Path + '/Chr15.fa'
    BED_address = Path + '/hg19_chr15-UCSC.bed'
    gtf_address = Path + '/hg19_chr15-UCSC.gtf'
#    exp_address = Path + '/Chr15.exp'  # standard expression level file from database 
    

    # generate a random expression level file
    [BED_sorted_address, exp_address] = BED2ExpressionLevel(BED_address)
    
    # Find the exonic parts with coverage not less than a certain value
    coverage_address = ExpressionLevel2Coverage(BED_sorted_address, exp_address)
    
    #pdb.set_trace()
    
    # Num_SNP = Number of SNP's (would be randomly located only in Exon regions)
    Num_SNP = 20
    
    # Generate 2 random target2 (for paternal and maternal) sequence from ref_address by insering Num_SNP SNPs in the exonic positions
    tar_address_m = Path + '/Tar_m.txt'
    tar_address_p = Path + '/Tar_p.txt'
    SNP_address_m = Path + '/SNP_m.txt' 
    SNP_address_p = Path + '/SNP_p.txt'
    GenTarget(ref_address, coverage_address, Num_SNP, tar_address_m, SNP_address_m )
    GenTarget(ref_address, coverage_address, Num_SNP, tar_address_p, SNP_address_p )
    
    N=10000     #Number of Reads
    L=100       #Read Length
    error_rate = 0
    [readBED_address, readFA_address, readFQ_address] = ReadGeneration(tar_address_m, BED_sorted_address, exp_address,  N, L, error_rate)
#    subprocess.call( 'mv ' +  readFQ_address + ' ' +  'm_' + readFQ_address ,  shell=True )
    [readBED_address, readFA_address, readFQ_address] = ReadGeneration(tar_address_p, BED_sorted_address, exp_address,  N, L, error_rate)
#    subprocess.call( 'mv ' +  readFQ_address + ' ' +  'p_' + readFQ_address ,  shell=True )
     
if __name__ == '__main__':
    main()
    