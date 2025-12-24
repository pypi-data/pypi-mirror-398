from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('groupdocs')

datas = [(os.path.join(root, 'assemblies', 'pygc'), os.path.join('groupdocs', 'assemblies', 'pygc'))]

hiddenimports = [ 'groupdocs' ]

