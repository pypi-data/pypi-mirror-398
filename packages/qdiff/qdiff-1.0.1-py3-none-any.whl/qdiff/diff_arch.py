import os

from qdiff.diff import Diff
from qdiff.smell_diff import SmellDiff


class DiffArchDJ(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package','Smell'],['Description'])
        for file in os.listdir(path1):
            if file == 'ArchitectureSmells.csv':
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, 'ArchitectureSmells_diff.csv'))

class DiffArchDpy(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package','Smell'],['Description'])
        for file in os.listdir(path1):
            if file.endswith('arch_smells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))


class DiffArchDc(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Namespace','Smell'],['Description'])
        for file in os.listdir(path1):
            if file.endswith('ArchSmells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))