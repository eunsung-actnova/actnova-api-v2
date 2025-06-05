## 협업 방식
- feature별로 branch를 생성하여 개발
- 리뷰어를 위해 PR 생성 전 충분히 테스트해보고 올릴 것.
    - 간단한 설명 첨부
    - 최대한 PR에 관련된 코드만 포함할 것

<br></br>


## 테스트 작성(가장 중요)
- 개발 주기를 단축시킬 수 있는 테스트 작성
- 테스트하는 기능 외의 다른 부분은 대체할 수 있도록 코드 작성(e.g 가짜 객체)

<br></br>

## 테스트 관리
- pytest
- [test container](https://testcontainers.com/guides/getting-started-with-testcontainers-for-python/)

<br></br>
## 라이브러리 관리

- 모든 Python 패키지는 uv로 관리합니다.
- 의존성 추가 시 반드시 pyproject.toml에 추가 후, 아래 명령어로 lock 파일을 갱신합니다.
- 의존성 추가 및 lock 파일 갱신
    ```sh
    uv pip add <패키지명>
    uv pip compile pyproject.toml
    ```

<br></br>