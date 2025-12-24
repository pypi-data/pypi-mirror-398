from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('groupdocs')

datas = [(os.path.join(root, 'assemblies', 'pydrawing'), os.path.join('groupdocs', 'assemblies', 'pydrawing'))]

hiddenimports = [ 'groupdocs', 'groupdocs.pyreflection', 'groupdocs.pygc' ]

