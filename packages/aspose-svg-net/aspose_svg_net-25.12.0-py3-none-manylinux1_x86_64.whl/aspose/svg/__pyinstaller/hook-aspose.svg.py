from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('aspose')

datas = [(os.path.join(root, 'assemblies', 'svg'), os.path.join('aspose', 'assemblies', 'svg'))]

hiddenimports = [ 'aspose', 'aspose.pydrawing', 'aspose.pyreflection', 'aspose.pygc', 'aspose.pycore' ]

