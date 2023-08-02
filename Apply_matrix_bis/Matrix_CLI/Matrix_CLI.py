import argparse





def main(args):

    pass


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()


    parser.add_argument('path_patient_intput',type=str)
    parser.add_argument('path_matrix_intput',type=str)
    parser.add_argument("suffix",type=str)
    parser.add_argument('path_patient_output',type=str)


    args = parser.parse_args()


    main(args)