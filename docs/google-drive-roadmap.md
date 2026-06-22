# Google Drive Roadmap

## Final Goal

Google Drive 규정집 폴더에 올라오는 문서를 자동 수집해 Open Notebook Source로 등록하고, 자연어 검색 챗봇에서 최신 규정 기반 답변을 제공한다.

## Phases

1. **Manual upload PoC**: 사용자가 Markdown/TXT/PDF를 업로드하고 RAG 검색을 확인한다.
2. **Drive polling**: 지정 folder ID의 파일 목록, modifiedTime, checksum을 주기적으로 확인한다.
3. **Incremental ingestion**: 신규/수정 파일만 다운로드하고 Open Notebook Source로 등록한다.
4. **Version tracking**: 문서명, 개정일, 담당부서, Drive file ID, revision ID를 저장한다.
5. **Access control**: 사용자별 접근권한, 부서별 문서 제한, 감사 로그를 추가한다.

## Required Google Setup

- Google Cloud project
- Drive API enabled
- OAuth client 또는 service account
- Target folder ID
- 최소 권한 원칙: 읽기 전용 scope 우선
