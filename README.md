# Internal Policy RAG Chatbot PoC

오픈소스 NotebookLM 대안인 [Open Notebook](https://github.com/lfnovo/open-notebook)을 RAG 엔진으로 사용해, 사내 규정집을 자연어로 검색하는 챗봇 PoC입니다.

## 목표

### 이번 PoC

- 규정집 Markdown/TXT 파일을 업로드합니다.
- Open Notebook API가 가능하면 Source로 등록하고 RAG/Ask 검색을 호출합니다.
- Open Notebook이 아직 실행되지 않은 환경에서도 mock/fallback 검색으로 데모와 테스트가 가능합니다.
- 사내 규정집 온톨로지로 질문 영역과 위험도를 분류합니다.

### 최종 목표

- Google Drive 규정집 폴더를 자동 수집합니다.
- 신규/수정 문서를 감지해 Open Notebook Source를 갱신합니다.
- 직원이 자연어로 질문하면 규정 조항/출처 기반 답변을 제공합니다.

## 빠른 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

## Open Notebook 실행

Open Notebook을 별도 서비스로 실행하려면:

```bash
cp .env.example .env
# .env에서 OPEN_NOTEBOOK_ENCRYPTION_KEY 등을 변경
mkdir -p open-notebook-runtime
cd open-notebook-runtime
cp ../docker-compose.open-notebook.yml docker-compose.yml
docker compose up -d
```

기본 포트:

- Open Notebook UI: `http://localhost:8502`
- Open Notebook REST API: `http://localhost:5055/api`

## 테스트

```bash
python -m pytest -q
```

## 핵심 구조

```text
src/
  app.py                    # Streamlit PoC UI
  open_notebook_client.py   # Open Notebook REST API adapter
  policy_ontology.py        # 규정집 온톨로지/위험질문 분류
  policy_rag_chain.py       # 질문 → 온톨로지 → RAG/Ask → 안전 답변

data/samples/
  employee-leave-policy.md
  travel-expense-policy.md
  information-security-policy.md
  privacy-policy.md
  policy_ontology.json

docs/
  open-notebook-integration.md
  google-drive-roadmap.md
  safety-policy.md
```

## 안전 원칙

이 챗봇은 사내 규정 안내 도우미입니다. 다음은 거절하거나 담당부서 확인으로 라우팅합니다.

- 징계 회피 방법
- 규정 우회 방법
- 개인정보 유출 방법
- 보안 통제 우회
- 불법/비윤리 행위 조언
- 개별 직원에 대한 법률/징계 판단

## 상태

- PoC용 파일 업로드/샘플 문서 검색: 준비됨
- Open Notebook API 연동 adapter: 준비됨 / 실제 서버 연결은 환경 필요
- Google Drive 자동 수집: 로드맵 문서화 단계
