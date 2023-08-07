import SimpleITK as sitk
import os,time
from tqdm import tqdm
from Apply_matrix_utils.General_tools import search



def CheckSharedList(shared_list,maxvalue):
    for i in tqdm(range(maxvalue)):
        while sum(shared_list) < i+1:
            time.sleep(1)

def ResampleImage(image, transform):
    '''
    Resample image using SimpleITK
    
    Parameters
    ----------
    image : SimpleITK.Image
        Image to be resampled
    target : SimpleITK.Image
        Target image
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

def ApplyMatrixGZ(patients,keys,input_path, out_path, num_worker=0, shared_list=None,logPath=None,idx=0):

    for key in keys:
        try:
                
            img = sitk.ReadImage(patients[key]["scan"])

            transform_right = None
            transform_left = None

            try :
                transform_right = sitk.ReadTransform(patients[key]["mat_right"])
            except:
                print("Patient {key} not have right matrix files")

            try :
                transform_left = sitk.ReadTransform(patients[key]["mat_left"])
            except:
                print("Patient {key} not have left matrix files")
            

            if transform_right!=None :
                resampled = ResampleImage(img,transform_right)
                outpath = patients[key]['scan'].replace(input_path,out_path)
                if not os.path.exists(os.path.dirname(outpath)):
                    os.makedirs(os.path.dirname(outpath))

                sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+f'Scan_Right_Or.nii.gz')
            
            if transform_left!=None : 
                resampled = ResampleImage(img,transform_left)
                outpath = patients[key]['scan'].replace(input_path,out_path)
                if not os.path.exists(os.path.dirname(outpath)):
                    os.makedirs(os.path.dirname(outpath))
                sitk.WriteImage(resampled,outpath.split('.nii.gz')[0]+f'Scan_Left_Or.nii.gz')

            with open(logPath,'r+') as log_f :
                log_f.write(str(idx))
            idx+=1


            
            # WriteJson(ldmk,"/home/luciacev/Desktop/Luc_Anchling/DATA/ALI_CBCT/Resampled/"+patient+".json")
            shared_list[num_worker] += 1
        except KeyError:
            print(f"Patient {key} not have either scan or matrix")
            shared_list[num_worker] += 1
            continue


def GetPatients(file_path,matrix_path):
    patients = {}

    files = search(file_path,".nii.gz")['.nii.gz']
    files = [f for f in files if 'T1' in f]
    
    matrixes = search(matrix_path,".tfm")['.tfm']
    matrixes = [f for f in matrixes]

    for i in range(len(files)):
        file = files[i]

        file_pat = os.path.basename(file).split("_T1")[0].replace('.','')

        if file_pat not in patients.keys():
            patients[file_pat] = {}
        patients[file_pat]['scan'] = file
        
    for i in range(len(matrixes)):
        matrix = matrixes[i]
        matrix_pat = os.path.basename(matrix).split("_T1")[0].split("_Right")[0].split("_right")[0].split("_Left")[0].split("left")[0].replace('.','')
        if matrix_pat in patients.keys():
            # patients[matrix_pat] = {}

            
            if 'left' in matrix.lower():
                patients[matrix_pat]['mat_left'] = matrix
                
            if 'right' in matrix.lower():
                patients[matrix_pat]['mat_right'] = matrix


    return patients,len(files)