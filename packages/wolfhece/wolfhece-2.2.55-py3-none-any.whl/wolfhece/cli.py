"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

def check():
    """ Main wolf application : Check """
    from .apps.check_install import main
    main()

def license():
    """ Main wolf application : License """
    from wolf_libs.wolfogl import request_license

    from pathlib import Path

    if Path(__file__).parent / 'license' / 'wolf.lic':
        print('License file found -- Regenerate !')

    email = ''
    while not '@' in email:
        email = input('Enter your email and press enter : ')

    request_license(email)
    if Path(__file__).parent / 'license' / 'wolf.lic':
        print('Done !')
    else:
        print('Error ! - Please retry. If the error persists, contact the support.')

def accept():
    """ Main wolf application : Accept """
    from .acceptability.cli import main
    main()

def acceptability_gui():
    """ Main wolf application : Accept """
    from .apps.acceptability import main
    main()

def wolf():
    """ Main wolf application : Map Manager"""
    from .apps.wolf import main
    main()

def wolf2d():
    """ Application for 2D simuations """
    from .apps.wolf2D import main
    main()

def hydrometry():
    """ Application for 2D simuations """
    from .apps.hydrometry import main
    main()

def digitizer():
    """ Application for digitizing curves """
    from .apps.curvedigitizer import main
    main()

def params():
    """ Application for managing parameters in WOLF format """
    from .apps.ManageParams import main
    main()

def optihydro():
    """ Application for hydrological optimisation """
    from .apps.Optimisation_hydro import main
    main()

def hydro():
    """ Application for hydrological simulations """
    from .apps.wolfhydro import main
    main()

def report_gpu():
    """ Application for generating GPU simulation reports """
    from .report.simplesimgpu import SimpleSimGPU_Report

    # récupère l'argument de la ligne de commande
    from pathlib import Path
    import sys
    n = len(sys.argv)

    if n == 3:
        outpath = Path(sys.argv[2])
        mydir = Path(sys.argv[1])
    elif n == 2:
        outpath = Path('.')
        mydir = Path(sys.argv[1])
    else:
        print('Usage: wolf_report_gpu <directory> or wolf_report_gpu <directory> <directory_out>')

    if n in [2, 3]:
        if mydir.exists():
            report = SimpleSimGPU_Report(mydir)
            report.create_report()
            report.save_report(outpath / (mydir.name + '_report.pdf'))
        else:
            print('Directory not found')
    else:
        print('Usage: wolf_report_gpu <directory>')

def reports_gpu():
    """ Application for generating GPU simulation reports """
    from .report.simplesimgpu import SimpleSimGPU_Report

    # récupère l'argument de la ligne de commande
    from pathlib import Path
    import glob
    import sys
    n = len(sys.argv)

    if n == 3:
        outpath = Path(sys.argv[2])
        mydir = Path(sys.argv[1])
    elif n == 2:
        mydir = Path(sys.argv[1])
        outpath = Path('.')
    else:
        print('Usage: wolf_reports_gpu <directory> or wolf_reports_gpu <directory> <directory_out>')

    if n in [2, 3]:
        if mydir.exists():
            # find all sims in the directory
            sim_dirs = Path(mydir).rglob('parameters.json')
            sim_dirs = [Path(d).parent for d in sim_dirs]
            if not sim_dirs:
                print('No simulation directories found in {}'.format(mydir))
                return
            # create a report for each simulation
            for sim_dir in sim_dirs:
                print('Creating report for {}'.format(sim_dir))
                report = SimpleSimGPU_Report(sim_dir)
                report.create_report()
                report.save_report(outpath / (sim_dir.name + '_report.pdf'))
        else:
            print('Directory not found')

def report_compare():
    """ Application for comparing GPU simulation reports """
    from .report.simplesimgpu import SimpleSimGPU_Report_Compare

    # récupère l'argument de la ligne de commande
    from pathlib import Path
    import sys
    n = len(sys.argv)
    if n == 2:
        mydir = Path(sys.argv[1])
        if mydir.exists():
            report = SimpleSimGPU_Report_Compare(mydir)
            report.create_report()
            report.save_report(mydir.name + '_report_compare.pdf')
        else:
            print('Directory not found')
    elif n > 2:
        files = [Path(f) for f in sys.argv[1:]]
        if all(f.exists() for f in files):
            report = SimpleSimGPU_Report_Compare(files)
            report.create_report()
            report.save_report('report_compare.pdf')
        else:
            for f in files:
                if not f.exists():
                    print('File {} not found'.format(f))
    else:
        print('Usage: wolf_report_compare <directory> or wolf_report_compare <file1> <file2> ...')


def compare():
    """ Application for comparing 2D arrays """
    from .apps.wolfcompare2Darrays import main
    from PyTranslate import _
    from wolf_array import WolfArray
    from pathlib import Path
    import sys
    from pathlib import Path

    """gestion de l'éxécution du module en tant que code principal"""
    # total arguments
    n = len(sys.argv)
    # arguments
    print("Total arguments passed:", n)
    assert n in [2,3], _('Usage : wolfcompare <directory> or wolfcompare <file1> <file2>')

    if n==2:
        mydir = Path(sys.argv[1])
        if mydir.exists():
            main(mydir)
        else:
            print(_('Directory not found'))
    elif n==3:
        file1 = Path(sys.argv[1])
        file2 = Path(sys.argv[2])

        if file1.exists() and file2.exists():
            main('', [WolfArray(file1), WolfArray(file2)])
        else:
            if not file1.exists():
                print(_('File {} not found'.format(file1)))
            if not file2.exists():
                print(_('File {} not found'.format(file2)))
