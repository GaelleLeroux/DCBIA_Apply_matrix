import SimpleITK as sitk
import os,time
from tqdm import tqdm
from Apply_matrix_utils.General_tools import search
import numpy as np
from pathlib import Path



def CheckSharedList(shared_list,maxvalue,logPath,idxProcess):
    for i in tqdm(range(maxvalue)):
        while sum(shared_list) < i+1:
            time.sleep(0.1)
        with open(logPath,'r+') as log_f :
            idxProcess.acquire()
            log_f.write(str(idxProcess.value))
        idxProcess.value +=1
        # print(f"idxProcess.value : {idxProcess.value}")
        idxProcess.release()
        time.sleep(0.5)


def CenterImage(img):

    T = - np.array(img.TransformContinuousIndexToPhysicalPoint(np.array(img.GetSize())/2.0))
    translation = sitk.TranslationTransform(3)
    translation.SetOffset(T.tolist())
    img_trans = ResampleImage(img,translation.GetInverse())
    return img_trans

def ResampleImage(image, transform):
    '''
    Resample image using SimpleITK
    
    Parameters
    ----------
    image : SimpleITK.Image
        Image to be resampled
    transform : SimpleITK transform
        Transform to be applied to the image.
        
    Returns
    -------
    SimpleITK image
        Resampled image.
    '''
    # Create resampler
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(image)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(0)
    resampler.SetTransform(transform)

    # Resample image
    resampled_image = resampler.Execute(image)

    return resampled_image

def ApplyMatrixGZ(patients,keys,input_path, out_path, num_worker=0, shared_list=None,logPath=None,idx=0,suffix=""):
    for key in keys:
        try:
            
        
            transform_right = None
            transform_left = None
            transform_one_mat = None

            try :
                transform_right = sitk.ReadTransform(patients[key]["mat_right"])
            except:
                print(f"Patient {key} not have right matrix files")

            try :
                transform_left = sitk.ReadTransform(patients[key]["mat_left"])
            except:
                print(f"Patient {key} not have left matrix files")

            if transform_left==None and transform_right==None : 
                try :
                    transform_one_mat = sitk.ReadTransform(patients[key]["one_mat"])
                except:
                    print(f"Patient {key} not have one_mat files")
            
            for scan in patients[key]["scan"] :
                img = sitk.ReadImage(scan)
                # img = CenterImage(img)
                # outpath = scan.replace(input_path,out_path)
                # sitk.WriteImage(img,outpath.split('.nii.gz')[0]+f'_centered_'+suffix+'.nii.gz')

                if transform_right!=None and 'LM' not in os.path.basename(scan):
                    resampled = ResampleImage(img,transform_right)
                    outpath = scan.replace(input_path,out_path)
                    if not os.path.exists(os.path.dirname(outpath)):
                        os.makedirs(os.path.dirname(outpath))
                    sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+f'_Right_Or'+suffix+'.nii.gz')
                
                if transform_left!=None and 'LM' in os.path.basename(scan): 
                    resampled = ResampleImage(img,transform_left)
                    outpath = scan.replace(input_path,out_path)
                    if not os.path.exists(os.path.dirname(outpath)):
                        os.makedirs(os.path.dirname(outpath))
                    sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+f'_Left_Or'+suffix+'.nii.gz')

                if transform_one_mat!=None : 
                    resampled = ResampleImage(img,transform_one_mat)
                    outpath = scan.replace(input_path,out_path)
                    if not os.path.exists(os.path.dirname(outpath)):
                        os.makedirs(os.path.dirname(outpath))
                    sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+f'_Or'+suffix+'.nii.gz')
                
                shared_list[num_worker] += 1

           
          
        except KeyError:
            print(f"Patient {key} not have either scan or matrix")
            shared_list[num_worker] += 1
            continue

        time.sleep(0.5)



def GetPatients(file_path,matrix_path):
    patients = {}

    if Path(file_path).is_dir():
        files = search(file_path,".nii.gz")['.nii.gz']
        files = [f for f in files if 'T1' in f]

        for i in range(len(files)):
            file = files[i]

            file_pat = os.path.basename(file).split("_T1")[0].replace('.','')

            if file_pat not in patients.keys():
                patients[file_pat] = {}
                patients[file_pat]['scan'] = []
            patients[file_pat]['scan'].append(file)
    
    else : 
        files = [file_path]
        file_pat = os.path.basename(file_path).split("_T1")[0].replace('.','')

        if file_pat not in patients.keys():
            patients[file_pat] = {}
            patients[file_pat]['scan'] = []
        patients[file_pat]['scan'].append(file_path)    

    
    if Path(matrix_path).is_dir():
        matrixes = search(matrix_path,".tfm")['.tfm']
        matrixes = [f for f in matrixes]
            
        for i in range(len(matrixes)):
            matrix = matrixes[i]
            matrix_pat = os.path.basename(matrix).split("_T1")[0].split("_Right")[0].split("_right")[0].split("_Left")[0].split("left")[0].replace('.','')
            if matrix_pat in patients.keys():
                # patients[matrix_pat] = {}

                
                if 'left' in matrix.lower():
                    patients[matrix_pat]['mat_left'] = matrix
                    
                if 'right' in matrix.lower():
                    patients[matrix_pat]['mat_right'] = matrix

    else : 
        for key in patients.keys() :
            patients[key]['one_mat'] = matrix_path
            

    return patients,len(files)