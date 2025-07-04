# FastAPI 설계

## 준비 사항

1. 가상환경 설정

```
python -m venv venv
```

2. 라이브러리 설치

```
pip install fastapi uvicorn openai python-dotenv
```

3. requirements.txt 만들기

```
pip freeze > requirements.txt
```

4. app.py 생성

- 필요한 라이브러리 불러오기
- 환경 변수 불러오기
- CORS 설정

## 핵심 개념

[참고 사이트](https://brotherdan.tistory.com/40)

### FastAPI의 주요 컴포넌트

1. FastAPI() 객체

- 프레임워크의 핵심으로, 앱 전역 설정이나 이벤트 훅 등을 처리
- `@app.get()`, `@app.post()` 데코레이터를 통해 라우트를 직접 정의할 수도 있음. 하지만 규모가 커지면 라우터(routers)로 분리하는 것이 일반적.

2. 라우트 데코레이터

- `@app.get("/users")`, `@app.post("/items")` 등으로 간단히 경로와 메서드를 지정한다.
- 규모가 커질수록, **APIRouter**를 활용해서 엔드포인트를 **모듈별로 나누는 것**이 권장된다.

3. Dependency Injection

- `Depends()`를 이용해 **DB 세션, 인증 정보, 환경 설정 등**을 깔끔하게 주입할 수 있다.
- 코드의 재사용성과 테스트 편의성을 높여주는 핵심 기능이다.

4. `Pydantic` 스키마

- 모델(`BaseModel`)을 통해 **입력/출력 형식**을 선언적(Declarative)으로 정의한다.
- 요청 바디나 쿼리 파라미터를 **자동 검증**하고, **API 문서화**에도 도움을 준다.

### ※ 디렉토리 구조가 중요한 이유

- **유지보수성** : 파일이 한 곳에 몰려 있으면, 변경 사항을 파악하기 어렵고 충돌이 잦아짐.
- **확장성** : 코드가 커질수록 라우트, 모델, 스키마, 비즈니스 로직 등을 분리해둬야 확장에 유리함.
- **협업** : 팀원들이 코드 위치나 역할을 쉽게 찾고, 충돌을 줄이는 것에 도움이 된다.

### 프로젝트 디렉토리 구조 설계

```plain text

app/
├── main.py              # FastAPI 애플리케이션 엔트리포인트
├── core/                # 설정, 보안, 유틸성 모듈
│    ├── config.py       # 환경 변수 로드, 전역 설정
│    └── security.py     # 인증, JWT 로직 등
├── db/
│    ├── base.py         # Base = declarative_base() 등
│    ├── session.py      # DB 연결 엔진, 세션 생성
│    └── migrations/     # Alembic 마이그레이션 폴더
├── models/              # SQLAlchemy 모델 정의
│    ├── user.py
│    ├── item.py
│    └── ...
├── schemas/             # Pydantic 스키마
│    ├──
│    ├──
│    └──
├── crud/                # DB 처리 로직 (Create, Read, Update, Delete)
│    ├── user.py
│    ├── item.py
│    └── ...
├── api/
│    └── v1/             # 버전별 API (v1, v2 등)
│        ├── endpoints/  # 실제 라우트(엔드포인트)들을 모아둔 디렉토리
│        │   ├── user.py
│        │   ├── item.py
│        │   └── ...
│        └── routers.py  # v1 라우터들을 모아 FastAPI에 등록하는 모듈
├── test/                # 테스트 코드
│    ├── test_user.py
│    ├── test_item.py
│    └── ...
└── celery_app.py        # Celery 초기화 (비동기 작업 필요 시)
```

- main.py = `app = FastAPI()` 인스턴스를 생성하고, 필요한 라우터를 불러와 등록
- core/ : 공통 설정, 보안 관련 로직, 인증 헬퍼 함수 등
- db/ : DB 연결, 세션, 마이그레이션(Alembic) 관련
- models/ : SQLAlchemy ORM 모델
- schemas/ : Pydantic 데이터 검증/직렬화 모델
- crud/ : DB 엑세스 로직 (ORM 사용), 반복적인 CRUD 코드를 깔끔하게 캡슐화
- api/ : FastAPI 라우팅 코드, 엔드포인트들 (Controller) 집합
- tests/ : pytest 기반 테스트

### 라우팅 전략과 APIRouter 사용

- APIRouter란?

    -**FastAPI**는 규모가 커질 경우, 엔트리포인트 하나 (`main.py`)에 모든 라우트를 정의하기 보다는 APIRouter를 사용해 여러 파일로 분리하기를 권장함.
    - `fastapi.APIRouter`를 통해 엔드포인트(함수)들을 그룹핑하고, `app.include_router()`로 메인 앱에 연결할 수 있음.

### 라우팅 best practice

1. URL 명명 규칙

- GET /api/v1/users -> 사용자 목록 조회
- GET /api/v1/users/{user_id} -> 특정 사용자 조회
- POST /api/v1/users -> 사용자 생성
- PUT /api/v1/users/{user_id} or PATCH /api/v1/users/{user_id} -> 사용자 수정
- DELETE /api/v1/users/{user_id} -> 사용자 삭제  
=> 직관적으로 **리소스**(Resource)와 **동작**(CRUD)을 나타내도록 설계

2. 계층적 라우트/네임스페이스

- `@router.get("/{user_id}/items")` : 특정 사용자 소유의 아이템을 조회
- api/v1/endpoints 디렉토리 내에 기능별 파일을 나누어 코드를 분산

3. 메서드와 응답 코드 일관성

- 생성 : POST + 201 Created
- 조회 : GET + 200 OK
- 삭제 : DELETE + 204 No Content

4. API 버전 관리

- 라우터가 늘어날 때, api/v1, api/v2 처럼 버전을 라우트에 명시해두면 안전하게 버전별 호환성을 유지 가능함.

### OpenAPI 문서 자동화

- Swagger UI & Redoc
    - /docs : Swagger UI
    - /redoc : ReDoc 문서 페이지
    - response_model, status_code, **Pydantic** 스키마를 활용하면, API 문서가 자동으로 풍부해짐.