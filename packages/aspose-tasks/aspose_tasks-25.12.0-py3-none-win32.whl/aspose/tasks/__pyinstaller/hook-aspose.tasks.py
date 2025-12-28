from PyInstaller.utils.hooks import get_package_paths
import os.path

(_, root) = get_package_paths('aspose')

datas = [(os.path.join(root, 'assemblies', 'tasks'), os.path.join('aspose', 'assemblies', 'tasks'))]

hiddenimports = [ 'aspose', 'aspose.pyreflection', 'aspose.pydrawing', 'aspose.pygc', 'aspose.pycore' ]

