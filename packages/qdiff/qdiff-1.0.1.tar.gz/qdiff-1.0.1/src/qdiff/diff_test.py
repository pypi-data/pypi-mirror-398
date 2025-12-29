import os

from qdiff.diff import Diff
from qdiff.smell_diff import SmellDiff


class DiffTestDJ(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Class', 'Method', 'Smell', 'Description'],[])
        for file in os.listdir(path1):
            if file == 'TestSmells.csv':
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, 'TestSmells_diff.csv'))

class DiffTestDpy(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Module', 'Class', 'Smell', 'Method', 'Description'],[])
        for file in os.listdir(path1):
            if file.endswith('test_smells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))

class DiffTestDc(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Namespace', 'Class', 'Smell', 'Method', 'Description'],[])
        for file in os.listdir(path1):
            if file.endswith('TestSmells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))