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
            transform = None

            for scan in patients[key]["scan"] :
                img = sitk.ReadImage(scan)
                for matrix in patients[key]["matrix"] :
                    try :
                        transform = sitk.ReadTransform(matrix)
                    except:
                        print(f"Can't read the matrix : {matrix}")

                
                    resampled = ResampleImage(img,transform)

                    outpath = scan.replace(input_path,out_path)

                    if not os.path.exists(os.path.dirname(outpath)):
                        os.makedirs(os.path.dirname(outpath))

                    matrix_name = os.path.basename(matrix).split('.tfm')[0].split(key)[1]
                    sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+suffix+matrix_name+'.nii.gz')
                
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
        files = [f for f in files]

        for i in range(len(files)):
            file = files[i]

            file_pat = os.path.basename(file).split('_Seg')[0].split('_seg')[0].split('_Scan')[0].split('_scan')[0].split('_Or')[0].split('_OR')[0].split('_MAND')[0].split('_MD')[0].split('_MAX')[0].split('_MX')[0].split('_CB')[0].split('_lm')[0].split('_Cl')[0].split('.')[0].replace('.','')
            for i in range(50):
                file_pat=file_pat.split('_T'+str(i))[0]

            if file_pat not in patients.keys():
                patients[file_pat] = {}
                patients[file_pat]['scan'] = []
                patients[file_pat]['matrix'] = []
            patients[file_pat]['scan'].append(file)
    
    else : 
        files = [file_path]
        file_pat = os.path.basename(file_path).split('_Seg')[0].split('_seg')[0].split('_Scan')[0].split('_scan')[0].split('_Or')[0].split('_OR')[0].split('_MAND')[0].split('_MD')[0].split('_MAX')[0].split('_MX')[0].split('_CB')[0].split('_lm')[0].split('_T2')[0].split('_T1')[0].split('_Cl')[0].split('.')[0].replace('.','')
        for i in range(50):
            file_pat=file_pat.split('_T'+str(i))[0]

        if file_pat not in patients.keys():
            patients[file_pat] = {}
            patients[file_pat]['scan'] = []
            patients[file_pat]['matrix'] = []
        patients[file_pat]['scan'].append(file_path)    

    
    if Path(matrix_path).is_dir():
        matrixes = search(matrix_path,".tfm")['.tfm']
        matrixes = [f for f in matrixes]
            
        for i in range(len(matrixes)):
            matrix = matrixes[i]
            matrix_pat = os.path.basename(matrix).split("_Right")[0].split("_right")[0].split("_Left")[0].split("left")[0].replace('.','')

            for i in range(50):
                matrix_pat=matrix_pat.split('_T'+str(i))[0]

            if matrix_pat in patients.keys():
                patients[matrix_pat]['matrix'].append(matrix)

    else : 
        for key in patients.keys() :
            patients[key]['matrix'].append(matrix)
    

    return patients,len(files)