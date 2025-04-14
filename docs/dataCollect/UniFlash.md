# UniFlash
[Download Site](https://www.ti.com/tool/UNIFLASH)\
[Quick Guid](https://software-dl.ti.com/ccs/esd/uniflash/docs/v8_8/uniflash_quick_start_guide.html)

## How to Flash
1. 센서 MUX switch를 flashing mode로 설정

    | 1 | 2 | 3 | 4 | 5 | 6 |
    |:---:|:---:|:---:|:---:|:---:|:---:|
    | on | off | on | on | off | - |

2. USB 연결 후 장치 관리자에서 포트 확인

3. UniFlash 실행 후 IWR6843ISK 선택 후 Start

4. Enhanced COM Port에 맞는 번호로 COM 포트 설정

5. Flash 할 Binary Image 선택
* 3D People Tracking의 경우\
<toolbox_install_dir>\source\ti\examples\people_tracking\3D_people_tracking\prebuilt_binaries\3D_people_track_68xx_demo.bin

6. Load Image

7. 완료 후, 센서 MUX switch를 functional mode로 설정

    | 1 | 2 | 3 | 4 | 5 | 6 |
    |:---:|:---:|:---:|:---:|:---:|:---:|
    | off | off | on | on | off | - |
