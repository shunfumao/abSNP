import sys, pdb, numpy
from intervaltree import Interval, IntervalTree 

from tool_address import FA2FQ_address

from old_code.batch_run_case1plus6 import enforce_unique_readID, enforce_unique_readID_bed
from old_code.util import run_cmd
from old_code.snp_oper import load_snps, gen_genome_of_snps
from old_code.Synthesis import calc_exp_sum, ExpressionLevel2Coverage, GenTarget
from old_code.ReadProcess import BED2Exon1
from old_code.debug_MACRO import FilterCoverage

from old_code_multiShannon.sim_reads import sim_reads_g_b

def main():

    pdb.set_trace()
    
    return

#calculate the qt-percentile (0~99) value of the abundances in cov_file
def calc_cover_thre(cov_file, qt):

    #pdb.set_trace()

    vals = []

    with open(cov_file) as f:
        for line in f:
            x = line.split()
            vals.append(float(x[4]))

    coverThre = numpy.percentile(vals, qt)

    #pdb.set_trace()

    return coverThre 

'''
usage:

python sim_data_generator.py
--gen_sim_exp_snp_tar
--bedSorted bedSorted
-O outFolder (exp_m.txt, exp_p.txt; 
              cov_m.txt, cov_p.txt; cov_m_<qt>.txt, cov_p_<qt>.txt;
              SNP_m.txt, SNP_p.txt;
              Tar_m.txt, Tar_p.txt)
--qt qt (0~99; SNPs are generated at qt quantile of coverage regions)
[-L readLen -N numReads] (used for cov calculation ==> NOT USED)
--refGenome refGenome
--NumSNP numSNP
'''
def gen_sim_exp_snp_tar(args):

    #pdb.set_trace()

    bedSorted = args[args.index('--bedSorted')+1]
    outFolder = args[args.index('-O')+1]
    qt = int(args[args.index('--qt')+1])

    if '-L' in args:
        L = int(args[args.index('-L')+1])
    else:
        L = 100

    if '-N' in args:
        N = int(args[args.index('-N')+1])
    else:
        N = 100000

    refGenome = args[args.index('--refGenome')+1]

    numSNP = int(args[args.index('--NumSNP')+1])


    #output files
    exp_m = '%s/exp_m.txt'%outFolder
    exp_p = '%s/exp_p.txt'%outFolder

    #generate expression
    cmd = 'python tools/RNASeqReadSimulator/genexplvprofile.py %s > %s'%(bedSorted, exp_m)
    run_cmd(cmd)

    cmd = 'python tools/RNASeqReadSimulator/genexplvprofile.py %s > %s'%(bedSorted, exp_p)
    run_cmd(cmd)

    #exp --> cov
    cov_m = ExpressionLevel2Coverage(bedSorted, exp_m, cov_fn='/coverage_m.txt', Stat=None)
    cov_m_filt = cov_m[:-4]+'_%d.txt'%qt

    cov_p = ExpressionLevel2Coverage(bedSorted, exp_p, cov_fn='/coverage_p.txt', Stat=None)
    cov_p_filt = cov_p[:-4]+'_%d.txt'%qt

    #cov --> cov_filt
    coverThre_m = calc_cover_thre(cov_m, qt) ##
    FilterCoverage(cov_m, cov_m_filt, coverThre_m)

    coverThre_p = calc_cover_thre(cov_p, qt) ##
    FilterCoverage(cov_p, cov_p_filt, coverThre_p)

    #gen snps & tar
    tar_address_m = '%s/Tar_m.txt'%outFolder
    tar_address_p = '%s/Tar_p.txt'%outFolder

    SNP_address_m = '%s/SNP_m.txt'%outFolder
    SNP_address_p = '%s/SNP_p.txt'%outFolder

    #pdb.set_trace()

    GenTarget(refGenome, cov_m_filt, numSNP, tar_address_m, SNP_address_m, genSNP=True)
    GenTarget(refGenome, cov_p_filt, numSNP, tar_address_p, SNP_address_p, genSNP=True)

    #pdb.set_trace()

    return

'''
usage:

python sim_data_generator.py --mark_homozygous -m snp_m file -p snp_p file
                                               [-m2 snp_m2_file] [-p2 snp_p2_file]
                                               [--no_homozygous]
                                               [--outputHomo snp_homo_file]

description:
- if --no_homozygous:
  homozygous snps will not be output
  from snp_m.txt and snp_p.txt, output snp_m_noHomo.txt and snp_p_noHomo.txt
- if no --no_homozygous (default)
  homozygous will be marked as: gPos rB --> tB (*)
  from snp_m.txt and snp_p.txt, output snp_m_markHomo.txt and snp_p_markHomo.txt
- if --outputHomo is specified, we output homozygous snps into specified snp_homo_file

'''
def mark_homozygous(args):

    if '--no_homozygous' in args:
        noHomo = True
    else:
        noHomo = False

    m1 = args[args.index('-m')+1]
    if '-m2' in args:
        m2 = args[args.index('-m2')+1]
    else:
        if noHomo == True:
            m2 = m1[:-4]+'_noHomo.txt'
        else:
            m2 = m1[:-4]+'_markHomo.txt'

    p1 = args[args.index('-p')+1]
    if '-p2' in args:
        p2 = args[args.index('-p2')+1]
    else:
        if noHomo == True:
            p2 = p1[:-4]+'_noHomo.txt'
        else:
            p2 = p1[:-4]+'_markHomo.txt'

    snps_m = load_snps(m1)
    snps_p = load_snps(p1)

    with open(m2, 'w') as of:
        itms = sorted(snps_m.items(), key=lambda x:x[0])
        for k, v in itms:
            if k in snps_p:
                if noHomo == False:
                    st = '%d\t%s\t-->\t%s\t(*)\n'%(k, v[0], v[1])
                    of.write(st)
            else:
                st = '%d\t%s\t-->\t%s\n'%(k, v[0], v[1])
                of.write(st)
    print('%s written'%m2)

    with open(p2, 'w') as of:
        itms = sorted(snps_p.items(), key=lambda x:x[0])
        for k, v in itms:
            if k in snps_m:
                if noHomo == False:
                    st = '%d\t%s\t-->\t%s\t(*)\n'%(k, v[0], v[1])
                    of.write(st)
            else:
                st = '%d\t%s\t-->\t%s\n'%(k, v[0], v[1])                
                of.write(st)
    print('%s written'%p2)

    if '--outputHomo' in args:
        #pdb.set_trace()
        snp_homo_file = args[args.index('--outputHomo')+1]

        with open(snp_homo_file, 'w') as shf:
            itms = sorted(snps_m.items(), key=lambda x:x[0])
            for k, v in itms:
                if k in snps_p:
                    #pdb.set_trace()
                    st = '%d\t%s\t-->\t%s\n'%(k, v[0], v[1])
                    shf.write(st)

        print('%s written'%snp_homo_file)

    return

'''
usage:

python sim_data_generator.py --sel_snps
                             -i input_snp_file
                             -o output_snp_file
                             -e region_file

description:

filter input_snp_file into output_snp_file, such that:
- snps are restricted by region_file

'''
def sel_snps(args):

    input_snp_file = args[args.index('-i')+1]
    output_snp_file = args[args.index('-o')+1]
    region_file = args[args.index('-e')+1]

    tree = IntervalTree()

    with open(region_file, 'r') as rf:

        #pdb.set_trace()

        for line in rf:
            if line[0]=='#': continue
            tokens = line.split()
            if len(tokens)>=2:
                tree.add(Interval(int(tokens[0]), int(tokens[1])))
    #pdb.set_trace()

    with open(input_snp_file, 'r') as f1, open(output_snp_file, 'w') as f2:

        for line in f1:
            if line[0]=='#': continue
            gPos = int(line.split()[0])-1 #1-based into 0-based
            query_res = tree[gPos] #a set of Intervals containing gPos
            if len(query_res)!=0:
                #pdb.set_trace()
                query_res_int = sorted(query_res)[0]
                #st = '%s\t[%d,%d)\n'%(line.strip(), query_res_int.begin, query_res_int.end)
                st = line
                f2.write(st)

    return

'''
usage:

python sim_data_generator.py --sel_snps_covered
                             -i input_snp_file
                             -o output_snp_file
                             -a snp_read_cov_file

description:

select snps s.t. the input snps don't contain uncovered snps (indicated by an auxillary file -a)

snp_read_cov_file
- generated by snp_read_cov1
- format:
col-0: gPos (1-based)
col-1: # of m reads covering the snp
col-2: # of p reads covering the snp
col-3: (*) if no m/p reads covering the snps

'''
def sel_snps_covered(args):

    input_snp_file = args[args.index('-i')+1]
    output_snp_file = args[args.index('-o')+1]
    snp_read_cov_file = args[args.index('-a')+1]

    #pdb.set_trace()

    uncovered_locations = []
    with open(snp_read_cov_file, 'r') as inf:
        for line in inf:
            if line[0]=='#' or len(line.split())<3: continue
            tokens = line.split()
            if int(tokens[1])+int(tokens[2])==0:
                uncovered_locations.append(int(tokens[0]))

    #pdb.set_trace()

    snps = load_snps(input_snp_file)

    with open(output_snp_file, 'w') as outf:
        for gPos1, rB_tB in snps.items():
            if gPos1 in uncovered_locations:
                continue
            else:
                outf.write('%d\t%s\t-->\t%s\n'%(gPos1, rB_tB[0], rB_tB[1]))
        print('%s written'%output_snp_file) 

    #pdb.set_trace()

    return

'''
generate line coverage (i.e. abundance per exonic location)

usage:
python sim_data_generator.py --gen_coverage 
                             -b sorted_bed -e exp_file -o coverage_file
                             -L readLength -N numReads

note:
we make readLength, numReads and exp_sum more flexible here, instead of fixing them to be 10, 1e6 and 10 as before,
which may be the reason why prev ideal coverage is worse than rsem coverage

'''
def gen_coverage(args):

    #pdb.set_trace()

    sorted_bed = args[args.index('-b')+1]
    exp_file = args[args.index('-e')+1]
    coverage_file = args[args.index('-o')+1]
    cov_fn = '/'+coverage_file.split('/')[-1]

    readLength = int(args[args.index('-L')+1])
    numReads = int(args[args.index('-N')+1])    
    exp_sum = calc_exp_sum(exp_file)

    ExpressionLevel2Coverage(BED_sorted_address=sorted_bed, 
                             exp_address=exp_file,
                             cov_fn=cov_fn, Stat=None,
                             Lr=readLength, tot_N=numReads, exp_sum=exp_sum)
    return

'''
usage:
python sim_data_generator.py --snp_cov -s snp_file -m cov_file_m -p cov_file_p -o snp_cov_file

description:
- find per snp's exon interval and related abundance, helpful to see how snp is covered
- snp_cov_file: gPos(1-based), exon_stt(0-based), exon_stp(excluded), abundance of cov_file_m, abundance of cov_file_p

'''
def snp_cov(args):

    snp_file = args[args.index('-s')+1]
    cov_file_m = args[args.index('-m')+1]
    cov_file_p = args[args.index('-p')+1]
    snp_cov_file = args[args.index('-o')+1]

    tree = IntervalTree()

    #pdb.set_trace()
    with open(cov_file_m, 'r') as cf_m, open(cov_file_p, 'r') as cf_p:

        for line, line2 in zip(cf_m, cf_p):
            if line[0]=='#': continue
            tokens = line.split()
            tokens2 = line2.split()
            if len(tokens)>=5:
                tree.add(Interval(int(tokens[1]), int(tokens[2]), [float(tokens[4]), float(tokens2[4])]))
    
    #pdb.set_trace()
    snps = load_snps(snp_file)
    snp_cov = []
    for k, v in snps.items():
        gPos = k-1 
        query_res = tree[gPos]
        if len(query_res)!=0:
            query_res_int =  sorted(query_res)[0]
            snp_cov.append([k, v[0], v[1], query_res_int.begin, query_res_int.end, query_res_int.data[0], query_res_int.data[1]])
        else:
            snp_cov.append([k, v[0], v[1], -1, -1, 0, 0])

    #pdb.set_trace()
    snp_cov = sorted(snp_cov, key=lambda x:x[0])
    with open(snp_cov_file, 'w') as of:
        st = '#gPos\texonStart\texonStop\tmCoverage\tpCoverage\n'
        of.write(st)
        for k, rB, tB, exon_stt, exon_stp, abundance_m, abundance_p in snp_cov:
            st = '%d\t%s\t-->\t%s\t%d\t%d\t%f\t%f\n'%(k, rB, tB, exon_stt, exon_stp, abundance_m, abundance_p)
            of.write(st)
    #pdb.set_trace()

    print('%s written'%snp_cov_file)
    return

'''
find snp and whether it's covered by reads

usage:
python sim_data_generator.py --snp_read_cov -s snp_file -m m_read_bed -p p_read_bed -o snp_read_cov_file

format of snp_read_cov_file:
col-0: gPos (1-based)
col-1: # of m reads covering the snp
col-2: # of p reads covering the snp
'''
'''
def snp_read_cov(args):

    snp_file = args[args.index('-s')+1]
    m_read_bed = args[args.index('-m')+1]
    p_read_bed = args[args.index('-p')+1]
    read_beds = [m_read_bed, p_read_bed]
    trees = [IntervalTree(), IntervalTree()]

    snp_read_cov_file = args[args.index('-o')+1]

    snps = load_snps(snp_file)

    intermediate_files = []

    #build trees of read bed files for query purpose    
    for i in range(2):
        tmp_exon_file = read_beds[i] + '.tmp_exon_file'; intermediate_files.append(tmp_exon_file)
        BED2Exon1(read_beds[i], tmp_exon_file)
        print('%s written'%tmp_exon_file)
        #pdb.set_trace()

        tree = trees[i]
        with open(tmp_exon_file, 'r') as tef:
            for line in tef:
                if line[0]=='#' or len(line.split())<3: continue
                tokens = line.split()
                e_stt = int(tokens[0]) #0-based
                e_stp = int(tokens[1]) #exclusive
                data = [] #read ids
                for t in xrange(2,len(tokens)):
                    rid = tokens[t].split(',')[0]
                    data.append(rid)
                tree.add(Interval(e_stt, e_stp, data))
        print('%d-th tree built'%i)
        pdb.set_trace()

    #check snp read coverage and write to output
    snp_cnt = {} #key gPos (1-based), val=[# of m reads covering the snp, # of p reads covering the snp]
    for k, v in snps.items():
        gPos = k-1
        mp_sum = [0,0]
        for j in range(2):
            query_res = trees[j][gPos]
            if len(query_res) != 0:
                for interval in sorted(query_res):
                    mp_sum[j] += len(interval.data)
        snp_cnt[k]=mp_sum
    #pdb.set_trace()
    snp_cnt = snp_cnt.items()
    snp_cnt = sorted(snp_cnt, key=lambda x:x[0])
    pdb.set_trace()


    with open(snp_read_cov_file, 'w') as of:

        st = '#gPos\t#_m_reads\t#_t_reads\n'
        of.write(st)

        for gPos, mn_cnts in snp_cnt:
        
            st = '%d\t%d\t%d\n'%(gPos, mn_cnts[0], mn_cnts[1])
            of.write(st)
        #pdb.set_trace()
        print('%s written'%snp_read_cov_file)

    #clear intermediate files
    for i in range(len(intermediate_files)):
        cmd = 'rm %s'%intermediate_files[i]
        run_cmd(cmd)
    #pdb.set_trace()

    return
'''

def bed2cov(bed):
    res = {} #gPos (0-based): coverage

    with open(bed, 'r') as inf:

        nLines=sum([1 for l in open(bed,'r')]); T=nLines/100; p=0; q=0;

        for line in inf:
            p += 1
            if p>=T: p=0; q+=1; sys.stdout.write('\r'); sys.stdout.write('%d %% processed (bed2cov)'%q); sys.stdout.flush()
            if line[0]=='#' or len(line.split())<4: continue

            x = line.split()
            tr_ID = x[3]
            tr_start = int( x[1] )
            number_exon = int( x[9] )
            EXON_len_strng = x[10].split(',') 
            EXON_len = [ int(EXON_len_strng[i]) for i in range(number_exon) ]
            EXON_start_strng = x[11].split(',')
            EXON_start = [ int(EXON_start_strng[i]) for i in range(number_exon) ]
        
            for i in range(number_exon):
                exon_start = tr_start + int(EXON_start[i]) #0-based,
                exon_end = exon_start + int(EXON_len[i]) #exclusive
                for j in xrange(exon_start, exon_end):
                    if j in res:
                        res[j]+=1
                    else:
                        res[j]=1
    return res

'''
find snp and whether it's covered by reads

usage:
python sim_data_generator.py --snp_read_cov1 -s snp_file -m m_read_bed -p p_read_bed 
                             -o snp_read_cov_file (name after m or p read_bed)

format of snp_read_cov_file:
col-0: gPos (1-based)
col-1: # of m reads covering the snp
col-2: # of p reads covering the snp
col-3: (*) if no m/p reads covering the snps

snp_read_cov_file:
recommends to be named after related m_read_bed or p_read_bed file
'''
def snp_read_cov1(args): #try to avoid BED2Exon1

    snp_file = args[args.index('-s')+1]
    m_read_bed = args[args.index('-m')+1]
    p_read_bed = args[args.index('-p')+1]
    snp_read_cov_file = args[args.index('-o')+1]

    snps = load_snps(snp_file)

    #bed --> {gPos:cov}
    gPos_cov_m = bed2cov(m_read_bed)
    gPos_cov_p = bed2cov(p_read_bed)

    #pdb.set_trace()
    snp_cnt = {}
    for k, v in snps.items():
        gPos = k-1
        mp_sum = [0,0]
        if gPos in gPos_cov_m:
            mp_sum[0]=gPos_cov_m[gPos]
        if gPos in gPos_cov_p:
            mp_sum[1]=gPos_cov_p[gPos]
        snp_cnt[k]=mp_sum
    snp_cnt = snp_cnt.items()
    snp_cnt = sorted(snp_cnt, key=lambda x:x[0])
    #pdb.set_trace()

    num_no_coverage = 0
    with open(snp_read_cov_file, 'w') as of:

        st = '#gPos\t#_m_reads\t#_t_reads\t(no coverage)\n'
        of.write(st)

        for gPos, mn_cnts in snp_cnt:
        
            if sum(mn_cnts)==0:
                num_no_coverage += 1
                st = '%d\t%d\t%d\t(*)\n'%(gPos, mn_cnts[0], mn_cnts[1])
            else:
                st = '%d\t%d\t%d\n'%(gPos, mn_cnts[0], mn_cnts[1])
            of.write(st)
        #pdb.set_trace()
        print('%d out of %d snps not covered'%(num_no_coverage, len(snp_cnt)))
        print('%s written'%snp_read_cov_file)

    return


'''
usage:
python sim_data_generator.py --reasign_exp 
                             -s snp_file
                             -b sorted_bed_file
                             -e old_exp_file
                             -o new_exp_file

description:

- we collect exp vals from old_exp_file, and reasign them from high to low to the transcripts that contain highest snps to lowest snps
- for example, for snps at data_real/ref_snp/ in chr15 coding region w/o homozygous snps, 
               and based on bed file gencode.v19.annotation.target.chr15.sorted.bed,
               and generated exp files at data_real_abSNP_batch/reads_N100000_L100_Err0.00/intermediate/,
  we find for m allele, there're 1001 heterozygous snps. among 7314 trids, about 1200 (16.4%) trids contain at least 1 snp. we assign top 16.4% highest exp vals to these trids.
          for p allele, there're 899  heterozygous snps, among 7314 trids, about 1100 (15.0%) trids contain at least 1 snp. we assign top 15.0% highest exp vals to these trids.
          for m & p alleles, there're 1462 homozygous snps, among 7314 trids, about 1700 (23%) trids contain at least 1 snp. we assign top 23% highest exp vals to these trids.
'''
def reasign_exp(args): 

    snp_file = args[args.index('-s')+1]
    sorted_bed_file = args[args.index('-b')+1]
    old_exp_file = args[args.index('-e')+1]
    new_exp_file = args[args.index('-o')+1]

    intermediate_files = []
    tmp_exon_file = sorted_bed_file + '.tmp_exon_file'; intermediate_files.append(tmp_exon_file)
    BED2Exon1(sorted_bed_file, tmp_exon_file)
    #pdb.set_trace()

    #interval tree, each interval=exon, corresponding data=list of trs
    tree = IntervalTree()
    with open(tmp_exon_file, 'r') as ef:
        for line in ef:
            if line[0]=='#' or len(line.split())<3: continue
            tokens = line.split()
            e_stt = int(tokens[0]) #0-based
            e_stp = int(tokens[1]) #exclusive
            data = []
            for t in xrange(2,len(tokens)):
                trid = tokens[t].split(',')[0]
                data.append(trid)
            tree.add(Interval(e_stt, e_stp, data))
    #pdb.set_trace()

    #tr_snp_cnt = {} #key - trid; val - # of snps
    tr_snp_cnt = {}
    with open(sorted_bed_file, 'r') as bf:
        for line in bf:
            if line[0] == '#' or len(line.split())<4: continue
            tokens = line.split()
            trid = tokens[3]
            tr_snp_cnt[trid] = 0
    #pdb.set_trace()

    #mark transcripts that contain snps
    snps = load_snps(snp_file)
    for gPos, rB_tB in snps.items():
        gPos = gPos-1 
        query_res = tree[gPos]
        if len(query_res)!=0:
            intervals =  sorted(query_res)
            for interval in intervals:
                interval_trids = interval.data 
                for trid in interval_trids:
                    if trid in tr_snp_cnt:
                        tr_snp_cnt[trid] += 1
    tr_snp_cnt = tr_snp_cnt.items()
    tr_snp_cnt = sorted(tr_snp_cnt, key=lambda x:-x[1])
    #pdb.set_trace()

    #re-asign exp values
    exp_vals = []
    with open(old_exp_file, 'r') as oef:
        for line in oef:
            if line[0]=='#' or len(line)<8: continue
            exp_vals.append(float(line.split()[7]))
    exp_vals = sorted(exp_vals, key=lambda x:-x)
    #pdb.set_trace()

    tr_exp = {} #trid, new exp
    for i in range(len(tr_snp_cnt)):
        tr_exp[tr_snp_cnt[i][0]] = exp_vals[i]
    #pdb.set_trace()

    with open(old_exp_file, 'r') as oef, open(new_exp_file, 'w') as nef:
        for line in oef:
            if line[0]=='#' or len(line)<8:
                nef.write(line)
            else:
                tokens = line.split()
                tokens[7] = str(tr_exp[tokens[0]])
                st = '\t'.join(tokens)+'\n'
                nef.write(st)

    #clear intermediate files
    for i in range(len(intermediate_files)):
        cmd = 'rm %s'%intermediate_files[i]
        run_cmd(cmd)
    #pdb.set_trace()

    return

'''
description:

modified based on BED2Exon1

given a tr_bed_file (sorted), output:
- tree_exon:
  -- an interval tree
  -- each node is an interval with [e_stt/0-based, e_stp)
     and data as list of associated trid,leftBases,rightBases
- dic_tr_exonTree_exonBlocks
  -- key: trid
  -- val: [exonTree, exonBlocks]
     exonTree: [REL_e_stt, REL_e_stp) w/ data exon id
     exonBlocks: list of [e_stt, e_stp)
'''
def parse_bed(tr_sorted_bed_file):

    #pdb.set_trace()

    tree_exon = IntervalTree()
    dic_tr_exonTree_exonBlocks = {}

    Dict = {} #key [e_stt, e_stp) val counter
    EXONS = [ ] #list of [trid, left bases, right bases], i-th item corresponds to Dict entry with counter=i
    
    counter =0
    bed_file = open(tr_sorted_bed_file, 'rU')
    nLines=sum([1 for l in open(tr_sorted_bed_file,'r')]); T=nLines/100; p=0; q=0;
    for line in bed_file:
        p += 1
        if p>=T: p=0; q+=1; sys.stdout.write('\r'); sys.stdout.write('%d %% processed (parse_bed)'%q); sys.stdout.flush()
        if line[0]=='#' or len(line.split())<4: continue
        
        x = line.split()
        tr_ID = x[3]
        tr_start = int( x[1] )
        number_exon = int( x[9] )
        EXON_len_strng = x[10].split(',') 
        EXON_len = [ int(EXON_len_strng[i]) for i in range(number_exon) ]
        
        #pdb.set_trace()
        
        EXON_start_strng = x[11].split(',')
        EXON_start = [ int(EXON_start_strng[i]) for i in range(number_exon) ]
        
        dic_tr_exonTree_exonBlocks[tr_ID] = [IntervalTree(), []]
        
        acc_exon_len = 0
        for i in range(number_exon):
            exon_start = tr_start + int(EXON_start[i])
            exon_end = exon_start + int(EXON_len[i])

            REL_e_stt = acc_exon_len
            REL_e_stp = REL_e_stt + EXON_len[i]
            acc_exon_len += EXON_len[i]

            dic_tr_exonTree_exonBlocks[tr_ID][0].add(Interval(REL_e_stt, REL_e_stp, i))
            dic_tr_exonTree_exonBlocks[tr_ID][1].append([exon_start, exon_end])

            if (exon_start,exon_end) in Dict.keys():
                EXONS [ Dict[ (exon_start,exon_end) ] ].append( ( tr_ID, sum(EXON_len[:i]), sum(EXON_len[i+1:]) ) )
            else:
                Dict[ (exon_start,exon_end) ] = counter
                EXONS.append( [ ( tr_ID, sum(EXON_len[:i]), sum(EXON_len[i+1:]) ) ] )
                counter += 1

    #pdb.set_trace()
    print('')

    EXONS_sortet = sorted( Dict.keys() , key=lambda x: x[0])

    for exon in EXONS_sortet:
        stt = exon[0]
        stp = exon[1]
        trs = []
        for tr in EXONS[Dict[exon]]:
            st = tr[0] + ',' + repr(tr[1]) + ',' + repr(tr[2])
            trs.append(st)
        tree_exon.add(Interval(stt, stp, trs))
    #pdb.set_trace()

    return [tree_exon, dic_tr_exonTree_exonBlocks]

'''
find Tr s.t. on the left (and right) side of k, there're at least readLen-1 bases,
if no such Tr, find Tr with max left bases and right bases

inputs:
trInfo_list: list of [trid, L_left, L_right, L_left+L_right]
k: gPos of SNP (1-based)
f_output_log: a file handler; if no tr has L_left > readLen-1 and L_right > readLen-1, output related info to f_output_log
'''
def sel_longest_tr(tr_Info_list, k, f_output_log=None, readLength=100):

    longest_trid = ''
    num_left_bases = -1
    num_right_bases = -1

    for trid, L_left, L_right, tot in tr_Info_list:
        if L_left>=readLength-1 and L_right>=readLength-1:
            longest_trid = trid; 
            num_left_bases = readLength-1
            num_right_bases = readLength -1
            break
        else:
            curr_num_left_bases = min(L_left, readLength-1)
            curr_num_right_bases = min(L_right, readLength-1)
            if (curr_num_left_bases>=num_left_bases or curr_num_right_bases>=num_right_bases) and \
               (curr_num_left_bases+curr_num_right_bases>num_left_bases+num_right_bases):
                longest_trid=trid
                num_left_bases=curr_num_left_bases
                num_right_bases=curr_num_right_bases

    if num_left_bases<readLength-1 or num_right_bases<readLength-1 and f_output_log is not None:
        f_output_log.write('%d\t%s,%d,%d\n'%(k, longest_trid, num_left_bases, num_right_bases))

    if num_left_bases==-1:
        print('unexpected at sel_longest_tr')
        pdb.set_trace()    

    return longest_trid, num_left_bases

#
#pos: 0-based -- abosolute location
#exonBlocks: list of [e_stt, e_stp) -- absolute location
def get_exon_id(pos, exonBlocks):
    pos_e_id = -1 
    for eid in range(len(exonBlocks)):
        if pos >= exonBlocks[eid][0] and pos < exonBlocks[eid][1]:
            pos_e_id = eid; break
    return pos_e_id

#given a rel pos on a transcript and its relative interval tree [REL_e_stt, REL_e_stp) w/ data exon id
#return e id, or -1 if not found
def get_exon_id_relTree(rel_pos, rel_int_tree):
    query_int = rel_int_tree[rel_pos]
    if len(query_int)==0:
        return -1
    else:
        return sorted(query_int)[0].data

#given an absolute 0-based gPos and its exon id in exonBlocks of a transcript
#return relative location of gPos on the transcript
def get_rel_tr_loc(gPos, gPos_e_id, exonBlocks):
    if gPos_e_id==-1:
        rel_gPos=-1
    else:
        rel_gPos=gPos-sum([exonBlocks[j][0] for j in range(gPos_e_id+1)]) + sum([exonBlocks[j][1] for j in range(gPos_e_id)])
    return rel_gPos

#given a relative 0-based pos and its exon id in exonBlocks of a transcript
#return absolute location of pos on the transcript
def get_abs_tr_loc(rel_gPos, gPos_e_id, exonBlocks):
    if rel_gPos==-1 or gPos_e_id==-1:
        return -1
    else:
        abs_gPos = rel_gPos + sum([exonBlocks[j][0] for j in range(gPos_e_id+1)]) - sum([exonBlocks[j][1] for j in range(gPos_e_id)])
        return abs_gPos

'''
sample a <readLength>-bp read starting at i (0-based) at transcript tr,
return a bed line if available; otherwise return '' (read out of transcript boundary)

dic_tr_exonTree_exonBlocks
- key: trid
- val: [exonTree, exonBlocks]
  exonTree: [REL_e_stt, REL_e_stp) w/ data exon id
  exonBlocks: list of [e_stt, e_stp)
'''
def sample_a_read(tr, dic_tr_exonTree_exonBlocks, gPos, i, readLen, chrom):
    
    read_line=''

    #pdb.set_trace()

    [exonTree, exonBlocks]= dic_tr_exonTree_exonBlocks[tr]

    gPos_e_id = get_exon_id(gPos, exonBlocks)
    rel_gPos = get_rel_tr_loc(gPos, gPos_e_id, exonBlocks)

    rel_StartPos = rel_gPos-i
    StartPos_e_id = get_exon_id_relTree(rel_StartPos, exonTree)
    abs_StartPos = get_abs_tr_loc(rel_StartPos, StartPos_e_id, exonBlocks)

    rel_EndPos = rel_StartPos + readLen - 1 #inclusive
    EndPos_e_id = get_exon_id_relTree(rel_EndPos, exonTree)
    abs_EndPos = get_abs_tr_loc(rel_EndPos, EndPos_e_id, exonBlocks)

    #if tr=='ENST00000562759.1' and abs_StartPos==80191248 \
    #   or tr=='ENST00000563800.1' and abs_StartPos==83296089 \
    #if tr=='ENST00000562869.1' and abs_StartPos==74782029:
    #   pdb.set_trace()

    if StartPos_e_id!=-1 and EndPos_e_id!=-1:
        read_block_lens = []
        read_block_starts = []
        for j in xrange(StartPos_e_id, EndPos_e_id+1):
            curr_block_stt = exonBlocks[j][0]
            curr_block_stp = exonBlocks[j][1]
            curr_read_block_len = min(curr_block_stp, abs_EndPos+1)-max(curr_block_stt, abs_StartPos)
            #pdb.set_trace()
            read_block_lens.append(curr_read_block_len)
            read_block_starts.append(max(curr_block_stt,abs_StartPos)-abs_StartPos)

        read_stp = abs_EndPos+1 #max(exonBlocks[EndPos_e_id][0], i)+read_block_lens[-1] #exclusive
        read_line += chrom + '\t'
        read_line += str(abs_StartPos) + '\t'
        read_line += str(read_stp) + '\t'
        read_line += '%s_%s_%d_%d_%d'%(chrom, tr, StartPos_e_id, EndPos_e_id, abs_StartPos) + '\t'
        read_line += '0\t'
        read_line += '+\t'
        read_line += str(abs_StartPos) + '\t'
        read_line += str(read_stp) + '\t'
        read_line += '0\t'
        read_line += str(len(read_block_lens))+'\t'
        read_line += ','.join([str(bl) for bl in read_block_lens])+',\t'
        read_line += ','.join([str(bs) for bs in read_block_starts])+',\n'

    else:
        pass #pdb.set_trace()

    #pdb.set_trace()

    return read_line

'''
usage:
python sim_data_generator.py --readBed_generation_at_sel_snps
                             -s snp_file
                             -b tr_sorted_bed_file
                             -o output_read_bed
                             -L readLen
                             -c chrom
                             [-o2 log]

description:

generate reads (+ direction) so that each of selected snps (e.g. at REL location x of a covering transcript T) is covered by reads 
sampled from locations [x-(readLen-1), x] of T. 

If a snp has some read (head & tail pos) sampled from [x-(readLen-1),x] to be outside the transcript, those reads are discarded, 
and output related snp & transcript info info log file.

Finally, unique read id will be enforced

- log: 
col-0: snp (1-based)
col-1 col-2 etc: each col has: trid,#_bases_left_of_snp,#_bases_right_of_snp (s.t. one of #_left or #_right < readLen-1; # left + # right has the largest window size ever seen)

in case the snp is covered by no read (probably the snp is in the transcript with len < readLen), 
this snp & related tr info (list of [trid, L_left, L_right, L_left+L_right]) is also in log, appended with (*)
'''
def readBed_generation_at_sel_snps(args):

    snp_file = args[args.index('-s')+1]
    tr_sorted_bed_file = args[args.index('-b')+1]
    output_read_bed = args[args.index('-o')+1]
    readLen = int(args[args.index('-L')+1])
    chrom = args[args.index('-c')+1]
    if '-o2' in args:
        output_log = args[args.index('-o2')+1]
    else:
        output_log = output_read_bed + '.log'

    f_output_read = open(output_read_bed, 'w')
    f_output_log = open(output_log, 'w')

    #load snps
    snps = load_snps(snp_file)
    #pdb.set_trace()

    #parse bed
    [tree_exon, dic_tr_exonTree_exonBlocks] = parse_bed(tr_sorted_bed_file)##
    #pdb.set_trace()

    #process each snp
    for k, v in snps.items():
        gPos = k-1 #0-based
        exon_intervals = sorted(tree_exon[gPos])
        if len(exon_intervals)==0:
            print('snp not covered by exon -- unexpected')
            pdb.set_trace()
        else:
            trInfo_list = []
            for exon_interval in exon_intervals:
                e_stt = exon_interval.begin
                e_stp = exon_interval.end
                trs = exon_interval.data
                for tr in trs:
                    tokens = tr.split(',')
                    trid = tokens[0]
                    L_left = int(tokens[1])+gPos-e_stt
                    L_right = int(tokens[2])+e_stp-gPos-1
                    trInfo_list.append([trid, L_left, L_right, L_left+L_right])
            longest_tr, num_left_bases = sel_longest_tr(trInfo_list, k, f_output_log, readLen)##
            cnt = 0
            for i in xrange(num_left_bases+1): # sample read at pos rel_gPos-i on longest_tr
                read_line = sample_a_read(longest_tr, dic_tr_exonTree_exonBlocks, gPos, i, readLen, chrom)##
                if read_line != '':
                    f_output_read.write(read_line)
                    cnt += 1
                else:
                    #pdb.set_trace()
                    pass;
            if cnt==0:
                f_output_log.write('%d\t%s\t(*)\n'%(k,str(trInfo_list)))
                #pdb.set_trace()

    #pdb.set_trace()
    f_output_read.close()
    f_output_log.close()

    #enforce unique read id
    enforce_unique_readID_bed(output_read_bed)##
    #pdb.set_trace()

    return

'''
example:

python sim_data_generator.py --read_generation -g /data1/shunfu1/SNPCalling/snp20_reads100k_10/Tar_m.txt 
                             -b /data1/shunfu1/SNPCalling/snp20_reads100k_10/hg19_chr15-UCSC-sorted.bed
                             -O /data1/shunfu1/SNPCalling/snp20_reads100k_10_abSNPcode/reads_N100k_L100_Err0 
                             -n 100000 -l 100 -r 0 
                             --suffix _m --toFq
'''
def read_generation(args):

    sim_reads_g_b(args)

    #add suffix
    out_dir = args[args.index('-O')+1]

    suf = args[args.index('--suffix')+1]      
    
    src_dst_pairs = []

    reads = '%s/reads.fa'%(out_dir); readsNew = '%s/reads%s.fa'%(out_dir, suf)
    src_dst_pairs.append([reads, readsNew])
    
    if '--exp_path' not in args:
        exp = '%s/intermediate/exp.txt'%(out_dir); expNew = '%s/intermediate/exp%s.txt'%(out_dir, suf)
        src_dst_pairs.append([exp, expNew])

    reads_bed = '%s/intermediate/reads.bed'%(out_dir); reads_bedNew = '%s/intermediate/reads%s.bed'%(out_dir, suf)
    src_dst_pairs.append([reads_bed, reads_bedNew])

    for i in range(len(src_dst_pairs)):
        run_cmd('mv %s %s'%(src_dst_pairs[i][0], src_dst_pairs[i][1]))

    #fa to fq
    readsFq = '%s/reads%s.fq'%(out_dir, suf)
    run_cmd( 'perl ' + FA2FQ_address + ' ' + readsNew + ' > '  + readsFq )

    return

def merge_reads(args):

    reads_m = args[args.index('-m')+1]
    reads_p = args[args.index('-p')+1]
    merged_reads = args[args.index('-o')+1]

    run_cmd('cat '  + reads_m + ' ' + reads_p + ' > ' + merged_reads)

    if '--uniqID' in args:
        enforce_unique_readID(merged_reads, flag=True)
        
    return

'''
usage:

#filter input_snp_file into output_snp_file, such that:
# - snps are restricted by region_file

python sim_data_generator.py --sel_snps
                             -i input_snp_file
                             -o output_snp_file
                             -e region_file

#mark or filter snps
#- if --no_homozygous:
#  homozygous snps will not be output
#  from snp_m.txt and snp_p.txt, output snp_m_noHomo.txt and snp_p_noHomo.txt
#- if no --no_homozygous (default)
#  homozygous will be marked as: gPos rB --> tB (*)
#  from snp_m.txt and snp_p.txt, output snp_m_markHomo.txt and snp_p_markHomo.txt

python sim_data_generator.py --mark_homozygous -m snp_m file -p snp_p file
                                               [-m2 snp_m2_file] [-p2 snp_p2_file]
                                               [--no_homozygous]
                                               [--outputHomo snp_homo_file]


# we collect exp vals from old_exp_file, and reasign them from high to low to the transcripts that contain highest snps to lowest snps

python sim_data_generator.py --reasign_exp 
                             -s snp_file
                             -b sorted_bed_file
                             -e old_exp_file
                             -o new_exp_file

#generate target genome (m or p) w/ extracted snp info

python sim_data_generator.py --gen_genome_of_snps -r ref_genome -c target_chr -s snp_file -t path/to/target_genome


# use RNASeqReadSimulator to generate reads per target allele
#
# we re-use the simulator written in multi shannon
# for snp calling purpose, we need to add suffix (e.g. _m, _p) and convert fa to fq
#
# note:
#
# .fa, \.sorted.bed
#                               --> out_dir/intermediate/exp[_suffix].txt (if --exp_path unspecified), reads[_suffix].bed 
#                               --> out_dir/reads[_suffix].[fa or fq] (SE)
# 
# .sorted.bed needs 1st line to be "# trNum (trNum) avgTrLen (avgTrLen)" for '-c readCoverage'
#

python sim_data_generator.py --read_generation -g genomeFile -b trBedFile -O out_dir
                             (-n numReads or -c readCoverage) -l readLength -r errRate
                             --suffix suf --toFq
                             [--exp_path exp_path]

# pool reads sampled from maternal and paternal alleles together
#

python sim_data_generator.py --merge_reads -m reads_m.fq -p reads_p.fq -o merged_reads.fq [--uniqID]

'''
if __name__ == "__main__":

    args = sys.argv

    # generate simulated snps (exp --> snps and tar), as in batch_run_case1plus6
    if '--gen_sim_exp_snp_tar' in args:
        gen_sim_exp_snp_tar(args)
    # select snps (true snps --> restrict to snps of interest e.g. coding regions)
    elif '--sel_snps' in args:
        sel_snps(args)
    # select snps s.t. the input snps don't contain uncovered snps (indicated by an auxillary file)
    elif '--sel_snps_covered' in args:
        sel_snps_covered(args)
    #from snp_m.txt and snp_p.txt, output snp_m_markHomo.txt and snp_p_markHomo.txt
    elif '--mark_homozygous' in args: 
        mark_homozygous(args)
    #generate coverage file
    elif '--gen_coverage' in args:
        gen_coverage(args)
    #find snp and its coverage
    elif '--snp_cov' in args:
        snp_cov(args)
    #find snp and whether it's covered by reads -- not efficient, replaced by snp_read_cov1
    #elif '--snp_read_cov' in args:
    #    snp_read_cov(args)
    elif '--snp_read_cov1' in args:
        snp_read_cov1(args)
    #re-asign exp file so that snp contained transcript gets high expression (e.g. check multiple alignments)
    elif '--reasign_exp' in args:
        reasign_exp(args)
    #generate target individual genome
    elif '--gen_genome_of_snps' in args:
        gen_genome_of_snps(args)
    # generate reads (+ direction) so that selected snps are covered
    elif '--readBed_generation_at_sel_snps' in args:
        readBed_generation_at_sel_snps(args)
    # generate simulated reads
    elif '--read_generation' in args:
        read_generation(args)
    elif '--merge_reads' in args:
        merge_reads(args)
    else:
        main()