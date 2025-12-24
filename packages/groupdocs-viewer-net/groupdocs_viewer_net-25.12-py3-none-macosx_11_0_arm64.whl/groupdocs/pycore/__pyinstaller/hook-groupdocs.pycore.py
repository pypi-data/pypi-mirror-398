from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('groupdocs')

datas = [(os.path.join(root, 'assemblies', 'pycore'), os.path.join('groupdocs', 'assemblies', 'pycore'))]

datas += [(os.path.join(root, 'pycore'), os.path.join('groupdocs', 'pycore'))]

hiddenimports = [ 'groupdocs', 'groupdocs.pygc' ]

