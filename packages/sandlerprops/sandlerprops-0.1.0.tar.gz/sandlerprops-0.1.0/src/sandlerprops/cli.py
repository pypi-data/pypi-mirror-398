# Author: Cameron F. Abrams, <cfa22@drexel.edu>


import logging
import os
import shutil

import argparse as ap

from .properties import PropertiesDatabase

banner = """
                                  █████ ████                    
                                 ░░███ ░░███                    
  █████   ██████   ████████    ███████  ░███   ██████  ████████ 
 ███░░   ░░░░░███ ░░███░░███  ███░░███  ░███  ███░░███░░███░░███
░░█████   ███████  ░███ ░███ ░███ ░███  ░███ ░███████  ░███ ░░░ 
 ░░░░███ ███░░███  ░███ ░███ ░███ ░███  ░███ ░███░░░   ░███     
 ██████ ░░████████ ████ █████░░████████ █████░░██████  █████    
░░░░░░   ░░░░░░░░ ░░░░ ░░░░░  ░░░░░░░░ ░░░░░  ░░░░░░  ░░░░░     
                                                                                 
       ████████  ████████   ██████  ████████   █████            
      ░░███░░███░░███░░███ ███░░███░░███░░███ ███░░             
       ░███ ░███ ░███ ░░░ ░███ ░███ ░███ ░███░░█████            
       ░███ ░███ ░███     ░███ ░███ ░███ ░███ ░░░░███           
       ░███████  █████    ░░██████  ░███████  ██████            
       ░███░░░  ░░░░░      ░░░░░░   ░███░░░  ░░░░░░             
       ░███                         ░███                        
       █████                        █████                       
      ░░░░░                        ░░░░░              

        (c) 2025, Cameron F. Abrams <cfa22@drexel.edu> 
"""
def cli():
    P = PropertiesDatabase()
    subcommands = {
        'showprops': dict(
            func = P.show_properties,
            help = 'show available properties',
            ),
        'find' : dict(
            func = P.find_compound,
            help = 'find compound by name',
            ),
        'show': dict(
            func = P.show_compound_properties,
            help = 'show properties for a compound',
        )
    }
    parser = ap.ArgumentParser(
        prog='sandlerprops',
    )
    parser.add_argument(
        '-b',
        '--banner',
        default=False,
        action=ap.BooleanOptionalAction,
        help='toggle banner message'
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="command",
        metavar="<command>",
        required=True,
    )
    command_parsers={}
    for k, specs in subcommands.items():
        command_parsers[k] = subparsers.add_parser(
            k,
            help=specs['help'],
            formatter_class=ap.RawDescriptionHelpFormatter
        )
        command_parsers[k].set_defaults(func=specs['func'])

    command_parsers['find'].add_argument(
        'compound_name',
        type=str,
        help='name of compound to find'
    )
    command_parsers['show'].add_argument(
        'compound_name',
        type=str,
        help='name of compound whose properties to show'
    )

    args = parser.parse_args()
    if args.banner:
        print(banner)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        my_list = ', '.join(list(subcommands.keys()))
        print(f'No subcommand found. Expected one of {my_list}')
    if args.banner:
        print('Thanks for using sandlerprops!')