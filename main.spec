# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/USUARIO/AppData/Local/Programs/Python/Python311/Lib/site-packages/mysql/connector/locales', 'mysql/connector/locales'), ('C:/Users/USUARIO/AppData/Local/Programs/Python/Python311/Lib/site-packages/certifi/cacert.pem', 'certifi'), ('ui/config.json', 'ui'), ('commands.db', '.'), ('imagenes', 'imagenes'), ('icon.ico', '.')],
    hiddenimports=['mysql.connector.plugins.mysql_native_password', 'PyQt5.QtWidgets', 'PyQt5.QtGui', 'PyQt5.QtCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
