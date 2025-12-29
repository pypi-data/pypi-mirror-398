import os

from qdiff.diff import Diff
from qdiff.smell_diff import SmellDiff


class DiffImplDJ(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Class', 'Method', 'Smell', 'Description'],[])
        for file in os.listdir(path1):
            if file == 'ImplementationSmells.csv':
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, 'ImplementationSmells_diff.csv'))

class DiffImplDpy(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Module', 'Class', 'Smell', 'Method', 'Description'],[])
        for file in os.listdir(path1):
            if file.endswith('implementation_smells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))


class DiffImplDc(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Namespace', 'Class', 'Smell', 'Method', 'Description'],[])
        for file in os.listdir(path1):
            if file.endswith('ImpSmells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))