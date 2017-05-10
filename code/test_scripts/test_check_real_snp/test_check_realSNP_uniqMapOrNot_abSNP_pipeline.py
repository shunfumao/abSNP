import pdb
from old_code.util import run_cmd

#use prev data (e.g. fa, snps, exp, target alleles), to generate new reads and do snp calls by abSNP code

def main():

    srcDir = '/data1/shunfu1/SNPCalling/data_real_HeteSNPsCodingRegion/'
    dstDir = '/data1/shunfu1/SNPCalling/data_real_HeteSNPsCodingRegion/SNPs_Filt/'
    code_folder = 'old_code'

    num_p = 20

    L = 100
    errRate = 0.00
    
    readsLabel = 'reads_CoverSNPs_L%s_Err%.2f'%(L, errRate)
    
    chrom = 'chr15'

    refGenome = '%s/%s.fa'%(srcDir, chrom)
    
    trBedFile = '%s/annotation/gencode.v19.annotation.target.chr15.sorted.bed'%srcDir
    gtfFile = '%s/annotation/gencode.v19.annotation.gtf'%srcDir     

    true_SNP = ['%s/SNPs_Filt/chr15_snp_m_codingRegion_noHomo_allCoveredByReads.txt'%srcDir, 
                '%s/SNPs_Filt/chr15_snp_p_codingRegion_noHomo_allCoveredByReads.txt'%srcDir]

    genomeFile = ['%s/SNPs_Filt/chr15_m_HeteFiltSNPs.fa'%srcDir,
                  '%s/SNPs_Filt/chr15_p_HeteFiltSNPs.fa'%srcDir]
    
    callerThre = 1 # snp call

    filt3_sameAb = 1 # filt same ab
    rocT = [0.0, 1.0] # filt poisson

    clear_intFiles = 1 #clear intermediate split sam, count_x and count_y etc during para operations

    #### auto configuration

    readFile = '%s/read_merged_SNPs_covered.fq'%(dstDir)
    rsem_out_dir = '%s/%s/rsem/'%(dstDir, readsLabel)
    snp_out_dir = '%s/%s/snp_res/T%d'%(dstDir, readsLabel, callerThre)

    exon_address = '%s/exon.txt'%rsem_out_dir #intermediate output
    rsemCov = '%s/rsemCoverage.txt'%rsem_out_dir #intermediate output   

    rsemPrefixName = chrom
    rsemGenomePrefix = '%s/%s'%(rsem_out_dir, rsemPrefixName)
    tbam = '%s.transcript.bam'%rsemGenomePrefix
    gbam = '%s.genome.bam'%rsemGenomePrefix
    gsam = '%s.genome.sorted_n.sam'%rsemGenomePrefix    

    suf = ['_m', '_p']
    
    samFn = '%s.genome.sorted_n'%rsemPrefixName
    cntFile = '%s/split_sorted_sam_%s/count_y/count_%s.txt'%(rsem_out_dir, samFn, samFn)
    cntFileAltInfo = '%s/split_sorted_sam_%s/count_y_altInfo/count_%s_altInfo.txt'%(rsem_out_dir, samFn, samFn)

    rocT_str = ','.join(['%.2f'%v for v in rocT])

    snp_res = '%s/caller_output_snp_found_%s_T%d_para.txt'%(snp_out_dir, samFn, callerThre)
    snp_res_filt = []
    for rocT_val in rocT:
        tmp_snp_res_filt_file = '%s/caller_output_snp_found_%s_T%d_para_rocT_%.2f.txt'%(snp_out_dir, samFn, callerThre, rocT_val)
        snp_res_filt.append(tmp_snp_res_filt_file)

    pdb.set_trace()

    #quantification

    cmd = 'python quantification.py --RSEM1 --ref %s -r %s -g %s -O %s -p %s'% \
          (refGenome, readFile, gtfFile, rsem_out_dir, rsemPrefixName)
    #pdb.set_trace()
    #run_cmd(cmd)

    rsemIsoformsResults = '%s/%s.isoforms.results'%(rsem_out_dir, rsemPrefixName)

    cmd = 'python quantification.py --rsemCoverage -i %s -b %s -e %s -c %s -L %d'% \
          (rsemIsoformsResults, trBedFile, exon_address, rsemCov, L)
    pdb.set_trace()
    run_cmd(cmd)

    cmd = 'python quantification.py --tbam2gbam -p %s -t %s -g %s'% \
          (rsemGenomePrefix, tbam, gbam)
    pdb.set_trace()
    run_cmd(cmd)

    #snp call
    cmd = 'python snp_call_para.py  -r %s '%refGenome+\
                                   '-c %s '%rsemCov+\
                                   '-s %s '%gsam+\
                                   '-O %s '%snp_out_dir+\
                                   '-T %d '%callerThre+\
                                   '-p %d '%num_p+\
                                   '--dupRun 0 '+\
                                   '--code_folder %s '%code_folder+\
                                   '--filt3_sameAb %d '%filt3_sameAb+\
                                   '--filt3_rocT %s '%rocT_str+\
                                   '--clear_intFiles %d'%clear_intFiles
    pdb.set_trace()
    run_cmd(cmd)

    #evaluator
    for i in range(len(rocT)):
        snpResSubDir = '%s/nonFilt_vs_filt3rocT%.2f/'%(snp_out_dir, rocT[i])
        run_cmd('mkdir -p %s'%snpResSubDir)

        snpLog = '%s/snpLog.txt'%(snpResSubDir)
        snpSum = '%s/snpSum.txt'%(snpResSubDir)
        snpSum2 = '%s/snpSum2.txt'%(snpResSubDir)

        cmd = 'python evaluator.py --loadSnpInfo '+\
                                  '-L1 m -F1 %s '%true_SNP[0]+\
                                  '-L2 p -F2 %s '%true_SNP[1]+\
                                  '-L3 O -F3 %s '%snp_res+\
                                  '-L4 G -F4 %s '%snp_res_filt[i]+\
                                  '-C1 %s '%cntFile+\
                                  '-C2 %s '%cntFileAltInfo+\
                                  '--snpLog %s '%snpLog+\
                                  '--snpSum %s '%snpSum+\
                                  '--snpSum2 %s '%snpSum2
        pdb.set_trace()
        run_cmd(cmd)

    '''
    if clear_intFiles==1:
        cmd = 'rm %s'%cntFile
        run_cmd(cmd)

        cmd = 'rm %s'%cntFileAltInfo
        run_cmd(cmd)
    '''

    return

if __name__ == "__main__":

    main()