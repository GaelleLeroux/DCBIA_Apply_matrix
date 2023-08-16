#!/usr/bin/env python-real

import argparse
import os
import sys
from pathlib import Path
import multiprocessing as mp
import numpy as np
import Apply_matrix_utils as amu


def main(args):
    
    path_patient_input = Path(args.path_patient_intput)
    path_matrix_intput = Path(args.path_matrix_intput)
    path_patient_output = Path(args.path_patient_output)

    idx = 0

    with open(args.logPath,'w') as log_f:
        # clear log file
        log_f.truncate(0)

    ## Apply matrix on files != .nii.gz 
    ## Use the function in VTK_tools to apply the matrix on each files and saved them
    if path_patient_input.is_file() and path_matrix_intput.is_file():
        fname, extension = os.path.splitext(os.path.basename(args.path_patient_intput))
        if extension == ".vtk" or extension == ".vtp" or extension == ".stl" or extension == ".off" or extension == ".obj" :
            surf = amu.ReadSurf(args.path_patient_intput)
            matrix = amu.ReadMatrix(args.path_matrix_intput)
            new_surf=amu.TransformSurf(surf,matrix)
            amu.WriteSurf(new_surf,args.path_patient_output,args.path_patient_intput,args.suffix)

    elif path_patient_input.is_dir() and path_matrix_intput.is_dir() : # folder option
            dico_patient=amu.search(args.path_patient_intput,'.vtk','.vtp','.stl','.off','.obj')
            dico_matrix=amu.search(args.path_matrix_intput,'.npy','.h5','.tfm','.mat','.txt')
            dico_link={}
            for list_value_patient in dico_patient.values():
                for filename_patient in list_value_patient:
                    name = (os.path.basename(filename_patient)).split('_Seg')[0].split('_seg')[0].split('_Scan')[0].split('_scan')[0].split('_Or')[0].split('_OR')[0].split('_MAND')[0].split('_MD')[0].split('_MAX')[0].split('_MX')[0].split('_CB')[0].split('_lm')[0].split('_T2')[0].split('_T1')[0].split('_Cl')[0].split('.')[0]
                    for list_value_matrix in dico_matrix.values():
                        for filename_matrix in list_value_matrix:
                            name_tempo=(os.path.basename(filename_matrix)).split('_Left')[0].split('_left')[0].split('_Right')[0].split('_right')[0].split('_T1')[0].split('_T2')[0].split('_MA')[0]
                            if name_tempo==name:
                                if filename_patient in dico_link :
                                    dico_link[filename_patient].append(filename_matrix)
                                else :
                                    dico_link[filename_patient]= [filename_matrix]
                                    
            for filename_patient,list_matrix in dico_link.items():
                surf = amu.ReadSurf(os.path.join(args.path_patient_intput,filename_patient))
                output_path = filename_patient.replace(os.path.normpath(args.path_patient_intput),os.path.normpath(args.path_patient_output))
                for filename_matrix in list_matrix :
                    matrix = amu.ReadMatrix(os.path.join(args.path_matrix_intput,filename_matrix))
                    new_surf=amu.TransformSurf(surf,matrix)
                
                    if 'left' in filename_matrix.lower():
                        amu.WriteSurf(new_surf,output_path,filename_patient,"_Left"+args.suffix)
                        
                    if 'right' in filename_matrix.lower():
                        amu.WriteSurf(new_surf,output_path,filename_patient,"_Right"+args.suffix)
                        
                with open(args.logPath,'r+') as log_f :
                    log_f.write(str(idx))
                idx+=1


    ## Apply matrix on files == .nii.gz 
    ## Call the function in GZ_tools to Apply the matrixs and to save the new files
    ## The update of the file log for the progress bare is in the function ApplyMatrixGZ
    patients,nb_files = amu.GetPatients(args.path_patient_intput,args.path_matrix_intput)
    nb_worker = 6
    nb_scan_done = mp.Manager().list([0 for i in range(nb_worker)])
    idxProcess = mp.Value('i',idx)
    check = mp.Process(target=amu.CheckSharedList,args=(nb_scan_done,nb_files,args.logPath,idxProcess)) 
    check.start()

    splits = np.array_split(list(patients.keys()),nb_worker)
    
    if path_patient_input.is_dir() : 
        processess = [mp.Process(target=amu.ApplyMatrixGZ,args=(patients,keys,args.path_patient_intput,args.path_patient_output,i,nb_scan_done,args.logPath,idx,args.suffix)) for i,keys in enumerate(splits)]
    
    elif path_patient_input.is_file() : 
        processess = [mp.Process(target=amu.ApplyMatrixGZ,args=(patients,keys,os.path.dirname(args.path_patient_intput),args.path_patient_output,i,nb_scan_done,args.logPath,idx,args.suffix)) for i,keys in enumerate(splits)]    

    for proc in processess: proc.start()
    for proc in processess: proc.join()
    check.join()

    print("Applied matrix with success")








if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()

    
    parser.add_argument('path_patient_intput',type=str,help="choose a patient")
    parser.add_argument('path_matrix_intput',type=str,help="choose a matrix")
    parser.add_argument('path_patient_output',type=str,help="choose an output")
    parser.add_argument("suffix",type=str,help="choose a suffix")
    parser.add_argument("logPath",type=str, help="logpath")
    


    args = parser.parse_args()


    main(args)