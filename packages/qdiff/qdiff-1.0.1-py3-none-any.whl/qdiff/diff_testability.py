import os

from qdiff.diff import Diff
from qdiff.smell_diff import SmellDiff


class DiffTestabilityDJ(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Class', 'Smell'],['Description'])
        for file in os.listdir(path1):
            if file == 'TestabilitySmells.csv':
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, 'TestabilitySmells_diff.csv'))

class DiffTestabilityDpy(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Module', 'Class', 'Smell', 'Method'],['Description'])
        for file in os.listdir(path1):
            if file.endswith('testability_smells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))


class DiffTestabilityDc(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Namespace', 'Class', 'Smell'],
                               ['Description'])
        for file in os.listdir(path1):
            if file.endswith('TestabilitySmells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))