<p align="center">
  <img src="https://raw.githubusercontent.com/bestend/confee/main/assets/logo.png" width="360" />
</p>

<div align="center">

**언어:** 한국어 | [English](./README.md)

Hydra 스타일의 Configuration 관리 + Pydantic 타입 안전성 + Typer 스타일 자동 Help 생성

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-yellow)](https://github.com/bestend/confee)
[![Tests](https://github.com/bestend/confee/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/confee/actions/workflows/tests.yml)

</div>

---

## ☕️ 개요

**confee**는 Python 애플리케이션의 설정 관리를 간단하고 타입 안전하며 직관적으로 만드는 패키지입니다. Hydra와 Pydantic의 최고 기능을 결합하여 설정 파일, 환경 변수, CLI 인자를 seamlessly하게 관리할 수 있습니다.

---

## ✨ 주요 기능

- **🎯 타입 안전 Configuration** — Pydantic V2로 자동 타입 검증 및 IDE 자동완성
- **📋 다중 포맷 지원** — YAML과 JSON 자동 감지 및 파싱
- **🔄 유연한 Override 시스템** — CLI 인자와 환경 변수로 값 오버라이드
- **🏗️ Configuration 상속** — 부모-자식 설정 병합 및 조합
- **📁 파일 참조** — `@file:` & `@config:` 접두사로 파일 내용 로드
- **🔐 Strict 모드** — unknown fields 거부 또는 검증 오류 처리 방식 제어
- **📦 Zero Configuration** — 기본값으로 즉시 사용 가능
- **⚙️ Parse 순서 제어** — file/env/cli 소스의 우선순위 자유롭게 조정
- **💬 자동 Help 생성** — `--help` 플래그로 모든 옵션과 기본값 표시
- **🪆 Nested 필드 접근** — 점 표기법으로 nested 필드 오버라이드 (database.host=localhost)
- **🧾 Verbosity 제어** — `--quiet`/`--verbose`/`--no-color` 플래그로 출력 수준 조정

---

## 📦 설치

```bash
pip install confee
```

---

## 🚀 빠른 시작

### 기본 사용법

```python
from confee import ConfigBase

class AppConfig(ConfigBase):
    name: str
    debug: bool = False
    workers: int = 4

# 모든 소스에서 파싱 (파일, 환경 변수, CLI)
config = AppConfig.load(config_file="config.yaml")

print(config.name)     # 타입 안전한 접근
print(config.debug)    # 완전한 IDE 지원
print(config.workers)  # 자동완성 지원
```

### YAML 설정 파일

```yaml
name: production-app
debug: false
workers: 8
```

### 명령줄 Override

```bash
python app.py name=my-app debug=true workers=16
```

### 환경 변수

```bash
export CONFEE_NAME=my-app
export CONFEE_DEBUG=true
export CONFEE_WORKERS=16

python app.py
```

### Help 표시

```bash
python app.py --help
```

### 상세한 검증 에러 메시지

기본적으로 검증 에러는 간결하게 표시되지만, `--verbose` 플래그를 사용하면 각 필드별로 상세한 에러 정보를 볼 수 있습니다:

```bash
# 간결한 에러 메시지 (기본값)
python app.py name=123

# 결과:
# Config error: field 'name' - Input should be a valid string

# Verbose 모드로 상세한 에러 메시지 표시
python app.py name=123 --verbose

# 결과:
# ❌ Configuration Validation Error
#
#   Found 1 validation error(s):
#
#   [1] Field: name
#       Error: Input should be a valid string
#       Type: string_type
#       Got: 123
#
#   💡 How to fix:
#     1. Add the required field to your configuration file
#     2. Or pass the value via CLI: python main.py name=myapp
#     3. Or set an environment variable: export CONFEE_NAME=myapp
#     4. Check field types match your configuration class
```

또는 환경 변수로 설정할 수 있습니다:

```bash
export CONFEE_VERBOSITY=verbose
python app.py name=123
```

---

## 🎯 고급 기능

### Nested Configuration

```python
from confee import ConfigBase

class DatabaseConfig(ConfigBase):
    host: str = "localhost"
    port: int = 5432

class AppConfig(ConfigBase):
    name: str
    database: DatabaseConfig

# CLI에서 nested 필드 오버라이드
# python app.py database.host=prod.db database.port=3306
config = AppConfig.load()
print(config.database.host)  # "prod.db"
```

### 파일 참조

```yaml
# config.yaml
name: my-app
api_key: "@file:secrets/api_key.txt"
database_config: "@config:configs/database.yaml"
```

### 커스텀 환경 변수 Prefix

```python
# CONFEE_ 대신 커스텀 prefix 사용
# CONFEE_DEBUG=true 대신 MYAPP_DEBUG=true
config = AppConfig.load(env_prefix="MYAPP_")
```

### 커스텀 Source 순서

```python
# 어느 소스가 다른 소스를 override할지 제어
config = AppConfig.load(
    config_file="config.yaml",
    source_order=["cli", "env", "file"]  # CLI가 가장 높은 우선순위
)
```

### Strict/Non-Strict 모드

```python
# Strict 모드 (기본값): unknown fields 거부
class Config(ConfigBase):
    name: str

# Non-strict 모드: unknown fields 무시
config = Config.load(strict=False)
```

---

## 📚 문서

- [OmegaConf와의 비교](./comparison.ko.md)
- [개발 가이드](./development.ko.md)
- [라이선스](./license)

---

## 🎯 사용 사례

### 환경별 Configuration

```python
# dev.yaml
debug: true
workers: 2

# prod.yaml
debug: false
workers: 32

# 적절한 config 로드
import os
env = os.getenv("APP_ENV", "dev")
config = AppConfig.load(config_file=f"{env}.yaml")
```

### Kubernetes 환경 변수

```yaml
# pod.yaml
containers:
  - env:
    - name: CONFEE_DEBUG
      value: "false"
    - name: CONFEE_WORKERS
      value: "16"
```

### Configuration 검증

```python
from pydantic import Field

class AppConfig(ConfigBase):
    workers: int = Field(ge=1, le=128)  # 범위 검증
    timeout: float = Field(gt=0)         # 양수 필수
```

---

## 🔄 Integration 예제

### FastAPI와 함께

```python
from fastapi import FastAPI
from confee import ConfigBase

class AppConfig(ConfigBase):
    title: str = "My API"
    debug: bool = False

# 파일과 환경 변수에서만 로드 (CLI 제외)
config = AppConfig.load(
    config_file="config.yaml",
    source_order=["env", "file"]
)
app = FastAPI(title=config.title, debug=config.debug)
```

### Click과 함께

```python
import click
from confee import ConfigBase

class AppConfig(ConfigBase):
    name: str

# 파일과 환경 변수에서만 로드 (CLI 제외)
config = AppConfig.load(
    config_file="config.yaml",
    source_order=["env", "file"]
)

@click.command()
def main():
    click.echo(f"Hello {config.name}")
```

---

## ✅ Configuration 테스트

```python
def test_config_loading():
    config = AppConfig.load(
        config_file="tests/fixtures/config.yaml",
        cli_args=["debug=true"],
        strict=True
    )
    assert config.debug is True
```

---

## 🤝 기여하기

기여는 환영합니다! 다음을 수행해주세요:

1. 리포지토리 Fork
2. Feature 브랜치 생성
3. 변경사항에 대한 테스트 작성
4. Pull Request 제출

---

## 📜 라이선스

MIT License © 2025

자세한 내용은 [LICENSE](./license)를 참조하세요.

---

## 💬 지원

문제 및 질문사항:
- GitHub Issues: https://github.com/bestend/confee/issues
- GitHub Discussions: https://github.com/bestend/confee/discussions

---

**즐거운 ☕️ Configuration 관리 되세요!**

---

**언어:** 한국어 | [English](./readme.md)

