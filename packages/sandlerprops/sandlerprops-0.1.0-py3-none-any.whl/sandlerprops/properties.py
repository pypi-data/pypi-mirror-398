# Author: Cameron F. Abrams <cfa22@drexel.edu>

import pandas as pd
import numpy as np

from argparse import Namespace
from difflib import SequenceMatcher
from importlib.resources import files

class PropertiesDatabase:
    datafile_path = files('sandlerprops.resources').joinpath('data','properties_database.csv')
    def __init__(self):
        D = pd.read_csv(self.datafile_path, header=0, index_col=None)
        self.D = D.rename(columns={
            'Tfp (K)': 'Tfp',
            'Tb (K)': 'Tb',
            'Tc (K)': 'Tc',
            'Pc (bar)': 'Pc'})
        unitlist = [
            '',
            '',
            '',
            'g/mol',
            'K',
            'K',
            'K',
            'bar',
            'm3/mol',
            '',
            '',
            '',
            'J/mol-K',
            'J/mol-K2',
            'J/mol-K3',
            'J/mol-K4',
            'J/mol',
            'J/mol',
            '',
            '',
            '',
            '',
            '',
            'K',
            'K',
            '',
            '']
        self.properties = list(self.D.columns)
        unitdict = {k: v for k,v in zip(self.properties, unitlist)}
        self.U = Namespace(**unitdict)

    def show_properties(self, args: Namespace):
        for p in self.properties:
            unit = self.U.__dict__[p]
            if unit != '':
                print(f'{p} ({unit})')
            else:
                print(f'{p}')

    def find_compound(self, args: Namespace):
        compound_name = args.compound_name
        record = self.get_compound(compound_name)
        if record is not None:
            print(f'Found exact match: {record.Name} (index {record.No})')

    def show_compound_properties(self, args: Namespace):
        compound_name = args.compound_name
        record = self.get_compound(compound_name)
        if record is not None:
            print(f'Properties for {record.Name} (index {record.No}):')
            for p in self.properties:
                value = record.__dict__[p]
                unit = self.U.__dict__[p]
                if unit != '':
                    print(f'  {p}: {value} {unit}')
                else:
                    print(f'  {p}: {value}')

    def get_compound(self, name, near_matches=10):
        row = self.D[self.D['Name'] == name]
        if not row.empty:
            d = row.to_dict('records')[0]
            return Namespace(**d)
        else:
            print(f'{name} not found.  Here are similars:')
            scores = []
            for n in self.D['Name']:
                scores.append(SequenceMatcher(None, name, n).ratio())
            scores = np.array(scores)
            si = np.argsort(scores)
            sorted_names = np.array(self.D['Name'])[si]
            top_sorted_names = sorted_names[-near_matches:][::-1]
            for n in top_sorted_names:
                print(n)
        return None
        
# Properties = PropertiesDatabase()
