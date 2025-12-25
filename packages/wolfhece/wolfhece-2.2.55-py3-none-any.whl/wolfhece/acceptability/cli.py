"""
Author: University of Liege, HECE, LEMA
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
The command-line interface for the acceptability
"""

import argparse
from wolfhece.acceptability.acceptability import Base_data_creation, Vulnerability, Acceptability, Accept_Manager

def main():
    """
    This function sets up the command line argument parser, defines the
    available subcommands for the model operations (allowing efficient "-h"), 
    to help the user.

    Subcommands:
        - check: Perform checks on the model's data.
        - base_data_creation: Create base data for the model.
        - vulnerability: Assess vulnerability within the model.
        - acceptability: Evaluate the acceptability of the model's output.

    Usage:
        python cli.py <subcommand> [options]

    Options:
        -h, --help: Show this help message and exit.
    """
    
    
    print("\n=================Command Line Interface for Acceptability routine=================\n")
    parser = argparse.ArgumentParser(
        description="A tool to obtain vulnerability and acceptability for regions in Walloon Region and particularly in Vesdre valley."
    )

    subparsers = parser.add_subparsers(dest='function', required=True)

    """
    Informations for the subcommand "check"
    
    Options:
        --dir (str, optional): Path to the main directory containing all folders, setting the location for inputs and outputs. Default is 'Data'.
        --GDB (str, optional): Name of the main GDB file, such as GT_Resilence_dataRisques202010.gdb. Default is 'GT_Resilence_dataRisques202010.gdb'.
        --CaPa (str, optional): Name of the Cadaster geopackage, e.g., 'Cadastre_Walloon.gpkg'. Default is 'Cadastre_Walloon.gpkg'.
        --PICC (str, optional): Name of the PICC GDB file, e.g., 'PICC_vDIFF.gdb'. Default is 'PICC_vDIFF.gdb'.
        --CE (str, optional): Name of the river extent file from IGN, such as 'CE_IGN_top10v.shp'. Default is 'CE_IGN_TOP10V/CE_IGN_TOP10V.shp'.
        --scenario (str, optional): Scenario name. Default is 'Scenario1'.
        --study_area (str, optional): Area of interest, such as 'Theux', 'Chaudfontaine', 'Eupen', etc. Default is 'Bassin_Vesdre'.
        
    Usage example:
        python cli.py check --dir C:\example --GDB GT_Resilence_dataRisques202010.gdb --scenario Scenario_example
    """

    subparser_check = subparsers.add_parser('check', help='Check the status and process data.')
    subparser_check.add_argument("--dir",
                                 type=str,
                                 nargs='?',  
                                 default='Data',
                                 help="Add path to the main directory with all folders. This sets the path of all outputs and inputs.")
    
    subparser_check.add_argument("--GDB",
                                 type=str,
                                 nargs='?',  
                                 default='GT_Resilence_dataRisques202010.gdb',
                                 help="Add the name of the main gdb like GT_Resilence_dataRisques202010.gdb.")
    
    subparser_check.add_argument("--CaPa",
                                 type=str,
                                 nargs='?',
                                 default='Cadastre_Walloon.gpkg',
                                 help="Add the name of the Cadaster geopackage, like Cadastre_Walloon.gpkg.")
    
    subparser_check.add_argument("--PICC",
                                 type=str,
                                 nargs='?', 
                                 default='PICC_vDIFF.gdb',
                                 help="Add the name of the PICC gdb, like PICC_vDIFF.gdb.")
    
    subparser_check.add_argument("--CE",
                                 type=str,
                                 nargs='?', 
                                 default='CE_IGN_TOP10V/CE_IGN_TOP10V.shp',
                                 help="Add the name of the river extent from IGN, like CE_IGN_top10v.shp.")
    
    subparser_check.add_argument("--scenario",
                                 type=str,
                                 nargs='?', 
                                 default='Scenario1',
                                 help="Scenario name.")
    
    subparser_check.add_argument("--study_area",
                                 type=str,
                                 nargs='?',
                                 default='Bassin_Vesdre',
                                 help="Add the area of interest, like Theux, Chaufontaine, Eupen, etc.")

    """
    Informations for the subcommand "base_data_creation"
    
    Options:
        --dir (str, optional): Path to the main directory containing all folders, setting the location for inputs and outputs. Default is 'Data'.
        --GDB (str, optional): Name of the main GDB file. Default is 'GT_Resilence_dataRisques202010.gdb'.
        --study_area (str, optional): Name of the study area shapefile, such as 'Bassin_Vesdre.shp'. Default is 'Bassin_Vesdre.shp'.
        --CaPa (str, optional): Name of the Cadaster geopackage, e.g., 'Cadastre_Walloon.gpkg'. Default is 'Cadastre_Walloon.gpkg'.
        --PICC (str, optional): Name of the PICC GDB file, e.g., 'PICC_vDIFF.gdb'. Default is 'PICC_vDIFF.gdb'.
        --CE (str, optional): Name of the river extent file from IGN, e.g., 'CE_IGN_TOP10V/CE_IGN_TOP10V.shp'. Default is 'CE_IGN_TOP10V/CE_IGN_TOP10V.shp'.
        --resolution (float, optional): Resolution of the water depth files in meters. Default is 1.0.
        --number_procs (int, optional): Number of processors to use. Default is 1.
        --steps (int, optional, multiple): Step(s) to perform, specified as a space-separated list, e.g., '--steps 5 6 7'. Default is [1,2,3,4,5,6,7].
        --Vuln_csv (str, optional): Path to the .csv file for the weights. Default is 'Vulnerability.csv'.    
    """
    subparser_base = subparsers.add_parser('base_data_creation', help='Create the base data needed for the vulnerability and acceptability rasters.')
    
    subparser_base.add_argument("--dir",
                                type=str,
                                nargs='?',  
                                default='Data',
                                help="Add path to the main directory with all folders. This sets the path of all outputs and inputs. Defaults to Data.")
    
    subparser_base.add_argument("--GDB",
                                type=str,
                                nargs='?',  
                                default='GT_Resilence_dataRisques202010.gdb',
                                help="Add the name of the main gdb. Defaults to GT_Resilence_dataRisques202010.gdb.")
    
    subparser_base.add_argument("--study_area",
                                type=str,
                                nargs='?', 
                                default='Bassin_Vesdre.shp',
                                help="Add the name of the study area shapefile, Vesdre Valley like Bassin_SA.shp. Defaults to Bassin_Vesdre.shp.")
    
    subparser_base.add_argument("--CaPa",
                                type=str,
                                nargs='?',  
                                default='Cadastre_Walloon.gpkg',
                                help="Add the name of the Cadaster geopackage. Defaults to Cadastre_Walloon.gpkg.")
    
    subparser_base.add_argument("--PICC",
                                type=str,
                                nargs='?',  
                                default='PICC_vDIFF.gdb',
                                help="Add the name of the PICC gdb. Defaults to PICC_vDIFF.gdb.")
    
    subparser_base.add_argument("--CE",
                                type=str,
                                nargs='?', 
                                default='CE_IGN_TOP10V/CE_IGN_TOP10V.shp',
                                help="Add the name of the river extent from IGN. Defaults to CE_IGN_TOP10V/CE_IGN_TOP10V.shp.")
    
    subparser_base.add_argument("--resolution",
                                type=float,
                                nargs='?',  
                                default=1.0,
                                help="Add the resolution of water_depth files. Defaults to 1.0m.")
    
    subparser_base.add_argument("--number_procs",
                                type=int,
                                nargs='?', 
                                default=1,
                                help="Add the number of processors to use. Defaults to 1.")
    
    subparser_base.add_argument("--steps",
                                type=int,
                                nargs='*', 
                                default= [1,2,3,4,5,6,7],
                                help="Add the particular step(s) to perform, e.g '--steps 5 6 7'. Defaults to [1,2,3,4,5,6,7]")
    
    subparser_base.add_argument("--Vuln_csv",
                                type=str,
                                nargs='?', 
                                default='Vulnerability.csv',
                                help="Add the particular .csv file for the weights. Defaults to Vulnerability.csv")
                           
                           

    """
    Informations for the subcommand "vulnerability"
    
    Options:
        --dir (str, optional): Path to the main directory containing all folders, setting the location for inputs and outputs. Default is 'Data'.
        --scenario (str, optional): Name of the scenario. Default is 'Scenario1'.
        --study_area (str, optional): Area of interest, such as 'Theux', 'Chaudfontaine', 'Eupen', etc. Default is 'Bassin_Vesdre'.
        --resolution (float, optional): Resolution for the vulnerability raster in meters. Default is 1.0.
        --steps (int, optional, multiple): Step(s) to perform, specified as a space-separated list, e.g., '--steps 2 3 4'. Default is [1,10,11,2,3].
        --Vuln_csv (str, optional): Path to the .csv file for vulnerability layers. Default is 'Vulnerability.csv'.
        --Intermediate_csv (str, optional): Path to the .csv file for acceptability functions (scoring layers based on water depth). Default is 'Intermediate.csv'.
        
    Usage example :
        python cli.py vulnerability --scenario Scenario_example --study_area Bassin_Vesdre --dir C:\example --steps 1 10 11
    """
    subparser_vulnerability = subparsers.add_parser('vulnerability', help='Compute the total vulnerability raster.')
    
    subparser_vulnerability.add_argument("--dir",
                                         type=str,
                                         nargs='?', 
                                         default='Data',
                                         help="Add path to the main directory with all folders. This sets the path of all outputs and inputs.")
    
    subparser_vulnerability.add_argument("--scenario",
                                         type=str,
                                         nargs='?',
                                         default='Scenario1',
                                         help="Scenario name.")
    
    subparser_vulnerability.add_argument("--study_area",
                                         type=str,
                                         nargs='?', 
                                         default='Bassin_Vesdre',
                                         help="Add the area of interest, like Theux, Chaufontaine, Eupen, etc.")
    
    subparser_vulnerability.add_argument("--resolution",
                                         type=float,
                                         nargs='?', 
                                         default=1.0,
                                         help="Add the resolution for the vulnerability raster. Defaults to 1.0.")
    
    subparser_vulnerability.add_argument("--steps",
                                         type=int,
                                         nargs='*', 
                                         default=[1,10,11,2,3],
                                         help="Add the particular step(s) to perform, e.g '2 3 4'. Defaults to [1,10,11,2,3]")
    
    subparser_vulnerability.add_argument("--Vuln_csv",
                                         type=str,
                                         nargs='?', 
                                         default='Vulnerability.csv',
                                         help="Add the .csv file for the vulenrability layers. Defaults to Vulnerability.csv.")
    
    subparser_vulnerability.add_argument("--Intermediate_csv",
                                         type=str,
                                         nargs='?', 
                                         default='Intermediate.csv',
                                         help="Add the .csv file for the acceptability functions (for each layers, acceptability scores in fct of the water depths). Defaults to Intermediate.csv.")                      
                      
    """
    Informations for the subcommand "acceptability"
    
    Options:
        --dir (str, optional): Path to the main directory with all folders, setting the location for inputs and outputs. Default is 'Data'.
        --study_area (str, optional): Name of the area of interest. Default is 'Bassin_Vesdre'.
        --scenario (str, optional): Name of the scenario to use. Default is 'Scenario1'.
        --coeff_auto (bool, optional): Indicates if weighting coefficients should be re-computed automatically. Default is True.
        --Ponderation_csv (str, optional): Path to the .csv file from which weighting coefficients are read. Default is 'Ponderation.csv'.
        --resample_size (int, optional): Resolution at which the final raster will be aggregated, in meters. Default is 100m.
        --steps (int, optional, multiple): Specific step(s) to execute, given as a space-separated list, e.g., '--steps 2 3 4'. Default is [1,2,3,4,5].

    Usage example :
        python cli.py acceptability --scenario Scenario_example --study_area Bassin_Vesdre --dir C:\Example --steps 1 10 11
    """
    subparser_acceptability = subparsers.add_parser('acceptability', help='Compute the acceptability rasters.')
    
    subparser_acceptability.add_argument("--dir",
                                         type=str,
                                         nargs='?',  
                                         default='Data',
                                         help="Add path to the main directory with all folders. This sets the path of all outputs and inputs.")
    
    subparser_acceptability.add_argument("--study_area",
                                         type=str,
                                         nargs='?', 
                                         default='Bassin_Vesdre',
                                         help="Add the name of area. Defaults to Bassin_Vesdre.")
    
    subparser_acceptability.add_argument("--scenario",
                                         type=str,
                                         nargs='?', 
                                         default='Scenario1',
                                         help="Add the name of the scenario. Default to Scenario1.")


    subparser_acceptability.add_argument("--coeff_auto",
                                         type=bool,
                                         nargs='?', 
                                         default=True,
                                         help="Decide if the weighting coefficients are re-computed. Defaults to True.")

    subparser_acceptability.add_argument("--Ponderation_csv",
                                         type=str,
                                         nargs='?', 
                                         default='Ponderation.csv',
                                         help="Add the .csv file where the weighting coefficients are read. Defaults to Ponderation.csv.")
    
    subparser_acceptability.add_argument("--resample_size",
                                         type=int,
                                         nargs='?', 
                                         default=100,
                                         help="Add the resolution at which the final raster will be agglomerate. Defaults to 100m.")
    
    subparser_acceptability.add_argument("--steps",
                                         type=int,
                                         nargs='*', 
                                         default=[1,2,3,4,5],
                                         help="Add the particular step(s) to perform, e.g '2 3 4'. Defaults to [1,2,3,4,5]")
        
    args = parser.parse_args()
    
    """
    Starting the computations themselves if the function is ordered.
    """
    if args.function == "check":
        manager = Accept_Manager(main_dir=args.dir,
                                 Study_area=args.study_area,
                                 scenario=args.scenario,
                                 Original_gdb=args.GDB,
                                 CaPa_Walloon=args.CaPa,
                                 PICC_Walloon=args.PICC,
                                 CE_IGN_top10v=args.CE)

    elif args.function == "base_data_creation":
        Base_data_creation(main_dir=args.dir,
                           Original_gdb=args.GDB,
                           Study_area=args.study_area,
                           CaPa_Walloon=args.CaPa,
                           PICC_Walloon=args.PICC,
                           CE_IGN_top10v=args.CE,
                           resolution=args.resolution,
                           number_procs=args.number_procs,
                           steps=args.steps,
                           Vuln_csv=args.Vuln_csv)
        
    elif args.function == "vulnerability":
        Vulnerability(main_dir=args.dir,
                      scenario=args.scenario,
                      Study_area=args.study_area,
                      resolution=args.resolution,
                      steps=args.steps,
                      Vuln_csv=args.Vuln_csv,
                      Intermediate_csv=args.Intermediate_csv)

    elif args.function == "acceptability":
        Acceptability(main_dir=args.dir,
                      scenario=args.scenario,
                      Study_area=args.study_area,
                      coeff_auto=args.coeff_auto,
                      Ponderation_csv=args.Ponderation_csv,
                      resample_size=args.resample_size,
                      steps=args.steps)    
    
if __name__ == '__main__':
    main()