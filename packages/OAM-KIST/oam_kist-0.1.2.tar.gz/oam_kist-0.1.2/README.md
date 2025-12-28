# OAM KIST

Imaging and sequence toolkit for Lageurre-Gaussian mode light, i.e. Orbital Angular Montum(OAM) state.

```bash
OAM_KIST/          # GitHub 저장소 루트  
├── OAM_KIST/              # 실제 패키지 소스 코드 (import OAM_KIST)  
│   ├── __init__.py       # 패키지 초기화 및 버전 정의  
│   ├── holography.py     # SLM 좌표계 및 홀로그램 생성 함수  
│   ├── vqe_solver.py     # COBYLA 알고리즘 및 VQE 로직  
│   └── utils.py          # 기타 유틸리티 (시각화 등)  
├── tests/                # 유닛 테스트 코드  
├── README.md             # 프로젝트 설명  
├── requirements.txt      # 의존성 라이브러리 목록  
├── setup.py              # 패키지 빌드 및 배포 설정  
└── .gitignore            # 제외할 파일 목록  
```