# How to Build

## pyinstaller 설치
```cmd
pip install pyinstaller
```
* dependency check 위한 빌드 이전 최신화 필요

## 초기 빌드
```cmd
pyinstaller --onefile --windowed -n "app_name" app.py  
```

### 다시 빌드
spec 변경에 따라 다시 빌드하기는
```cmd
pyinstaller app.spec
```

### exe파일의 icon 설정
exe = EXE(... icon='path') 명시

## spec 파일
```py
a = Analysis(
    ['app.py'],  # main script
    pathex=[],  # additional paths to include for module searching
    binaries=[],    # extra binary files like DLLs
    datas=[],   # extra images like images or configs
    hiddenimports=[],
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
    name='app_name',  # name of output file
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,   # UPX compress
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # disable console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## 실행이 되지 않는다면
```py
exe=EXE(
    ...
    debug=True,
    ...
    console=True,
    ...
)
```
와 같이 설정하여 문제점 확인

### dll missing
* datas에 직접 path 명시하여 해결가능
* intel cpu의 경우 아래 명령어 시도가능
```
conda install mkl
or
pip install mkl
```

### icon missing
```py
if getattr(sys, 'frozen', False):
    os.path.join(sys._MEIPASS, 'bm_icon.ico')
```
* 위와 같이 임시 폴더에서 아이콘 찾도록 지정

```py
datas=[('img/bm_icon.ico','.')]
```

## venv에서 빌드
* conda에서 빌드시 용량 커지는 문제점 존재
```cmd
py -0
```
* 위 명령어로 원하는 버전 있는지 먼저 확인 후
```cmd
py -3.10 -m venv name_of_venv
name_of_venv\Scripts\activate
pip install Pyside2 pyserial numpy pyinstaller
```
* 이후 동일하게 빌드 가능