# Memvid-rs (Python Bindings)

**Memvid-rs**는 Rust의 고성능을 Python의 편리함과 결합한 라이브러리입니다. 텍스트 데이터를 QR 코드로 변환하고 이를 비디오 프레임으로 인코딩하여 대용량 데이터를 효율적으로 저장하고 검색할 수 있게 해줍니다.

이 프로젝트는 Rust로 작성된 코어 로직(`MemvidEncoder`)을 PyO3를 통해 Python 모듈로 제공합니다.

> **Attribution**: 이 프로젝트는 [Olow304/memvid](https://github.com/Olow304/memvid)의 아이디어와 설계를 바탕으로 Rust로 재구현한 포트(Port)입니다. 원본 프로젝트의 혁신적인 접근 방식에 깊은 감사를 드립니다.

## 🚀 주요 기능

-   **고성능 인코딩**: Rust의 병렬 처리와 효율적인 메모리 관리를 통해 빠른 속도로 텍스트를 비디오로 변환합니다.
-   **Python 친화적**: `pip`를 통해 간편하게 설치하고, Python 객체처럼 자연스럽게 사용할 수 있습니다.
-   **강력한 압축**: 텍스트 -> QR -> 비디오(H.264/H.265) 변환을 통해 데이터 저장 공간을 획기적으로 줄입니다.

## 📦 설치 방법 (Installation)

### 1. 소스 코드에서 직접 빌드 및 설치 (개발자용)

Rust와 Python 개발 환경이 필요합니다.

```bash
# 1. Rust 설치 (없을 경우)
brew install rust ffmpeg

# 2. 가상 환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 3. Maturin 설치 (Rust-Python 빌드 도구)
pip install maturin

# 4. 빌드 및 설치
maturin develop --release
```

### 2. Wheel 파일로 설치 (배포용)

빌드된 `.whl` 파일이 있다면 `pip`로 바로 설치할 수 있습니다.

```bash
pip install memvid_rs-0.1.0-cp39-cp39-macosx_11_0_arm64.whl
```

### 3. PyPI를 통한 설치 (공식)

PyPI 저장소에 배포되었으므로 다음과 같이 간단하게 설치할 수 있습니다.

```bash
pip install memvid-rs
```

## 💻 사용 방법 (Usage)

### 기본 사용법

```python
import memvid_rs

# 1. 인코더 초기화
encoder = memvid_rs.MemvidEncoder()

# 2. 텍스트 데이터 추가
# add_text(text, chunk_size, overlap)
# - text: 인코딩할 전체 텍스트
# - chunk_size: 하나의 QR 코드에 담을 글자 수 (예: 100~500)
# - overlap: 청크 간 중복시킬 글자 수 (검색 정확도 향상용)
text_data = "Memvid-rs는 정말 빠르고 효율적입니다. " * 100
encoder.add_text(text_data, chunk_size=200, overlap=20)

# 3. 비디오 생성
# build(output_path, index_path)
# - output_path: 저장할 비디오 파일 경로 (.mp4)
# - index_path: (현재 미사용, 향후 검색 인덱스용)
try:
    encoder.build("output.mp4", "index.json")
    print("비디오 생성 완료: output.mp4")
except Exception as e:
    print(f"오류 발생: {e}")
```

### 대용량 데이터 처리

Rust 내부적으로 메모리를 효율적으로 관리하므로, 반복문을 통해 계속해서 텍스트를 추가해도 됩니다.

```python
encoder = memvid_rs.MemvidEncoder()

# 여러 문서 추가
documents = ["doc1.txt", "doc2.txt", "doc3.txt"]

for doc in documents:
    with open(doc, "r") as f:
        content = f.read()
        encoder.add_text(content, 500, 50)

encoder.build("archive.mp4", "index.json")
```

## 🛠 배포 가이드 (PyPI 등록)

-   `pip install git+https://github.com/drivenbycode/memvid-rs.git` 명령어로 누구나 설치할 수 있게 하려면 **PyPI (Python Package Index)**에 패키지를 업로드해야 합니다.

1.  **PyPI 계정 생성**: [pypi.org](https://pypi.org/)에서 계정을 만듭니다.
2.  **Maturin으로 배포**:
    ```bash
    # PyPI에 업로드 (토큰 필요)
    maturin publish
    ```
    
    또는 GitHub Actions 등을 통해 자동화할 수도 있습니다.

## ⚠️ 요구 사항

-   **시스템**: macOS (현재 테스트됨), Linux, Windows
-   **필수 프로그램**: `ffmpeg` (비디오 인코딩용, 런타임에 필요)
    -   macOS: `brew install ffmpeg`
