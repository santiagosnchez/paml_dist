# PamlDist.py
# Wrapper for PAML to get dN/dS estimates

import os
import sys
from multiprocessing import Pool, Lock, Process
from shutil import rmtree

def check_install():
    o = os.popen("yn00 2> /dev/null")
    return(o.readlines())

def cmd_constructor():
    ctl = """seqfile = infile
outfile = outfile
verbose = 0
icode = 0
weighting = 1
commonf3x4 = 0"""
    cmd = "echo \'" + ctl + "\'" + " | yn00 /dev/stdin &> /dev/null"
    return(cmd)

def fix_codons(seq):
    for i in range(0,len(seq),3):
        if "N" in seq[i:i+3]:
            seq = seq[:i] + "---" + seq[(i+3):]
        if "-" in seq[i:i+3]:
            seq = seq[:i] + "---" + seq[(i+3):]
        if "TGA" == seq[i:i+3] or "TAA" == seq[i:i+3] or "TAG" == seq[i:i+3]:
            seq = seq[:i] + "---" + seq[(i+3):]
    return(seq)

def retrieve_from_output():
    with open("2YN.dN","r") as f:
        dn = f.readlines()
        dn = dn[2].split(" ")[-1].rstrip()
    with open("2YN.dS","r") as f:
        ds = f.readlines()
        ds = ds[2].split(" ")[-1].rstrip()
    return(dn,ds)

def single_output_to_screen(lock, seq1, seq2, dn, ds):
     lock.acquire()
     try:
         print(seq1, seq2, dn, ds, sep=",")
     finally:
         lock.release()

def masterfn(lock, seqs):
    pid = os.getpid()
    dirname = "tmp."+str(pid)
    os.makedirs(dirname)
    os.chdir(dirname)
    for i in range(1,len(seqs),2): seqs[i] = fix_codons(seqs[i].rstrip()) + "\n"
    with open("infile","w") as f:
        for i in seqs: f.write(i)
    cmd = cmd_constructor()
    sig = os.system(cmd)
    if sig == 0:
        dn,ds = retrieve_from_output()
        seq1 = seqs[0][1:].rstrip()
        seq2 = seqs[2][1:].rstrip()
        single_output_to_screen(lock, seq1, seq2, dn, ds)
    os.chdir("../")
    rmtree(dirname)

if __name__ == "__main__":
    o = check_install()
    if "paml version" not in o[0]:
        print("PAML is not properly install or accessible through the $PATH")
        sys.exit()
    lock = Lock()
    with open(sys.argv[1],"r") as f:
        lines = f.readlines()
    for i in range(0,len(lines),4):
        seqs = lines[i:i+4]
        p = Process(target=masterfn, args=(lock, seqs))
        p.start()
    p.join()
