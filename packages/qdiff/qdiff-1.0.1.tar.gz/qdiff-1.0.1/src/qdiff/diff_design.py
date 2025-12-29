import os

from qdiff.diff import Diff
from qdiff.smell_diff import SmellDiff


class DiffDesignDJ(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Class', 'Smell'],['Description'])
        for file in os.listdir(path1):
            if file == 'DesignSmells.csv':
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, 'DesignSmells_diff.csv'))


class DiffDesignDpy(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Package', 'Module', 'Smell', 'Class'],['Description'])
        for file in os.listdir(path1):
            if file.endswith('design_smells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))


class DiffDesignDc(Diff):
    def diff(self, path1, path2, output_path):
        smell_diff = SmellDiff(['Project', 'Namespace', 'Smell', 'Class'],['Description'])
        for file in os.listdir(path1):
            if file.endswith('DesignSmells.csv'):
                smell_diff.diff_csv(os.path.join(path1, file),
                                os.path.join(path2, file),
                                os.path.join(output_path, file.replace('.csv', '_diff.csv')))