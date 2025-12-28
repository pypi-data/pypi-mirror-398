from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('groupdocs')

datas = [(os.path.join(root, 'netcore'), os.path.join('groupdocs', 'netcore'))]

datas += [(os.path.join(root, '__init__.py'), 'groupdocs')]


