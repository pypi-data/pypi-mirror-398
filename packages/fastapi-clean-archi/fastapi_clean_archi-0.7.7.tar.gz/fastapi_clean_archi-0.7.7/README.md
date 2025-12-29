## FastAPI with Clean-Architecture
> 클린 아키텍처 구조를 적용한 FastAPI.


### Clean Architecture 구조 및 역할
#### 흐름
> interfaces -> application -> domain -> infrastructure

#### 설명
- 클린 아키텍처의 핵심은 관심사의 분리로 유지보수와 확장성을 높일 수 있다.

| Layer       | Description                             |
|-------------|-----------------------------------------|
| Interface   | 사용자/외부 입력을 Application의 유즈케이스에 연결하는 레이어 | 
| Application | 사용자 시나리오(usecase) 및 비즈니스 로직을 실행하는 레이어   |
| Domain       | 핵심 비즈니스 규칙 및 엔티티를 정의하는 레이어              |
| Infrastructure | 외부 시스템\(DB, API 등\)과의 연동 및 구현을 담당하는 레이어 |

**예시** _by github copilot_
- **Interface**: 사용자가 회원가입 폼을 제출하면, API 엔드포인트에서 입력 데이터를 받아 Application 레이어로 전달합니다.
- **Application**: 회원가입 유즈케이스를 실행하며, 입력값 검증, 비밀번호 암호화, 도메인 객체 생성, 트랜잭션 관리 등을 처리합니다.
- **Domain**: `User` 엔티티와 회원가입 관련 비즈니스 규칙(예: 이메일 중복 체크, 비밀번호 정책 등)을 정의합니다.
- **Infrastructure**: DB에 사용자 정보를 저장하고, 이메일 인증을 위해 외부 메일 서비스와 연동합니다.


---

### 기본 사용법
- fastapi-setup 으로 프로젝트 초기화할 수 있습니다.
```bash
fastapi-setup
```

- --help 를 통해 명령어를 확인할 수 있습니다.
```bash
python3 manage.py --help
```

### 커스텀 명령어 추가 방법
- `{PROJECT_DIR}/managements/commands/` 아래 Command 를 상속받아 명령어를 추가할 수 있습니다.
```bash
python3 manage.py {command_name}
```

