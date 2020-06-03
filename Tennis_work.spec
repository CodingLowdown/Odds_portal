# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Tennis_work.py'],
             pathex=['/Users/nicholaslowe/Desktop/code/Tennis'],
             binaries=[],
             datas=[],
             hiddenimports=['_sysconfigdata_m_darwin_darwin'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Tennis_work',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
