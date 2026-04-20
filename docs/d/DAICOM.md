# DAICOM

## 목차

- [개념](#개념)

## 개념

### 정의

- Digital Imaging and Communications in Medicine 약어
- X-Ray 등 의료 영상을 저장 및 전송하기 위한 국제 표준 파일 형식으로 `.dcm` 확장자 사용

!!! info "본 문서에서의 DAICOM 개념 범위"

    위 정의에 따라 X-Ray 등 여러 의료 영상을 다룰 때 사용하는 파일 형식이지만
    본 문서에서는 유방촬영술(Mammography)에 의해 촬영된 맘모그램(Mammogram) 영상만을 대상으로 다룹니다.

### 구조

#### 메타데이터

| 메타데이터               | 설명                                                                             |
|:--------------------|:-------------------------------------------------------------------------------|
| Patient             | 이름 및 생년월일 같은 환자 정보                                                             |
| Study               | 검사 일시 및 검사 사유 같은 검사 정보                                                         |
| Series              | 촬영 장비(Modality) 및 촬영 부위와 같은 촬영 관련 정보                                           |
| Image               | 픽셀 데이터, 해상도, [Window]() 같은 이미지 관련 정보                                           |
| View Position       | 3차원 입체를 2차원 평면으로 확인하기 위해 촬영한 표준 각도로 아래 CC 및 MLO를 함께 활용하여 "상부 바깥쪽" 같은 3차원 좌표 획득 |
| CC(Craniocaudal)    | 유방을 위에서 아래로 눌러 촬영하는 방식으로 안쪽(Medial) 및 바깥쪽(Lateral) 가시화                         |
| MLO(Meidolateral)   | 유방을 옆에서 대각선 방향으로 촬영하는 방식으로 상부 외측(Upper-Outer)과 겨드랑이 부위(Axillary Tail)를 가시화     |
| Image Laterality    | 왼쪽 및 오른쪽 구분                                                                    |
| Image Pixel Spacing | 픽셀 하나당 실제 몸 길이로 병변 크기 파악에 사용                                                   |
| Organ Dose          | 환자가 받은 방사선 조사량으로 화질과 노이즈 수준 짐작                                                 |

## 실습

### 메타데이터 출력

```Python


```
