import os
import sys
import shutil
import importlib.util
from os import path
import glob
import pandas as pd
import numpy as np
from os.path import dirname, realpath
from runpy import run_path
import copy
import re
from itertools import product

from Molecule import Molecule

pd.set_option("display.max_columns", 15)

np.set_printoptions(precision=4)

# =======================
# Database Specifications
# =======================

# High and low levels of theory
# Available: "CCSD_T_TZ", "CCSD_T_DZ", "B3LYP_6-31G_2df,p_"
h_theory = ["CCSD_T_TZ"]
l_theory = ["CCSD_T_DZ", "B3LYP_6-31G_2df,p_"]
# l_theory = ["CCSD_T_DZ"]
# cma1_energy_regexes = ["\(T\) total energy\s+(\-\d+\.\d+)","Grab this energy (\-\d+\.\d+)"]
cma1_energy_regexes = ["\(T\)\s*t?o?t?a?l? energy\s+(\-\d+\.\d+)","Grab this energy (\-\d+\.\d+)"]
# cma1_energy_regexes = ["\(T\)\s*t?o?t?a?l? energy\s+(\-\d+\.\d+)",[r"Total Gradient",r"tstop"]]
cma1_success_regexes = ["Variable memory released","beer"]
#l_theory = ["B3LYP_6-31G_2df,p_"]
combos = list(product(h_theory,l_theory))

# Coordinates types to use
# Available: "Nattys", "Redundant", "ZMAT" (not yet tho)
coord_type = ["Nattys", "Redundant"]

# Specify paths to grab data from
# Options: '/1_Closed_Shell', '/1_Linear', '/1*', '/2_Open_Shell', '/2_Linear', '/2*'
#paths = ['/2_Open_Shell']
# paths = ['/1_Closed_Shell']
paths = ['/1_Closed_Shell','/2_Open_Shell']

# Various output control statements
# n = 5                   # Number of CMA2 corrections (n = 0 -> CMA0)
n = 0                   # Number of CMA2 corrections (n = 0 -> CMA0)
cma1 = True             # Run CMA1 instead of CMA0
#cma1 = False           # Run CMA1 instead of CMA0
csv = True              # Generate database .csv file
SI = True               # Generate LaTeX SI file
compute_all = True      # run calculations for all or a select few
# compute_all = False      # run calculations for all or a select few
off_diag_bands = False  # (CMA2/3 ONLY) If set to true, "n" off-diag bands selected, if false, "n" largest fc will be selected
deriv_level = 0         # (CMA1) if 0, compute initial hessian by singlepoints. If 1, compute initial hessian with findif of gradients

# =====================
# Some useful functions
# =====================

def freq_diff(F1, F2):
    return F1 - F2

def averages(F_diff):
    return np.average(F_diff), np.average(abs(F_diff)) 

def stdev(F_diff):
    return np.std(F_diff)

def highlight_greaterthan(x):
    print('this is x.Ref__Redundant')
    print(x.Ref_Redundant) 
    #return np.where((x.F2diff > 0.5), props, '')
    if abs(x.Ref_Redundant) > 0.5:
        print('oi!!!!') 
        return ['background-color:yellow']
    else:
         return ['background-color:white']

def build_dataframe(d,basename):
    df = pd.DataFrame(data=d)
    df_i = df.to_csv('out.csv',index=False)
    # adds a space in between each molecule. 
    df.loc[df.shape[0]] = [None, None, None, None, None, None, None] 
    df.loc[df.shape[0]] = [None, None, None, None, None, None, None] 
    df.loc[df.shape[0]] = [None, None, None, None, None, None, None] 

    #df.loc[df.shape[0]] = [None, None, 'Signed Avg.', averages(F1diff)[0], 'Signed Avg.', averages(F1diff)[0], averages(F1F2diff)[0]]
    #df.loc[df.shape[0]] = [None, None, 'Average   .', averages(F1diff)[1], 'Average    ', averages(F1diff)[1], averages(F1F2diff)[1]]
    #df.loc[df.shape[0]] = [None, None, 'Std. Dev  .', stdev(F1diff),    'Std. Dev.  ', stdev(F1diff), stdev(F1F2diff)]

    df.loc[0,('Molecule')] = str(basename) 
    #df_i: dataframe, individual for each child directory
    frame.append(df)
    return frame, df_i 

def return_path_base(jobpath):
    name = os.path.basename(os.path.normpath(jobpath)) 
    return name


# ====================================
# Print out information about database
# ====================================

hq = os.getcwd()
jobb_list = []
path_ind = []

print("CMA Database Generation\n")
print(
"""
      CCCCCCCC      MMMMMM     MMMMMM           AAAAA
    CCCCCCCCCCCC    MMMMMMM   MMMMMMM          AAAAAAA
   CCCC      CCCC   MMMMMMMM MMMMMMMM         AAAA AAAA
  CCCC              MMMM MMMMMMM MMMM        AAAA   AAAA
  CCCC              MMMM  MMMM   MMMM       AAAA     AAAA
  CCCC              MMMM         MMMM      AAAA       AAAA
  CCCC              MMMM         MMMM     AAAAAAAAAAAAAAAAA 
   CCCC      CCCC   MMMM         MMMM    AAAAAAAAAAAAAAAAAAA
    CCCCCCCCCCCC    MMMM         MMMM   AAAA             AAAA
      CCCCCCCC      MMMM         MMMM  AAAA               AAAA
"""
)


print("""
.............................................................................,............
........................................................;+..,,,:::::::::,,,,..;;..........
......................................................:?S%*?*?%%%%SSSS%%%%?*++##?:........
...................................................,:?SS%%S#S%%?*******??%SSS###@#*,......
...................................................;??%%S#@%,.............,:#@@@@#@S;.....
......................................................,,,:::...............,;;;::,,,,.....
..........................................................................................
.................................................................,,,,,,,,,,,,.............
................................................................:::,,....,,:::............
...............................................................:;::,.,,,,,,:;+;...........
..............................................................,++;;:::::::;;++*,..........
..............................................................:*+*++++;;;++****,..........
..............................................................,+??????**?????%+...........
...............................................................,+%SSSSSSSSSS%+,...........
.................................................................:+%#@#@S%?+,.............
...................................................................:###S:,................
...................................................................+SS#?..................
...................................................................?SS#+..................
..................................................................,SSS#:..................
................................................................,.:SSSS,..................
................,*+...............................................+#S#?...................
.............,:*%#%...........................................,,,,?SS#+...................
...........,;?%?%#S,......................................,:;+*??%%%%S?*+:,...............
...........,;*?*?##:.................................,,.,;*%%%%%%%%%%%%%%%?+:.............
............,%S#?;*:...................................:?%%%%%%%%%%%%%%%%%%%%+,,..........
............+SS#;............,,.......................+%%%%%%%%%%%%%%%%%%%%%%S?,..........
............%S#%..,......,,,,,,,,,,,.................;S%%%%%%?*?%%%%%%?*?%%%%%S*,.........
...........,SS#*.....,.,::,,.....,::;,..............,?S%%%%%%%%%%%%%%%%%%%%%SSSS:.........
...........:SS#+......,;;;:,,,,,,,::++;;;;;+++++*****SSSSS%%%%%%%%%%%%%%%%%SSSSS;.........
...........:#S#+......:++;::::::::;;**%SSSSSSSSSSSSSS#SSSSSSS%%%%%%%%%SSSSSSSSS#;.........
...........,SS#?......;**+++;;;;+++*???????***+++;;;:*#SSSSSSSSSSSSSSSSSSSSSSSS%,.........
............?#SS,...,.,*%??*****??????:..............,?#SSSSSSSSSSSSSSSSSSSSS#S:..........
............:#SS%%*,...,*%%SSSSSSSS%?:................,*##SSSS###############%:...........
...........;S@@#@@?......:+?%SSSS%*;,...................;?S################%+,.,..........
...........,;%@@@@;.........,,,,,.........................:*%S####@@@##S%*;,..............
.............,;%@#,..........................................,:;+++++;:,..................
................;+,.......................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
""")

print("Authors: The Dorktor, Nathaniel Kitzpapi, the other one")
print()
print("Combinations of levels of theory (high, low): ", end="")
print(*combos, sep=", ")
print("Coordinate types: ", end="")
print(*coord_type, sep=", ")
print(f"Number of off-diagonal corrections: {n}")
print()

# Grab jobs from each path and order them numerically by ID
if compute_all:
    for path in paths:
        path_ind.append(len(jobb_list))
        tmp_list = glob.glob(hq + path + "/[1-9]*_*/")
        ind = np.argsort(np.array([int(re.search(r"/\d_.*/(\d*)_.*", name).group(1)) for name in tmp_list]))
        tmp_list = [tmp_list[i] for i in ind]
        jobb_list += tmp_list
else:
    for path in paths:
        path_ind.append(len(jobb_list))
        tmp_list = glob.glob(hq + path + "/76_*/")
        ind = np.argsort(np.array([int(re.search(r"/\d_.*/(\d*)_.*", name).group(1)) for name in tmp_list]))
        tmp_list = [tmp_list[i] for i in ind]
        jobb_list += tmp_list

# Gives printout for each molecule in jobb_list
print(f"Generating database entries for {len(jobb_list)} jobs:",end="")
for i, job in enumerate(jobb_list):
    if i in path_ind:
        print("\n\nDirectory: {}".format(paths[path_ind.index(i)]),end="")
        count = 0
    if count % 5 == 0:
        print("\n{0:20}".format(return_path_base(job)),end="")
        count += 1
    else:
        print("{0:20}".format(return_path_base(job)),end="")
        count += 1
print("\n")

# Initialize frames for pandas database
frame = []
if n > 0:
    frame2 = []


# ============
# Do the thing
# ============

def execute():
    for i, job in enumerate(jobb_list):
        os.chdir(job)
        sys.path.insert(0,job)
        options = None

        # Initialize objects
        mol = Molecule(job)
        basename = return_path_base(job) 
        d = {'Molecule' : None}     # Ensures molecule is first column
        if n > 0: 
            d2 = {'Molecule' : None}

        if i in path_ind:
            print(f"Currently running jobs in {paths[path_ind.index(i)]}\n")
        
        print("////////////////////////////////////////////")
        print(f"//{basename:^40}//")
        print("////////////////////////////////////////////")
        countt = 0
        # Run CMA for each combination of theory
        for combo in combos:
            # Grab geometry information 
            mol.get_geoms(combo)
            if not mol.direc_complete:
                break
 
            if not cma1:
                # Copy the necessary files with correct names
                shutil.copyfile(job + combo[1] + "/zmat", job + "zmat")
                shutil.copyfile(job + combo[1] + "/fc.dat", job + "fc.dat")
                shutil.copyfile(job + combo[0] + "/zmat", job + "zmat2")
                shutil.copyfile(job + combo[0] + "/fc.dat", job + "fc2.dat")       
                
                # Run for each coord type
                for coord in coord_type:
                
                    # Kept in for its historical significance
                    if coord == "Nattys":
                        print('ReeeeEEEEEeEEEEEEEEEEEEeEeeeeeeeeeeeeeeeeeEEEE')
                    elif coord == "Redundant":
                        print("Catalina wine mixer " + str(i))
                
                    print()
                    print("="*50)
                    print(" "*16+"Current Parameters")
                    print("-"*50)
                    print(f"  Job                     {mol.name} ({mol.ID})") 
                    print(f"  High level of theory    {combo[0]}")
                    print(f"  Low level of theory     {combo[1]}")
                    print(f"  Coordinate type         {coord}")
                    print("="*50)
                    print()
                
                    # Skip redundants if linear molecule
                    if 'Linear' in job and coord == 'Redundant':
                        print("What kind of idiot would use redundants for a linear molecule")
                        continue

                    from Merger import Merger
                    execMerger = Merger()
                     
                    #Specify options for Merger
                    if coord == "Nattys":
                        execMerger.options.man_proj = True
                        execMerger.options.coords = 'Custom'
                
                        #import the manual_projection module from the specific molecule directory 
                        spec = importlib.util.spec_from_file_location("manual_projection",  job + "/manual_projection.py")
                        foo = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(foo)
                        project_obj = foo.Projection(None)
                        project_obj.run()
                        Proj = copy.copy(project_obj.Proj)
                    
                    else:
                        execMerger.options.man_proj = False
                        execMerger.options.coords = coord
                        Proj = None
                
                    execMerger.options.n_cma2 = n
                    execMerger.options.off_diag = off_diag_bands
                
                    # Run CMA
                    execMerger.run(execMerger.options, Proj)
                
                    # Collect data
                    if coord_type.index(coord) == 0:
                        d[f'Ref ({combo[0]})'] = execMerger.reference_freq
                        mol.freqs[f'Ref ({combo[0]})'] = execMerger.reference_freq
                        
                        # Number the modes
                        d['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                
                    if coord == "Nattys":
                        d[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                        d[f'Ref - Nat ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_custom)
                        mol.freqs[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                    if coord == "Redundant":
                        d[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                        d[f'Ref - Red ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_redundant)
                        mol.freqs[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                
                    # Collect data for CMA2
                    if n > 0:
                        if coord == "Nattys":
                            d2['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                            d2[f"Ref {combo[0]}"] = execMerger.reference_freq
                            d2[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                            cma2_freqs_natty = execMerger.Freq_cma2 
                          
                            d2[f'Natty CMA2 ({combo[1]})'] = cma2_freqs_natty 
                            d2[f'Ref - Natty ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_custom)
                            d2[f'Ref - Natty CMA2 ({combo[1]})'] = freq_diff(execMerger.reference_freq, cma2_freqs_natty)
                            print('Give us CMA2!')                   
                        if coord == "Redundant":
                            d2['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                            d2[f"Ref {combo[0]}"] = execMerger.reference_freq
                            d2[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                            cma2_freqs_red = execMerger.Freq_cma2 
                          
                            d2[f'Natty CMA2 ({combo[1]})'] = cma2_freqs_red 
                            d2[f'Ref - Red ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_redundant)
                            d2[f'Ref - Red CMA2 ({combo[1]})'] = freq_diff(execMerger.reference_freq, cma2_freqs_red)
                            print('Give us CMA2!')                   
                
                    # delete objects so they are forced to reload
                    del execMerger
                    del Merger
                    if coord == "Nattys":
                        del project_obj
                
                # end of coord loop

                # Difference between Natty and Redundant freqs
                if 'Nattys' in coord_type and 'Redundant' in coord_type and 'Linear' not in job:
                    d[f'Nat - Red {combo[1]}'] = freq_diff(d[f'Natty ({combo[1]})'], d[f'Red ({combo[1]})'])
                
            #======================
            # Mitchell's playground
            #======================
            elif not mol.direc_complete:
                #cma1 = False 
                continue
            
            elif cma1:
                # move into directory with higher level geom, fc.dat, and Disp directories
                os.chdir(f"{job}/")
                # Add your code here
                print(f"I am in {os.getcwd()} and I can see {os.listdir()}")
                
                # raise RuntimeError

                # In the future we can use this coord loop if we want to 
                # But for now we will stick with redundants
                for coord in coord_type:
                    from Merger import Merger
                    execMerger = Merger(cma1_path= "/" + combo[0]+"/Disps_" + combo[1])
                    if os.path.exists(os.getcwd() + "/" + combo[0]+"/Disps_" + combo[1] + "/templateInit.dat"):
                        execMerger.options.calc_init = True
                   
                    if combo[1] == "CCSD_T_DZ":
                        execMerger.options.cart_insert_init = 9
                    elif combo[1] == "B3LYP_6-31G_2df,p_":
                        execMerger.options.cart_insert_init = 4
                        # execMerger.options.cart_insert_init = 315
                        execMerger.options.program_init = "psi4@master"
                    execMerger.options.coords = coord
                    execMerger.options.n_cma2 = n
                    execMerger.options.off_diag = off_diag_bands
                    execMerger.options.deriv_level = deriv_level
                    if coord == "Nattys":
                        try: 
                            shutil.copyfile(job + combo[0] + "/zmat", job + "zmat")
                            shutil.copyfile(job + combo[0] + "/zmat", job + "zmat2")
                            shutil.copyfile(job + combo[0] + "/fc.dat", job + "fc2.dat")       
                        except:
                            print('Once again, the directory does not contain the sufficient files for the specified job')
                            mol.direc_complete = False
                            break 
                        # print("No Nattys :(")
                        cma1_coord = "nat"
                        execMerger.options.man_proj = True
                        execMerger.options.coords = 'Custom'
                        spec = importlib.util.spec_from_file_location("manual_projection",  job + "/manual_projection.py")
                        foo = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(foo)
                        project_obj = foo.Projection(None)
                        project_obj.run()
                        Proj = copy.copy(project_obj.Proj)
                
                    else:
                        try: 
                            shutil.copyfile(job + combo[0] + "/zmat_cma1", job + "zmat")
                            shutil.copyfile(job + combo[0] + "/zmat_cma1_Final", job + "zmat2")
                            shutil.copyfile(job + combo[0] + "/fc.dat", job + "fc2.dat")       
                        except:
                            print('Once again, the directory does not contain the sufficient files for the specified job')
                            mol.direc_complete = False
                            break 
                        cma1_coord = "red"
                        # Import Merger
                        # print(os.getcwd())
                        # raise RuntimeError
                            # shutil.copy(os.getcwd() + "/" + combo[0]+"/Disps_" + combo[1] + "/templateInit.dat",os.getcwd() + "/" + combo[0]+ "/templateInit.dat")
                        execMerger.options.man_proj = False
                        Proj = None
                        # print(cma1_energy_regexes)
                    execMerger.run(execMerger.options,Proj,energy_regex=cma1_energy_regexes[countt],success_regex=cma1_success_regexes[countt],cma1_coord=cma1_coord)
                    # raise RuntimeError
                    # Run the thing
                    #execMerger.run(execMerger.options, Proj)

                    # Collect the data in dictionary d to add it to the database
                    # e.g. d[f"Ref {combo[0]}"] = execMerger.reference_freq
                    # d[f"CMA1 {combo[1]}"] = execMerger.Freq_redundant
                    # Collect data
                    if coord_type.index(coord) == 1:
                        print("Is this thing on?")
                        d[f'Ref ({combo[0]})'] = execMerger.reference_freq
                        print(execMerger.reference_freq)
                        mol.freqs[f'Ref ({combo[0]})'] = execMerger.reference_freq
                        
                        # Number the modes
                        d['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                        print(d['Molecule'])
                    
                    if coord == "Nattys":
                        d[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                        d[f'Ref - Nat ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_custom)
                        mol.freqs[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                    if coord == "Redundant":
                        d[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                        d[f'Ref - Red ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_redundant)
                        mol.freqs[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                    
                    #Collect data for CMA2
                    if n > 0:

                        if coord == "Nattys":
                            d2['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                            d2[f"Ref {combo[0]}"] = execMerger.reference_freq
                            d2[f'Natty ({combo[1]})'] = execMerger.Freq_custom
                            cma2_freqs_natty = execMerger.Freq_cma2 
                          
                            d2[f'Natty CMA2 ({combo[1]})'] = cma2_freqs_natty 
                            d2[f'Ref - Natty ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_custom)
                            d2[f'Ref - Natty CMA2 ({combo[1]})'] = freq_diff(execMerger.reference_freq, cma2_freqs_natty)
                        if coord == "Redundant":
                            d2['Molecule'] = [f"{mol.name} ({mol.ID}) mode {i+1}" for i in range(len(execMerger.reference_freq))]
                            d2[f"Ref {combo[0]}"] = execMerger.reference_freq
                            d2[f'Red ({combo[1]})'] = execMerger.Freq_redundant
                            cma2_freqs_red = execMerger.Freq_cma2 
                          
                            d2[f'Natty CMA2 ({combo[1]})'] = cma2_freqs_red 
                            d2[f'Ref - Red ({combo[1]})'] = freq_diff(execMerger.reference_freq, execMerger.Freq_redundant)
                            d2[f'Ref - Red CMA2 ({combo[1]})'] = freq_diff(execMerger.reference_freq, cma2_freqs_red)


                    del execMerger
                    del Merger
            countt += 1

        # end of combo loop
        if mol.direc_complete: 
            # Print molecule information
            mol.run()
            
            # Clean up job directory
            if not cma1:
                os.remove("fc.dat")
            try: 
                os.remove("zmat")
                os.remove("zmat2")
                os.remove("fc2.dat")
                # os.remove("templateInit.dat")
            except:
                print('These are not the files you are looking for') 
            
            sys.path.remove(job)
            del mol

            # Skip dataframe if linear molecule
            if 'Linear' in job:
                continue

            # Add to pandas dataframe
            if csv:
                df = pd.DataFrame(data=d)
                # print(df)
                # print()
                frame.append(df)
            
            if n > 0:
                # d2 ={'Ref_Redundant' : cma2_dict[key],
                     # 'CMA2_1_el' : d2[f'Ref - Red {combo[1]}']}        
                # d2['CMA2_1_el'] = d2[f'Ref - Red {combo[1]}']       
                # d2 ={'CMA2_1_el' : cma2_1_red_diff}        
                df2 = pd.DataFrame(data=d2)
                #df2.style.apply(highlight_greaterthan, axis =1)
                frame2.append(df2)

        # end of job loop

    # end of def
 
execute()
os.chdir(hq)
if csv:
    megaframe = pd.concat(frame)
    megaframe.to_csv('CoordDep.csv', index=False, float_format="%.2f")
    if n > 0:
        megaframe2 = pd.concat(frame2)
        megaframe2.to_csv('CMA2_Convergent.csv', index=False, float_format="%.2f")
#megaframe2.to_excel('CMA2_Convergent.xlsx', index=False)
#writer = pd.ExcelWriter("CMA2_Convergent.xlsx",engine = 'xlsxwriter', encoding = 'utf-8')
#megaframe2.to_excel(writer, sheet_name = 'Sheet1', index=False)
#
#workbook = writer.book
#worksheet = writer.sheets['Sheet1']
#
#workbook.close()



