from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('groupdocs')

datas = [(os.path.join(root, 'assemblies', 'comparison'), os.path.join('groupdocs', 'assemblies', 'comparison'))]

hiddenimports = [ 'groupdocs', 'groupdocs.pyreflection', 'groupdocs.pydrawing', 'groupdocs.pygc', 'groupdocs.pycore' ]

