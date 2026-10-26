# Reboot US — 실행 및 운영 안내

README의 기획을 바탕으로 구현한 Flask 웹사이트입니다. 미국 소비자용 기본 언어는 영어이며, 상단 EN / KO로 한국어 안내를 선택할 수 있습니다. 제공된 제품 원본 이미지와 자체 CSS/JavaScript 모션을 사용합니다.

## 바로 실행하기 (Windows PowerShell)

```powershell
cd C:\Users\user\Desktop\reboot_homepage
.\start.ps1
```

접속: <http://127.0.0.1:5000> — 첫 화면은 홈페이지이며 로그인 없이 모든 소개 페이지를 볼 수 있습니다. 로그인은 구매(장바구니·주문)와 관리자 화면에만 필요합니다.

> 5000 포트를 다른 프로그램(예: 별도 `reboot-us-dashboard` 프로젝트)이 쓰고 있으면, 브라우저에 그 프로그램의 로그인 화면이 뜹니다. `start.ps1`은 이를 감지해 5050번 이후 빈 포트로 자동 변경하고 실제 접속 주소를 출력합니다. 포트를 직접 지정하려면 `.\start.ps1 -Port 5080`.

PowerShell 실행 정책 때문에 스크립트를 실행할 수 없으면 다음 명령을 사용합니다.

```powershell
.\.venv\Scripts\python.exe -m flask --app app:create_app run --host 127.0.0.1 --port 5000
```

처음부터 설치하는 PC에서는 Python 3.13 이상으로 가상환경을 만들고 의존성을 설치합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_local.py
.\.venv\Scripts\python.exe -m flask --app app:create_app setup-db
.\.venv\Scripts\python.exe -m flask --app app:create_app run
```

## 생성된 계정

| 계정 | 이메일 | 비밀번호 위치 |
|---|---|---|
| 관리자 | `admin@reboot.example.com` | 로컬 `.env`의 `ADMIN_PASSWORD` |
| 소비자 | `customer@reboot.example.com` | 로컬 `.env`의 `CUSTOMER_PASSWORD` |

위 이메일은 테스트용입니다. 서로 다른 비밀번호를 무작위 생성했습니다. `.env`는 Git 제외 대상입니다. `setup-db`를 다시 실행해도 기존 계정의 비밀번호·역할과 기존 주문을 덮어쓰지 않습니다. 다른 환경에서 사용할 계정 이메일과 비밀번호는 해당 환경 변수로 설정합니다.

회원가입으로는 소비자 계정만 생성됩니다. 관리자 권한은 가입 폼이나 클라이언트 데이터로 부여할 수 없습니다. 로그인은 `/auth/login`, 회원가입은 `/auth/register`, 관리자 화면은 `/admin/`입니다.

## 구현한 기능

- 홈: 제품 카드 스택 부유 모션, 포인터 반응, 맛별 사진 전환, 마키, 스크롤 등장, 제품 캐러셀, 모션 일시정지, OS 모션 감소 설정 지원.
- 언어: 영어·한국어 선택, 주요 화면·폼·안내·정책 번역. 브랜드 슬로건과 일부 디스플레이 타이틀은 영문을 유지합니다. 비회원은 설정 쿠키, 회원은 DB에 언어를 저장합니다.
- 제품: Drink Original / Drink Balance / Jelly Original / Jelly Balance, 각 라임·레몬·체리 이미지, 유형 필터, 음료 낱병·3병 박스 옵션.
- 구매: 계정별 DB 장바구니, 수량 수정·삭제, 모의 주문, 본인 주문 내역, 서버 가격·할인 계산, 중복 제출 방지, 타 계정 데이터 접근 차단.
- 인증: 회원가입, 21세 이상 확인, 비밀번호 확인, 로그인·POST 로그아웃, 기억하기, 만료·폐기 가능한 DB 세션, 해시 비밀번호, 실패 로그인 제한, CSRF 보호.
- 관리자: 날짜·주문 상태·샘플/소비자 주문 필터, 요약 및 월별 차트, 제품·인플루언서 성과, CSV 3종, 활동 기록, 문의·크리에이터 신청함.
- 크리에이터 링크: `/r/NEONNIGHTS` 등 6개, 30일 마지막 클릭 귀속, 클릭 기록, 할인과 수수료 계산.
- 홈 첫 화면 스크롤 무대 (JINRO 첫 화면 참고, `main/index.html` · `core/static/core/home/styles.css` · `core/static/core/home/app.js`): 460vh 섹션 안에서 화면이 고정되고, 스크롤에 따라 제품이 4개 장면을 따라 내려옵니다 — 01 RESTART YOUR DAY(라임 병 주위에 `jelly_3D` 젤리 3개가 떠 있다가 스크롤하면 라임 → 레몬 → 체리 순서로 병 입구로 날아 들어가고, 하나씩 들어갈 때마다 병이 출렁이며 `beverage_3D`의 해당 맛 음료로 바뀝니다) → 02 TAKE A SIP(체리 병) → 03 MAKE IT A BITE(라임 부츠 젤리 + 맛 노트 카드 3장) → 04 FROM KOREA(제품 라인업, 배경이 초록으로 바뀌며 ALDICOM 회사 소개). 거대 타이포는 장면마다 아래에서 밀려 올라오고 위로 빠져나가며, 오른쪽 장면 버튼으로 이동할 수 있습니다. 이미지는 `images/beverage_3D`, `images/jelly_3D` 3D 렌더에서 잘라낸 `core/static/core/img/stage/` 파일입니다.
- 스프리츠 데모: 버튼을 누르면 병이 기울어 들어와 미스트(에어로졸 선·헤이즈·물방울 canvas 파티클)를 뿌리고, 젤리 사진 위에 떨어진 물방울은 약 14초간 반짝이는 방울로 남습니다. 누를 때마다 다른 문구 20개, 리셋 버튼. 연출용이며 섭취 방법 안내가 아님을 표시합니다.
- 홈 3D 제품 캐러셀 (Find Your Reboot, JINRO “Find Your Flavor” 참고): 4종 × 3맛 = 12개를 원형 링에 배치. ◀ ▶ 버튼·썸네일·키보드 좌우·스와이프·마우스 드래그, 무한 루프, power3.inOut 0.9초 회전, 배경색이 맛 대표색(라임 연두·레몬 노랑·체리 핑크, Balance는 옅은 톤)으로 전환, 회전 70% 시점에 제품 패널이 아래에서 올라옴, 중앙 제품 floating. 연타 시 현재 위치에서 새 목표로 다시 이어서 회전. 이미지는 `core/static/core/img/carousel/<slug>-<flavor>/`의 `center.webp`(정면)·`side.webp`(오른쪽)·`side-left.webp`(왼쪽) — 3D 렌더의 정면 뷰에서 배경을 제거하고 좌우로 돌린 모습을 만들었습니다(시트의 3/4 뷰에는 치수선이 있어 사용하지 않음). 양옆은 3D 렌더의 실제 3/4 뷰(치수선 제거)로, 가운데에 오면 정면 렌더로 바뀌어 실제로 돌아가는 것처럼 보입니다. 바닥 그림자·반사·조명을 넣었고, 회전 중에는 속도만큼 흔들리며, 중앙 제품은 떠 있는 동안 그림자가 함께 작아집니다. 알코올 제품이 아니므로 도수 대신 제형·샘플 가격을 표시합니다.
- 젤리 제품 사진: 봉지에 든 사진 대신 `images/jelly_3D` 3D 렌더에서 봉지 없는 젤리만 잘라낸 `images/jelly_3D/products/<original|balance>_<flavor>.webp`(투명 배경)를 제품 목록·상세·장바구니에 사용합니다. 렌더의 흰 바닥·치수선은 제거했습니다. 봉지 사진은 홈 데모 배경·피드 같은 연출 사진에만 남아 있습니다.
- 제품 배경색: 제품 카드·상세·장바구니의 배경이 선택한 맛 색(라임 연두, 레몬 노랑, 체리 핑크, Balance는 옅은 톤)을 따르고, 상세 페이지에서 맛을 바꾸면 배경도 바뀝니다. 사진 뒤 흐린 제품 글씨는 삭제했습니다.
- 브랜드 로고: 제공된 로고 원본을 `images/brand/`에 보관(검정 배경 JPG, 흰 배경 PNG, 투명 배경 PNG 2종, ∞ 마크, 공유 이미지). 헤더·푸터·홈 히어로·About·게임 화면에 투명 로고(`core/static/core/img/reboot-logo-on-dark.webp`)를 사용하고, 파비콘·홈 화면 아이콘은 ∞ 마크로 교체. 사이트 네온 색을 로고 초록(`#61e728`)으로 맞춤.
- 미니게임 Reboot Catch (`/game/`): 회의 메모의 “프로덕트·피드·게임” 구성 반영. 60초 동안 ∞ 마크로 라임·레몬·체리를 받고 스누즈 알람을 피함. 마우스·터치·키보드 조작, 일시정지, 브라우저별 최고 기록, 가장 많이 받은 맛의 제품 페이지 연결, 로그인 회원은 점수를 활동 기록에 저장. 홈에 게임 배너 추가.
- 크리에이터 링크 관리 (`/admin/links`): 관리자가 링크 생성, 이름·플랫폼·할인율·수수료율 수정, 일시중지. 코드는 생성 후 변경 불가(공유된 링크 보호), 비율 변경은 이후 주문에만 적용, 생성·수정은 활동 기록에 저장.
- SEO: Open Graph·Twitter 공유 태그, canonical, `/robots.txt`(관리자·계정·장바구니 제외), `/sitemap.xml`.
- 홈 Where to Buy: 자사몰 + Amazon·Weee!·Yamibuy 채널 배너(Coming soon).
- 기타: About, Feed 3개 글, Where to Buy, Vibe Test, Contact, Creators, Privacy/Terms/Cookies, 오류 페이지, 모바일 메뉴.
- 시드: 고정 난수로 생성한 샘플 주문 1,000건, 제품별 100건 이상, 링크 6개 각각 120건, DIRECT 280건. `paid` 950건 / `refunded` 30건 / `cancelled` 20건.

## DB에 저장되는 내용

SQLite 파일: `instance/reboot.db`. Render 설정은 영구 PostgreSQL을 사용합니다.

| 테이블 | 저장 내용 |
|---|---|
| `auth_user` | 계정, 비밀번호 해시, 역할, 연령 확인 |
| `auth_session` | 로그인 토큰 해시, 만료·로그아웃 시각 |
| `auth_login_attempt` | 실패한 로그인 식별자 해시, 시간 |
| `shop_product`, `shop_product_option` | 제품 4종 및 구매 옵션 6종 |
| `shop_cart_item` | 계정별 SKU·맛·수량 |
| `shop_order`, `shop_order_item` | 주문·품목·금액·배송 입력·귀속 링크 |
| `shop_checkout_ticket` | 일회성 주문 제출 토큰 |
| `shop_referral_link`, `shop_referral_click` | 링크 설정·클릭 시점·카운트 |
| `core_activity` | 가입·로그인·로그아웃·페이지 방문·맛 선택·필터·장바구니·주문·CSV 등 |
| `vibe_result` | 퀴즈 답변·추천 제품 |
| `core_submission` | 문의·크리에이터 신청 |
| `core_preference` | 계정별 언어 설정 |

“로그인해서 사용한 기록을 DB에 저장” 요청에 따라 README의 세션 전용 장바구니 설계를 DB 장바구니로 변경했습니다. 로그인 계정의 방문 URL 경로와 주요 기능 사용을 기록합니다. 비밀번호 원문, 키 입력, 결제 카드 정보는 활동 로그에 저장하지 않습니다. 문의와 퀴즈는 비로그인도 저장되며 계정 식별자는 없는 상태로 저장됩니다.

돈은 `Numeric(10,2)`와 `Decimal`로 계산합니다. 할인은 품목별 반올림 후 합산합니다. CSV는 UTF-8 BOM, 소수점 둘째 자리, 수식 주입 방어를 적용합니다. 대시보드와 CSV에는 같은 필터가 적용됩니다. 기본은 결제 상태 `paid`; 다른 상태를 선택하면 해당 주문의 금액을 보여주며 확정 매출로 취급하지 않습니다. 박스 수량은 박스 단위로 집계합니다.

## 확인 방법

1. 소비자로 로그인 → 제품 상세에서 맛·포장·수량 선택 → Add to bag.
2. 로그아웃·재로그인 후 장바구니가 남아 있는지 확인.
3. `/r/NEONNIGHTS` 접속 → 체크아웃에서 10% 할인 확인 → 모의 주문.
4. 관리자로 로그인 → `/admin/`에서 Data source를 Customer mock orders로 선택.
5. Product sales / Link sales / All matching orders CSV 다운로드.
6. Activity & inbox에서 기록과 문의 확인.

## 검증

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
New-Item -ItemType Directory -Force test-results
.\.venv\Scripts\python.exe -m pytest -q --basetemp test-results/pytest-temp
.\.venv\Scripts\python.exe scripts/browser_check.py
```

- 자동 테스트 51개 (젤리가 병으로 들어가는 장면, 첫 화면 스크롤 무대·데모, 상세 페이지 배경 글씨 제거, 홈 3D 캐러셀, 로고·SEO 파일, 게임 점수 기록, 크리에이터 링크 생성·수정·권한·검증 포함): 공개 페이지, CSRF, 회원가입·권한, 로그아웃 후 기억하기 토큰 폐기, 외부 리다이렉트 차단, 로그인 제한, DB 장바구니, 서버 가격 계산, 주문 중복·소유권, 퀴즈·문의 저장, 샘플 건수·시드 중복 방지, CSV 합계·필터·수식 방어, 언어 설정·한국어 주문 폼.
- Chrome 브라우저 검증 통과: 320/390/768/1024/1440px 반응형, 맛 선택, 로그인, 할인 주문, 퀴즈, 로그아웃, 관리자 CSV 다운로드, 모바일 메뉴·제품 필터, 영어/한국어 전환·한국어 회원가입·모바일 로그아웃, 가로 넘침·JavaScript 오류 검사.
- 브라우저 검증은 별도 테스트 DB를 사용하며 로컬 운영 DB의 계정·주문을 변경하지 않습니다. Windows의 기본 Chrome 경로를 사용하므로 다른 환경에서는 `scripts/browser_check.py`의 브라우저 경로를 조정합니다.
- `test-results/`의 스크린샷과 테스트 DB·CSV는 Git 제외입니다.

## Render 배포 준비

Flask를 실행할 수 있는 Render Web Service + PostgreSQL용 `render.yaml`을 제공했습니다. Sites의 Worker 환경은 README의 Flask 실행 환경과 달라 사용하지 않았습니다. 현재 외부 서비스 배포는 실행하지 않았습니다.

1. 이 소스를 GitHub의 작업 브랜치에서 검토·병합합니다. 사용자 저장소에 자동 push하지 않았습니다.
2. Render에서 이 저장소를 연결하여 Blueprint를 생성합니다.
3. `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `CUSTOMER_EMAIL`, `CUSTOMER_PASSWORD`, `SITE_URL`을 설정합니다. 로컬 테스트 비밀번호와 별도로 설정하십시오.
4. Render가 의존성 설치 → `setup-db` → Gunicorn 시작을 수행합니다. `SECRET_KEY`는 Render가 생성하고 `DATABASE_URL`은 PostgreSQL 서비스에서 연결합니다.
5. 샘플 주문이 필요 없는 새 DB에서는 첫 배포 전 `SEED_DUMMY_DATA=0`으로 설정합니다. 이미 저장된 샘플 주문은 이 설정으로 삭제되지 않습니다.

Blueprint에는 유료 컴퓨팅 플랜이 지정되어 있습니다. 서비스 생성 전에 Render가 표시하는 비용을 확인해야 합니다. 로컬 SQLite 파일을 일시적인 배포 파일시스템에 복사하는 방식은 사용하지 않습니다. `/healthz`는 DB 연결을 검사합니다. HTTPS 환경에서는 `COOKIE_SECURE=1`을 유지합니다.

배포 정의는 [Render Blueprint 문서](https://render.com/docs/blueprint-spec)와 [Flask 배포 문서](https://render.com/docs/deploy-flask)를 기준으로 작성했습니다. PostgreSQL 실제 배포 연결은 아직 검증하지 않았습니다.

## 남은 외부 확정 항목

- README대로 실제 결제·배송은 구현 범위 밖이며 모의 결제입니다.
- 제공된 Balance 음료 원본 이미지에는 `ZERO SUGAR` 문구가 포함되어 있습니다. 사용자 제공 이미지를 그대로 사용했고 홈페이지 카피에는 이 주장을 추가하지 않았습니다. README의 이미지 내 해당 문구 사용 보류 조건을 충족하려면 공개 전에 검토 완료된 패키지 이미지로 교체해야 합니다.
- 가격·최종 성분/알레르기 정보·제품 표시·정책 문구·외부 판매 URL은 출시 확정이 필요합니다. Amazon/Weee/Yamibuy는 링크가 없어 Coming soon으로 표시합니다.
- 문의·신청은 DB 저장 및 관리자 조회까지 제공하며 외부 이메일 발송은 연결하지 않았습니다.
- 인플루언서 링크 6개는 시드 데이터입니다. 신규 링크는 `/admin/links`에서 추가·수정합니다.
- `setup-db`는 최초 스키마와 시드를 만드는 명령입니다. 향후 기존 DB 스키마 변경 시에는 별도 마이그레이션을 추가해야 합니다.

## 소스 위치

`auth/`: 인증 · `shop/`: DB 장바구니/주문/추천 링크 · `products/`: 제품 단일 원본 데이터 · `admin/`: 집계/CSV · `main/`: 홈·소개·콘텐츠·문의·퀴즈 · `core/`: 공통 템플릿/스타일/JS/활동 모델.

JINRO의 구성과 움직임 방향을 참고했으며 이미지·로고·문구·소스는 복사하지 않았습니다. Anton 글꼴은 프로젝트에 포함한 SIL Open Font License로 제공됩니다.
