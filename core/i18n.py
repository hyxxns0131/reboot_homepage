"""Translate known UI copy without changing submitted values, URLs, or customer data."""
import re
from html import escape
from html.parser import HTMLParser

KO = {
    'About': '브랜드 소개', 'Products': '제품', 'Shop': '스토어', 'Feed': '피드', 'Where to buy': '구매처', 'Vibe test': '취향 테스트', 'Creators': '크리에이터', 'Contact': '문의', 'Login': '로그인', 'Logout': '로그아웃', 'My orders': '내 주문', 'Admin': '관리자', 'Join the crew': '회원가입', 'Skip to content': '본문으로 이동', 'Open menu': '메뉴 열기', 'Close menu': '메뉴 닫기', 'Dismiss notification': '알림 닫기',
    'A NEW RITUAL. FROM KOREA, FOR YOU.': '한국에서 시작된, 나를 위한 새로운 루틴.', 'Good nights. Fresh starts. Your kind of Reboot.': '즐거운 순간, 새로운 시작. 나만의 Reboot.', 'Meet a little ritual with a whole lot of flavor.': '다채로운 맛으로 만나는 작은 일상의 루틴.', 'Find your Reboot': '나만의 Reboot 찾기', 'Meet the brand': '브랜드 만나기', 'DRINK IT. BITE IT. MAKE IT YOURS.': '한 모금, 한 입. 나만의 방식으로.', 'YOUR NEXT CHAPTER STARTS HERE ↗': '당신의 다음 이야기는 여기서 ↗', 'PICK YOUR FLAVOR': '나만의 맛 고르기', '01 — WELCOME TO YOUR REBOOT': '01 — 나만의 REBOOT에 오신 것을 환영합니다', 'SCROLL TO DISCOVER': '스크롤해서 둘러보기', 'THE REBOOT STATE OF MIND': 'REBOOT가 생각하는 일상',
    'Born from ALDICOM in Korea. Made for your everyday rituals in the US. Fruit-forward drinks and jellies, a fresh perspective, and a little moment that’s all yours.': '한국 알디콤에서 시작된 미국 전용 라인. 과일 맛 음료와 젤리로 일상 속 나만의 순간을 만들어 보세요.',
    'FOUR WAYS TO START FRESH': '새로운 시작을 위한 네 가지 선택', 'Explore all': '전체 보기', '3 flavors. Your call.': '세 가지 맛, 나만의 선택.', 'Sample price': '샘플 가격', 'Non-carbonated drink': '비탄산 음료', 'Individually wrapped jelly': '개별 포장 젤리', 'Drink Original': '드링크 오리지널', 'Drink Balance': '드링크 밸런스', 'Jelly Original': '젤리 오리지널', 'Jelly Balance': '젤리 밸런스', 'ORIGINAL OR BALANCE. DRINK OR JELLY.': '오리지널 또는 밸런스. 음료 또는 젤리.', 'ONE RITUAL. ENDLESS POSSIBILITIES.': '다채로운 일상을 위한 작은 루틴.',
    'REBOOT MOMENTS / 001': 'REBOOT의 순간 / 001', 'Your favorite people. A spontaneous playlist.': '좋아하는 사람들, 우연히 발견한 플레이리스트.', 'The little moments make the story.': '작은 순간들이 모여 우리의 이야기가 됩니다.', 'Step into our world': 'Reboot의 일상 보기', 'A LITTLE SELF-DISCOVERY, REBOOT STYLE': 'REBOOT와 함께 알아보는 나의 취향', 'Three quick questions. One flavor of you.': '세 가지 질문으로 찾아보는 나만의 맛.', 'Find my vibe': '나의 취향 찾기', '30 SECONDS. ALL YOU.': '30초면 충분해요.', 'FRESH PERSPECTIVES': '새로운 시선', 'View the feed': '피드 보기', 'NEXT STOP: YOUR EVERYDAY': '다음은 당신의 일상에서', 'Where to find us': '구매처 알아보기',
    'A little ritual. A new beginning.': '작은 루틴, 새로운 시작.', 'From ALDICOM, with a fresh perspective.': '알디콤이 제안하는 새로운 일상.', 'EXPLORE': '둘러보기', 'Our collection': '제품 컬렉션', 'Our story': '브랜드 스토리', 'Find your vibe': '취향 테스트', 'LET’S CONNECT': '함께하기', 'For creators ↗': '크리에이터 협업 ↗', 'Get in touch ↗': '문의하기 ↗', 'Where to buy ↗': '구매처 ↗', 'YOUR REBOOT': '마이 REBOOT', 'Privacy': '개인정보 안내', 'Terms': '이용약관', 'Cookies': '쿠키 안내', 'Pause motion Ⅱ': '모션 일시정지 Ⅱ', 'Resume motion ▷': '모션 재생 ▷', 'Pause animations': '애니메이션 일시정지', 'Resume animations': '애니메이션 재생', 'FOR ADULTS 21+': '만 21세 이상', 'USA / EN': '미국 / 한국어',
    'Brand preview. All prices are sample prices in USD. Checkout is a simulation: no charges or shipments. Product details and packaging are subject to final review.': '브랜드 미리보기입니다. 모든 가격은 USD 기준 샘플이며 모의 결제로 청구·배송되지 않습니다. 제품 정보와 패키지는 최종 검토 후 변경될 수 있습니다.',
    'ORIGINAL / BALANCE · DRINKS / JELLIES': '오리지널 / 밸런스 · 음료 / 젤리', 'Four ways to make it yours. Three flavors to find your favorite.': '네 가지 제품과 세 가지 맛에서 나만의 Reboot를 찾아보세요.', 'All Reboots': '전체 제품', 'Drinks': '음료', 'Jellies': '젤리', 'Balance': '밸런스', 'Original': '오리지널', 'SAMPLE PRICES · USD': '샘플 가격 · USD', 'This is a brand preview. Prices and product details are samples. Mock checkout only.': '브랜드 미리보기입니다. 가격과 제품 정보는 샘플이며 모의 결제만 가능합니다.', '← Back to the collection': '← 전체 제품으로', 'Sample price · USD': '샘플 가격 · USD', '01 / PICK YOUR FLAVOR': '01 / 맛 선택', '02 / CHOOSE YOUR PACK': '02 / 포장 선택', 'Lime': '라임', 'Lemon': '레몬', 'Cherry': '체리', '1 Bottle': '1병', 'Box of 3': '3병 박스', '1 Pouch': '1봉지', 'Quantity': '수량', 'Increase quantity': '수량 늘리기', 'Decrease quantity': '수량 줄이기', 'Add to bag': '장바구니 담기', 'Sign in to shop': '로그인하고 구매하기', 'Shopping is available with a customer account.': '소비자 계정으로 구매 기능을 이용할 수 있습니다.', 'The little details': '제품 자세히 보기', 'Ingredient introduction': '원료 소개', 'About this preview': '미리보기 안내',
    'Big flavor. Fresh perspective.': '풍부한 맛, 새로운 시선.', 'A little bite. A whole new vibe.': '작은 한 입, 새로운 기분.', 'Find a different kind of flow.': '나만의 새로운 흐름을 찾아서.', 'Small ritual. Your own rhythm.': '작은 루틴, 나만의 리듬.',
    'Meet your new plus-one. A non-carbonated drink with a bold burst of fruit flavor, made for the little rituals between your plans.': '일상에 함께할 새로운 친구. 과일의 풍미를 담은 비탄산 음료로 계획 사이사이 나만의 작은 루틴을 만나 보세요.',
    'Pocket-sized flavor for whatever is next. Discover our original jelly collection in three fruit flavors, individually wrapped for easy, everyday moments.': '어디서든 함께하는 작은 맛. 간편하게 즐길 수 있도록 개별 포장된 세 가지 과일 맛의 오리지널 젤리를 만나 보세요.',
    'Your ritual, remixed. Explore the Balance drink collection in lime, lemon, and cherry, in a single bottle or a box made for sharing.': '나의 루틴에 새로운 선택을. 라임·레몬·체리 맛의 밸런스 드링크를 낱병 또는 3병 박스로 만나 보세요.',
    'Make a little room for you. The Balance jelly collection brings three fruit flavors to an easy-to-carry pouch. Pick your flavor and make it your own.': '나를 위한 작은 시간을 만들어 보세요. 휴대하기 편한 밸런스 젤리의 세 가지 과일 맛 중 마음에 드는 맛을 골라 보세요.',
    '1 bottle or a box of 3. Available in lime, lemon, and cherry. Packaging shown is a pre-launch concept and may change.': '낱병 또는 3병 박스. 라임·레몬·체리 맛으로 구성됩니다. 이미지는 출시 전 패키지 콘셉트로 변경될 수 있습니다.', '1 pouch. Available in lime, lemon, and cherry. Packaging shown is a pre-launch concept and may change.': '1봉지. 라임·레몬·체리 맛으로 구성됩니다. 이미지는 출시 전 패키지 콘셉트로 변경될 수 있습니다.', 'A-HAT and Hovenia dulcis (Oriental raisin tree) fruit. Full ingredient, nutrition, and allergen information will be available with final product labeling.': 'A-HAT와 헛개나무 열매를 원료로 소개합니다. 전체 원재료·영양·알레르기 정보는 최종 제품 표시와 함께 제공될 예정입니다.', 'For adults 21+. Sample pricing only. Orders use mock payment with no charges or shipping. This site does not make health or performance claims.': '만 21세 이상을 위한 미리보기입니다. 샘플 가격으로 모의 주문하며 실제 청구·배송되지 않습니다. 건강상 효능을 주장하지 않습니다.',
    'YOUR NEXT CHAPTER': '당신의 새로운 시작', 'COME AS YOU ARE': '지금의 당신 그대로', 'YOUR REBOOT IS WAITING': '나만의 REBOOT가 기다려요', 'Join the crew.': '함께해요.', 'Welcome back.': '다시 만나 반가워요.', 'Make it official. Save your bag, find your flavor, and keep your orders together.': '가입하고 장바구니, 나의 취향, 주문 내역을 한곳에서 관리하세요.', 'Sign in and pick up where you left off.': '로그인하고 이전에 담아 둔 일상을 이어 가세요.', 'Your name': '이름', 'Email address': '이메일 주소', 'Password': '비밀번호', 'Confirm password': '비밀번호 확인', 'Keep me signed in': '로그인 상태 유지', 'I am 21 or older and agree to the Terms and Privacy Policy.': '만 21세 이상이며 이용약관과 개인정보 안내에 동의합니다.', 'Privacy Policy': '개인정보 안내', 'Create my account': '회원가입', 'Let’s go': '로그인', 'Already part of the crew?': '이미 가입하셨나요?', 'New around here?': '처음 오셨나요?', 'Sign in': '로그인', 'Create an account': '회원가입', 'Welcome back. Your next chapter starts here.': '다시 만나 반갑습니다. 새로운 이야기를 시작해 보세요.', 'You’re in. Welcome to the Reboot crew.': '가입되었습니다. Reboot에 오신 것을 환영합니다.', 'You’re signed out. See you next time.': '로그아웃되었습니다. 다음에 또 만나요.', 'Email or password is incorrect.': '이메일 또는 비밀번호를 확인해 주세요.', 'This email is already registered. Please sign in.': '이미 가입된 이메일입니다. 로그인해 주세요.', 'Passwords must match.': '비밀번호가 일치하지 않습니다.', 'Please confirm that you are 21 or older and accept the terms.': '만 21세 이상 및 약관 동의를 확인해 주세요.', 'Sign in to keep your bag and orders together.': '장바구니와 주문을 저장하려면 로그인해 주세요.', 'Too many attempts. Please try again in 15 minutes.': '로그인 시도가 너무 많습니다. 15분 후 다시 시도해 주세요.', 'This field is required.': '필수 입력 항목입니다.', 'Invalid email address.': '이메일 형식을 확인해 주세요.',
    'GOOD CHOICES, ALL YOURS': '당신만의 좋은 선택', 'Saved to your account. Ready when you are.': '계정에 저장되어 언제든 이어서 이용할 수 있어요.', 'Qty': '수량', 'Update': '변경', 'Remove': '삭제', '← Keep exploring': '← 계속 둘러보기', 'THE GOOD STUFF, TOGETHER': '좋은 선택을 한곳에', 'Order summary': '주문 요약', 'Subtotal': '상품 금액', 'Shipping & tax (demo)': '배송비·세금 (데모)', 'Total': '합계', 'Continue to checkout': '주문서 작성', 'Sample prices. Mock checkout only.': '샘플 가격으로 진행하는 모의 주문입니다.', 'No charges. No products shipped.': '실제 청구되거나 배송되지 않습니다.', 'A fresh start.': '새로운 시작.', 'Your bag is empty. Let’s find your first Reboot.': '장바구니가 비어 있어요. 첫 Reboot를 찾아보세요.', 'Explore the collection ↗': '제품 둘러보기 ↗', 'Good choice. Added to your bag.': '좋은 선택이에요. 장바구니에 담았습니다.', 'You can add up to 10 of each flavor and pack.': '맛과 포장별로 최대 10개까지 담을 수 있습니다.', 'Your bag is waiting for a little Reboot.': '장바구니에 Reboot를 담아 보세요.',
    '← Back to your bag': '← 장바구니로', 'ALMOST THERE': '이제 거의 다 왔어요', 'THIS IS A MOCK CHECKOUT': '모의 결제 안내', 'No payment details are collected. You will not be charged and no products will be shipped.': '결제 정보를 수집하지 않습니다. 실제 청구되거나 제품이 배송되지 않습니다.', 'Full name': '수령인 이름', 'City': '도시', 'State': '주', 'Select a state': '주 선택', 'I understand this is a mock order. No payment will be taken and no products will be shipped.': '모의 주문임을 확인했습니다. 실제 결제와 제품 배송이 진행되지 않는 것에 동의합니다.', 'Place order (mock)': '모의 주문 완료', 'Your Reboot lineup': '나의 Reboot 목록', 'Total (sample)': '합계 (샘플)', 'Your order and selected flavors will be saved to your account.': '주문과 선택한 맛이 계정에 저장됩니다.', 'Your mock orders, all in one place.': '나의 모의 주문을 한곳에서 확인하세요.', 'ORDER': '주문', 'Your story starts here.': '이야기의 시작.', 'Your completed mock orders will appear here.': '완료한 모의 주문이 여기에 표시됩니다.', 'Find your first Reboot ↗': '첫 Reboot 찾기 ↗', '← All my orders': '← 전체 주문', 'SAVED TO YOUR ACCOUNT': '계정에 저장되었습니다', 'Mock order confirmed. No payment was taken and no products will be shipped.': '모의 주문이 완료되었습니다. 결제되거나 제품이 배송되지 않습니다.', 'Discount': '할인', 'Keep the good going': '계속 둘러보기', 'paid': '결제 완료', 'refunded': '환불', 'cancelled': '취소',
    'CALLING ALL FRESH PERSPECTIVES': '새로운 시선을 기다립니다', 'LET’S TALK': '함께 이야기해요', 'Got your own take on the Reboot lifestyle? Tell us your story. Let’s make something worth sharing.': '당신만의 Reboot 라이프스타일이 있나요? 이야기를 들려주세요. 함께 나누고 싶은 콘텐츠를 만들어요.', 'A question, an idea, or just a little hello. We’d love to hear from you.': '질문, 아이디어, 짧은 인사도 좋아요. 여러분의 이야기를 기다립니다.', 'Your voice. Our next chapter.': '당신의 목소리로 만드는 다음 이야기.', 'Apply for future collaborations and dedicated referral links. Include your channel, social handle, and the kind of content you love making.': '향후 협업과 전용 추천 링크를 신청하세요. 채널, SNS 계정, 만들고 싶은 콘텐츠를 함께 알려주세요.', 'Creator guidelines: clearly disclose sponsored content (for example, #ad). Keep content adult-focused. Avoid health, treatment, sobriety, or unverified nutrition claims.': '협업 가이드: 광고·협찬 여부를 명확히 표시하세요(예: #ad). 성인 대상 콘텐츠를 제작하고 건강·치료·음주 관련 효능이나 확인되지 않은 영양 표현은 사용하지 마세요.', 'Product questions · Partnership ideas': '제품 질문 · 파트너십 제안', 'Account support · Privacy requests': '계정 지원 · 개인정보 요청', 'Looking to collaborate? ↗': '협업을 원하시나요? ↗', 'Subject': '제목', 'Your message': '내용', 'I agree to the Privacy Policy and to being contacted about this request.': '개인정보 안내에 동의하며 이 요청에 대한 연락을 받는 것에 동의합니다.', 'Read our Privacy Policy': '개인정보 안내 읽기', 'Send my application': '협업 신청하기', 'Send my message': '문의 보내기', 'MESSAGE RECEIVED ↗': '메시지가 접수되었습니다 ↗', 'Your message is saved. Thank you for reaching out to Reboot.': '메시지가 저장되었습니다. Reboot에 연락해 주셔서 감사합니다.', 'Your message is stored for the Reboot team to review.': 'Reboot 팀이 확인할 수 있도록 문의가 저장되었습니다.', 'Your application is stored for the Reboot team to review.': 'Reboot 팀이 확인할 수 있도록 신청이 저장되었습니다.',
    'THE REBOOT VIBE TEST · THREE QUICK QUESTIONS': 'REBOOT 취향 테스트 · 세 가지 질문', 'A playful match for your style. No right or wrong answers.': '가볍게 알아보는 나의 스타일. 정답은 없어요.', 'What’s the plan?': '오늘은 어떤 계획인가요?', 'Out & about': '밖에서 신나게', 'New places. Favorite people. See where it goes.': '새로운 장소, 좋아하는 사람들과 함께.', 'On my own rhythm': '나만의 리듬으로', 'A cozy plan. A good playlist. A little me-time.': '편안한 시간, 좋은 음악, 나만의 여유.', 'Pick your little ritual.': '어떤 작은 루틴이 좋나요?', 'Take a sip': '가볍게 한 모금', 'A little bottle with a lot of personality.': '작은 병 속에 담긴 다채로운 매력.', 'Make it a bite': '즐겁게 한 입', 'A pocket-sized plus-one for my plans.': '주머니 속에서 함께하는 작은 친구.', 'What’s your flavor?': '어떤 맛을 좋아하나요?', 'Bright. Bold. A little unexpected.': '상큼하고 개성 있는 뜻밖의 매력.', 'Sunny with a citrus twist.': '햇살처럼 밝은 시트러스 느낌.', 'Fruit-forward and full of personality.': '과일의 풍미를 담은 나만의 개성.', '← Back': '← 이전', 'Next question ↗': '다음 질문 ↗', 'Show my Reboot ↗': '나의 Reboot 보기 ↗', 'Just for fun. This quiz recommends a style and flavor, not a health benefit.': '재미로 보는 취향 테스트입니다. 스타일과 맛을 추천하며 건강 효능을 안내하지 않습니다.', 'YOUR KIND OF REBOOT': '나만의 REBOOT', 'Meet your match': '추천 제품 보기', 'Go again ↻': '다시 해보기 ↻',
    'YOUR NEXT STOP': '다음 목적지', 'Explore our shop preview. More ways to find us are on the way.': '스토어 미리보기를 둘러보세요. 더 많은 구매처가 준비 중입니다.', 'THE REBOOT SHOP': 'REBOOT 공식 스토어', 'All four Reboots. All three flavors.': '네 가지 Reboot, 세 가지 맛.', 'Try the shopping experience with mock checkout.': '모의 결제로 쇼핑을 체험해 보세요.', 'Explore our shop': '스토어 둘러보기', 'Coming soon': '준비 중', 'Retail availability has not been announced.': '판매 일정은 아직 공개되지 않았습니다.', 'Retailer names indicate planned channels only. No external product listings are available yet.': '표시된 유통사는 예정된 채널이며 외부 판매 링크는 아직 준비되지 않았습니다.',
    'FROM KOREA. WITH A FRESH PERSPECTIVE.': '한국에서 시작된 새로운 시선.', 'THIS IS REBOOT / BY ALDICOM': '알디콤의 REBOOT', 'We’re Reboot, the US line from Korean company ALDICOM. We’re here for the little rituals that make your day feel like yours.': 'Reboot는 한국 기업 알디콤의 미국 전용 라인입니다. 당신의 일상을 더욱 나답게 만드는 작은 루틴을 제안합니다.', 'Our collection is simple: Original and Balance, in fruit-forward drinks and individually wrapped jellies. Lime, lemon, and cherry. A format for your plans. A flavor for your mood.': '오리지널과 밸런스, 과일 맛 음료와 개별 포장 젤리. 라임·레몬·체리로 나의 계획과 기분에 맞는 제품을 골라 보세요.', 'We bring together A-HAT and Hovenia dulcis fruit in our product concepts. Explore the collection for an introduction to each format; complete nutrition and allergen details will accompany final labeling.': '제품 콘셉트에 A-HAT와 헛개나무 열매를 담았습니다. 컬렉션에서 각 제품을 만나 보세요. 전체 영양·알레르기 정보는 최종 제품 표시와 함께 제공됩니다.', 'Meet your next ritual': '새로운 루틴 만나기',
    'A FRESH PERSPECTIVE, ON REPEAT': '새로운 시선으로 만나는 일상', 'Flavor notes, little rituals, and a look into our world.': '맛 이야기와 작은 루틴, Reboot의 일상을 전합니다.', 'Meet your new everyday ritual.': '새로운 일상 속 루틴을 만나 보세요.', 'A little introduction to the Reboot way of doing things.': 'Reboot가 제안하는 일상을 소개합니다.', 'Three flavors. Your kind of energy.': '세 가지 맛, 나만의 분위기.', 'Lime, cherry, or lemon. Where will you start?': '라임, 체리, 레몬. 무엇부터 시작할까요?', 'A pocket-sized plus-one.': '주머니 속 작은 친구.', 'Make room in your plans for something a little different.': '계획 속에 조금 색다른 순간을 더해 보세요.', 'THE REBOOT EDIT': 'REBOOT 이야기', 'FLAVOR NOTES': '맛 이야기', 'LITTLE RITUALS': '작은 루틴', '← Back to the edit': '← 피드로 돌아가기', 'Explore the collection': '컬렉션 둘러보기',
    'REBOOT / ADMINISTRATION': 'REBOOT / 관리자', 'Sales overview': '매출 대시보드', 'A clear view of your Reboot business.': 'Reboot의 주문과 판매 현황을 확인하세요.', 'Activity & inbox ↗': '활동 기록·문의함 ↗', 'PREVIEW DATA': '샘플 데이터', 'Includes 1,000 sample orders and customer mock orders. No real payments. All date filters use UTC.': '샘플 주문 1,000건과 소비자 모의 주문을 포함합니다. 실제 결제는 없으며 날짜 기준은 UTC입니다.', 'Start date': '시작일', 'End date': '종료일', 'Order status': '주문 상태', 'Data source': '데이터 구분', 'All orders': '전체 주문', 'Sample seed data': '샘플 주문', 'Customer mock orders': '소비자 모의 주문', 'Paid': '결제 완료', 'Refunded': '환불', 'Cancelled': '취소', 'All': '전체', 'Apply filters ↗': '필터 적용 ↗', 'Total orders': '총 주문 수', 'Units sold': '판매 수량', 'Pouches, bottles & boxes': '봉지·병·박스 단위', 'Net sales': '할인 후 매출', 'Selected order value': '선택한 주문 금액', 'After discounts · sample USD': '할인 적용 후 · 샘플 USD', 'Not recognized revenue · sample USD': '확정 매출 아님 · 샘플 USD', 'Via creator links': '크리에이터 경유 비중', 'Share of selected order value': '선택한 주문 금액 기준', 'Order value over time': '기간별 주문 금액', 'Monthly totals · selected filters': '월별 합계 · 현재 필터 기준', 'No orders in this date range. Try a wider period or a different source.': '해당 기간에 주문이 없습니다. 기간 또는 데이터 구분을 변경해 보세요.', 'Product performance': '상품별 실적', '↓ Product sales CSV': '↓ 상품별 매출 CSV', 'Product': '상품', 'Orders': '주문 수', 'Units': '판매 수량', 'Boxes': '박스 수량', 'Gross': '할인 전', 'Net': '할인 후', 'No product sales match these filters.': '해당 조건의 상품 매출이 없습니다.', 'Creator link performance': '크리에이터 링크별 실적', '↓ Link sales CSV': '↓ 링크별 매출 CSV', 'Creator names and seeded clicks are fictional. Clicks use the same date and source filters. Conversion = selected orders ÷ clicks.': '샘플 크리에이터와 클릭 수는 가상 데이터입니다. 클릭 수에도 같은 날짜·데이터 필터를 적용합니다. 전환율 = 선택한 주문 수 ÷ 클릭 수.', 'Creator / link': '크리에이터 / 링크', 'Platform': '플랫폼', 'Clicks': '클릭 수', 'Conversion': '전환율', 'Commission': '수수료', 'Recent orders': '최근 주문', '/ latest 15': '/ 최근 15건', '↓ All matching orders CSV': '↓ 조건에 맞는 전체 주문 CSV', 'Order': '주문', 'Date (UTC)': '일시 (UTC)', 'Status': '상태', 'Source': '데이터 구분', 'Referral': '추천 링크', 'Sample seed': '샘플 주문', 'Customer mock': '소비자 모의 주문', 'No matching orders.': '조건에 맞는 주문이 없습니다.', '← Sales overview': '← 매출 대시보드', 'Activity & inbox': '활동 기록·문의함', 'Account activity, customer messages, and creator applications.': '계정 활동, 고객 문의, 크리에이터 신청을 확인하세요.', 'Inbox': '문의함', '/ latest 50': '/ 최근 50건', 'No submissions yet. Contact messages and creator applications will appear here.': '아직 접수된 내용이 없습니다. 문의와 크리에이터 신청이 여기에 표시됩니다.', 'Account activity': '계정 활동 기록', 'Time (UTC)': '일시 (UTC)', 'Account': '계정', 'Event': '활동', 'Page': '페이지', 'Details': '상세', 'Guest': '비회원', 'No recorded activity yet.': '아직 활동 기록이 없습니다.', '← Previous': '← 이전', 'Next →': '다음 →',
    'REBOOT US / BRAND PREVIEW': 'REBOOT US / 브랜드 미리보기', 'Updated October 23, 2026 · Preview policies': '2026년 10월 23일 업데이트 · 미리보기 정책', 'Terms of Use': '이용약관', 'Cookies Policy': '쿠키 안내', 'Contact the team ↗': '팀에 문의하기 ↗', 'What this preview stores': '저장하는 정보', 'Who can access your information': '정보에 접근할 수 있는 사람', 'Retention and requests': '보관 및 요청', 'A preview experience': '미리보기 서비스', 'Accounts and use': '계정 및 이용', 'Product information': '제품 정보', 'Creator participation': '크리에이터 참여', 'Essential cookies': '필수 쿠키', 'Referral attribution': '추천 링크 귀속', 'Display preferences': '화면 설정',
    'A LITTLE PAUSE': '잠시 쉬어가기', 'Back to a fresh start': '홈으로 돌아가기', 'Your form session expired. Refresh the page and try again.': '입력 세션이 만료되었습니다. 새로고침 후 다시 시도해 주세요.', 'Something in that request needs another look.': '입력 내용을 다시 확인해 주세요.', 'This area is for a different account role.': '이 페이지에 접근할 권한이 없습니다.', 'Looks like this page took the night off.': '찾으시는 페이지가 없습니다.', 'That action needs a form submission.': '올바른 양식으로 요청해 주세요.', 'That message is a little too large.': '입력 내용이 너무 큽니다.', 'We hit a little pause. Please try again.': '잠시 오류가 발생했습니다. 다시 시도해 주세요.',
}

KO.update({
    'Logout ↗': '로그아웃 ↗',
    'We believe the moments in between deserve a little attention. The playlist before you head out. The friends around your table. The small rituals you make your own.': '일상 사이사이의 순간에도 관심이 필요하다고 생각합니다. 외출 전 듣는 플레이리스트, 식탁을 함께하는 친구들, 나만의 작은 루틴처럼요.',
    'Reboot is ALDICOM’s line for the United States. Our collection includes Original and Balance, in drinks and individually wrapped jellies. Three fruit flavors bring their own personality to the mix.': 'Reboot는 알디콤의 미국 전용 라인입니다. 오리지널과 밸런스의 음료 및 개별 포장 젤리, 그리고 각자의 개성을 가진 세 가지 과일 맛을 선보입니다.',
    'Pick the format that fits your day, find a flavor you love, and make a little space for what comes next. That is the Reboot spirit.': '오늘에 맞는 제품과 좋아하는 맛을 고르고, 다음 순간을 위한 작은 여유를 만들어 보세요. 이것이 Reboot가 생각하는 일상입니다.',
    'Lime brings a bright citrus personality. Cherry goes bold with a fruit-forward flavor. Lemon keeps things sunny with a familiar citrus note.': '라임은 밝고 개성 있는 시트러스, 체리는 풍부한 과일 풍미, 레몬은 익숙하고 산뜻한 시트러스 느낌을 전합니다.',
    'All three flavors appear across the Reboot collection. Try our Vibe Test for a playful place to start, then explore the product pages to choose your format and pack.': 'Reboot 컬렉션에서 세 가지 맛을 모두 만날 수 있습니다. 취향 테스트로 가볍게 시작한 다음 제품 페이지에서 제형과 포장을 골라 보세요.',
    'Our Vibe Test is a style quiz, not a health assessment. Product availability, packaging, and sample prices may change before launch.': '취향 테스트는 스타일을 알아보는 재미용 퀴즈입니다. 제품 구성, 패키지와 샘플 가격은 출시 전 변경될 수 있습니다.',
    'Some of the best plans start small. A spontaneous coffee catch-up. A favorite song on repeat. Something good tucked into your bag.': '좋은 계획은 작은 것에서 시작되기도 합니다. 즉흥적인 커피 약속, 반복해서 듣는 좋아하는 노래, 가방 속 기분 좋은 작은 선물처럼요.',
    'Meet Reboot Jelly, our individually wrapped jelly collection. Choose Original or Balance and discover lime, cherry, and lemon.': '개별 포장된 Reboot 젤리를 만나 보세요. 오리지널 또는 밸런스를 고르고 라임, 체리, 레몬을 즐겨 보세요.',
    'Keep your routines your own. Reboot is about flavor, format, and those little moments that feel like you.': '나만의 루틴을 지켜 보세요. Reboot는 취향에 맞는 맛과 제형, 나다운 작은 순간을 위한 제품입니다.',
    'When you register, we store your name, email address, password hash, and your confirmation that you are 21 or older. We store login sessions, sign-in and sign-out events, and failed login identifiers as hashes to help protect accounts. Passwords are not stored in plain text.': '가입 시 이름, 이메일, 비밀번호 해시, 만 21세 이상 확인을 저장합니다. 계정 보호를 위해 로그인 세션과 로그인·로그아웃 기록, 실패한 로그인 식별자의 해시를 저장합니다. 비밀번호 원문은 저장하지 않습니다.',
    'When signed in, your visited page paths, cart choices, quantities, quiz results, mock orders, demo delivery details, and referral attribution are saved in the database. Form submissions, including contact and creator applications, are also stored. We do not record keystrokes, payment cards, or the contents of password fields in activity logs.': '로그인 후 방문한 페이지 경로, 장바구니 선택과 수량, 퀴즈 결과, 모의 주문, 데모 배송 정보, 추천 링크 귀속을 DB에 저장합니다. 문의 및 크리에이터 신청도 저장합니다. 키 입력, 카드 정보, 비밀번호 입력값은 활동 로그에 기록하지 않습니다.',
    'You can access your own bag and orders. Authorized Reboot administrators can review orders, activity, and submissions, and export sales records. This preview does not send marketing emails or use advertising trackers.': '이용자는 본인의 장바구니와 주문에 접근할 수 있습니다. 권한 있는 Reboot 관리자는 주문, 활동 기록, 접수 내용과 매출 내보내기를 사용할 수 있습니다. 이 미리보기는 마케팅 이메일이나 광고 추적기를 사용하지 않습니다.',
    'Preview data is retained until the operator removes it. Use the contact form with “Privacy request” as the subject to request access, correction, or deletion. Please use sample delivery information when testing.': '미리보기 데이터는 운영자가 삭제할 때까지 보관합니다. 조회·수정·삭제를 요청하려면 문의 제목을 “개인정보 요청”으로 작성해 주세요. 테스트에는 샘플 배송 정보를 사용해 주세요.',
    'This website previews Reboot, ALDICOM’s US line. All listed prices are sample prices in US dollars. Checkout is a simulation. A mock order does not create a purchase, take payment, or trigger shipment.': '이 웹사이트는 알디콤의 미국 라인 Reboot를 미리 소개합니다. 모든 가격은 USD 기준 샘플입니다. 모의 주문은 실제 구매, 결제, 배송으로 이어지지 않습니다.',
    'Account registration is for adults aged 21 or older. Keep your credentials private. Customer accounts can save a bag and place mock orders. Administrator access is restricted to authorized operators.': '만 21세 이상 성인이 가입할 수 있습니다. 계정 정보를 안전하게 관리하세요. 소비자 계정은 장바구니 저장과 모의 주문을 이용할 수 있으며 관리자 접근은 권한 있는 운영자에게 제한됩니다.',
    'Product concepts, artwork, flavors, and packaging may change. Final labels will provide complete ingredient, nutrition, and allergen information. This preview makes no health, treatment, or performance claims.': '제품 콘셉트, 이미지, 맛, 패키지는 변경될 수 있습니다. 전체 원재료·영양·알레르기 정보는 최종 라벨에 제공됩니다. 이 미리보기는 건강·치료·기능적 효능을 주장하지 않습니다.',
    'Submitting an application does not establish a partnership. Any future sponsored content must clearly disclose the relationship and follow the brand’s confirmed content guidelines.': '신청만으로 협업 관계가 성립하지 않습니다. 향후 협찬 콘텐츠는 해당 관계를 명확히 공개하고 확정된 브랜드 가이드를 따라야 합니다.',
    'We use a session cookie to support sign-in, form security, and flash notifications. If you choose “Keep me signed in,” a remember cookie can keep your session available for up to 30 days. Logging out revokes that session.': '로그인, 입력 보안, 알림을 위해 세션 쿠키를 사용합니다. “로그인 상태 유지”를 선택하면 최대 30일 동안 로그인 세션을 유지할 수 있습니다. 로그아웃하면 해당 세션은 폐기됩니다.',
    'Opening a creator link sets a ref_code cookie for 30 days. The latest valid link determines the preview discount and order attribution. Cart and order records are stored in the database, not in this cookie.': '크리에이터 링크에 접속하면 ref_code 쿠키가 30일 동안 저장됩니다. 가장 최근의 유효한 링크가 할인과 주문 귀속을 결정합니다. 장바구니와 주문은 별도 DB에 저장합니다.',
    'A local browser preference remembers whether you paused motion. It contains no account or shopping data. There are no advertising or third-party analytics cookies in this implementation.': '브라우저에 모션 일시정지 설정을 저장하며 계정·구매 정보는 포함하지 않습니다. 언어 선택은 필수 설정 쿠키와 로그인 계정의 DB 설정에 저장합니다. 광고나 제3자 분석 쿠키는 사용하지 않습니다.',
    'Your quiz result has been saved to your account. A playful recommendation only.': '퀴즈 결과를 계정에 저장했습니다. 재미로 보는 취향 추천입니다.',
    'Your quiz result has been saved. A playful recommendation only.': '퀴즈 결과를 저장했습니다. 재미로 보는 취향 추천입니다.',
    'View more': '자세히 보기', 'Format': '제형', 'Previous flavor': '이전 제품', 'Next flavor': '다음 제품', 'Choose a product': '제품 선택', 'Reboot flavors. Use left and right arrow keys to rotate.': 'Reboot 제품. 왼쪽·오른쪽 화살표 키로 돌려 보세요.',
    # Home stage (scroll scenes) and spritz demo
    'Meet Reboot': 'Reboot 소개', '01 — MEET REBOOT': '01 — REBOOT를 소개합니다', 'A little ritual for what’s next.': '다음을 위한 작은 루틴.',
    'Fruit-forward drinks and jellies from ALDICOM. Lime, lemon, and cherry. Pick your mood.': 'ALDICOM이 만든 과일 향 가득한 드링크와 젤리. 라임, 레몬, 체리 중 오늘의 기분을 골라 보세요.',
    '02 — THE DRINK': '02 — 드링크', 'Reboot Drink': 'Reboot 드링크', 'A non-carbonated, pocket-sized bottle in Original and Balance. One bottle, or a box of three.': '오리지널과 밸런스로 만나는 주머니 크기의 비탄산 음료. 한 병 또는 3병 박스로 만나 보세요.', 'Meet the drink': '드링크 보기',
    '03 — THE JELLY': '03 — 젤리', 'Reboot Jelly': 'Reboot 젤리', 'Individually wrapped jellies with a little attitude: the lime boot, the lemon lasso, and the cherry hat.': '개성 있는 개별 포장 젤리: 라임 부츠, 레몬 올가미, 체리 모자.', 'Meet the jelly': '젤리 보기',
    '04 — ABOUT US': '04 — 회사 소개', 'Made by ALDICOM.': 'ALDICOM이 만듭니다.', 'Reboot is the US line from ALDICOM, a Korean company. We bring a Korean after-party ritual to your everyday, with a fresh perspective.': 'Reboot는 한국 기업 ALDICOM의 미국 전용 라인입니다. 한국의 애프터파티 루틴을 새로운 시선으로 당신의 일상에 전합니다.', 'Our story': '브랜드 스토리',
    'Jump to a chapter': '장면 이동', 'Restart': '리스타트', 'Drink': '드링크', 'Jelly': '젤리', 'The boot': '부츠', 'The lasso': '올가미', 'The hat': '카우보이 모자',
    'TRY IT · A LITTLE SPRITZ': '체험 · 살짝 뿌려 보기', 'GIVE IT A LITTLE': '살짝 더하는', 'sparkle.': '반짝임.', 'Tap the button and watch Reboot add a fresh little sparkle.': '버튼을 눌러 Reboot가 더하는 산뜻한 반짝임을 확인해 보세요.',
    'Psst, give it a spritz': '칙, 뿌리기', 'One more': '한 번 더', 'Reset': '다시 하기', 'Sprays': '뿌린 횟수', 'Just for fun. An animation, not a serving suggestion.': '재미로 보는 애니메이션이며, 섭취 방법 안내가 아닙니다.',
    'A little sparkle, instantly.': '반짝, 바로 생기가 돌아요.', 'Fresh start, coming right up.': '새로운 시작, 바로 준비 완료.', 'Look at that glow.': '이 반짝임 좀 보세요.', 'Lime-bright. Lemon-light. Cherry-sweet.': '라임처럼 산뜻하게, 레몬처럼 가볍게, 체리처럼 달콤하게.',
    'Your jelly says thank you.': '젤리가 고맙대요.', 'Again? We like your style.': '또요? 취향 좋으시네요.', 'That’s the Reboot glow.': '이게 바로 Reboot 글로우.', 'Small ritual, big mood.': '작은 루틴, 큰 기분 전환.', 'Nice rhythm. Keep going.': '리듬 좋아요. 계속해요.',
    'Ten sprays. Officially a ritual.': '열 번째. 이제 공식 루틴이에요.', 'Shine on.': '계속 반짝이세요.', 'Fresh looks good on you.': '산뜻함이 잘 어울려요.', 'Restart, repeat.': '리스타트, 그리고 반복.', 'Brighter by the minute.': '점점 더 반짝반짝.', 'Okay, now it’s glowing.': '좋아요, 이제 빛이 나요.',
    'You’ve got the touch.': '손맛이 있으시네요.', 'Almost a sparkle storm.': '거의 반짝이 폭풍이에요.', 'Fresh perspective, unlocked.': '새로운 시선, 잠금 해제.', 'One more for luck.': '행운을 위해 한 번 더.', 'Twenty! You’re a natural.': '스무 번! 타고나셨네요.', 'Still fresh. Still you.': '여전히 산뜻하게, 여전히 나답게.',
    # Brand logo, Reboot Catch game, creator link admin, home additions
    'Reboot home': 'Reboot 홈', 'Reboot Catch': 'Reboot 캐치', 'Play Reboot Catch': 'Reboot 캐치 플레이', 'REBOOT ARCADE · 60 SECONDS OF FUN': 'REBOOT 아케이드 · 60초 미니게임', 'Catch.': '캐치.',
    'Catch lime, lemon, and cherry. Dodge the snooze clocks. Three snoozes and it’s time to reboot.': '라임, 레몬, 체리를 받고 스누즈 알람은 피하세요. 알람에 세 번 걸리면 다시 시작합니다.',
    'Score': '점수', 'Combo': '콤보', 'Time': '시간', 'Snoozes': '스누즈', 'Best': '최고 기록', 'READY TO RESTART?': '다시 시작할 준비 됐나요?',
    'Move with your mouse, finger, or ← → keys.': '마우스, 손가락 또는 ← → 키로 움직이세요.', 'Lime +10': '라임 +10', 'Lemon +10': '레몬 +10', 'Cherry +10': '체리 +10', 'Snooze −1 life': '스누즈 −1 목숨',
    'Start the game': '게임 시작', 'PAUSED.': '일시정지.', 'Take a breath. Your score is waiting.': '잠깐 쉬어 가세요. 점수는 그대로입니다.', 'Resume': '계속하기', 'GAME OVER': '게임 종료', 'POINTS.': '점.',
    'New personal best ✳': '개인 최고 기록 ✳', 'Your flavor this round:': '이번 판의 맛:', 'Play again': '다시 하기', 'Meet this flavor': '이 맛 보러 가기', 'Pause Ⅱ': '일시정지 Ⅱ',
    'Space: start / pause · Best score is saved in this browser only.': 'Space: 시작 / 일시정지 · 최고 기록은 이 브라우저에만 저장됩니다.',
    'Just for fun. A game about fruit and fresh starts — no prizes, no purchase required.': '재미로 즐기는 게임입니다. 경품이나 구매 조건은 없습니다.',
    'Reboot Catch game area. Move the Reboot mark to catch falling fruit and avoid snooze clocks.': 'Reboot 캐치 게임 화면. Reboot 마크를 움직여 떨어지는 과일을 받고 스누즈 알람을 피하세요.',
    'REBOOT ARCADE / NEW': 'REBOOT 아케이드 / NEW', 'CATCH THE': '잡아라,', 'fresh start.': '새로운 시작.', 'Lime, lemon, cherry. Dodge the snooze. Sixty seconds to beat your best.': '라임, 레몬, 체리. 스누즈는 피하고, 60초 안에 최고 기록에 도전하세요.',
    'Reboot Shop': 'Reboot 스토어', 'Open · preview': '오픈 · 미리보기',
    'Creator links ↗': '크리에이터 링크 ↗', 'Creator links': '크리에이터 링크', '← Creator links': '← 크리에이터 링크', 'Creator Links': '크리에이터 링크', 'Edit Creator Link': '크리에이터 링크 수정',
    'Create, pause, and adjust creator links. Rate changes apply to future orders only.': '크리에이터 링크를 만들고, 일시중지하고, 조정합니다. 비율 변경은 이후 주문에만 적용됩니다.',
    'New creator link': '새 크리에이터 링크', 'Link code': '링크 코드', 'Creator name': '크리에이터 이름', 'Customer discount (%)': '고객 할인율 (%)', 'Creator commission (%)': '크리에이터 수수료율 (%)', 'Link is active': '링크 활성화',
    'Create link ↗': '링크 만들기 ↗', 'Save changes ↗': '변경 사항 저장 ↗', 'All links': '전체 링크', 'Edit ↗': '수정 ↗', 'Active': '활성', 'Paused': '일시중지', 'No creator links yet.': '아직 크리에이터 링크가 없습니다.',
    'Codes use letters and numbers and are saved in capitals. A code cannot be changed after it is created, so shared links keep working. Use fictional names for test links.': '코드는 영문과 숫자만 사용하며 대문자로 저장됩니다. 공유된 링크가 계속 작동하도록 생성 후에는 코드를 바꿀 수 없습니다. 테스트 링크에는 가상의 이름을 사용하세요.',
    'Past orders keep the discount and commission they were placed with.': '이전 주문은 주문 당시의 할인과 수수료를 유지합니다.',
    'Pausing a link turns off its URL and stops its discount and attribution on new orders.': '링크를 일시중지하면 URL이 비활성화되고 새 주문에 할인과 귀속이 적용되지 않습니다.',
    'Use letters and numbers only.': '영문과 숫자만 사용하세요.', 'This code is already in use.': '이미 사용 중인 코드입니다.', 'Enter 0 or more.': '0 이상을 입력하세요.', 'Number must be between 0 and 50.': '0에서 50 사이의 숫자를 입력하세요.',
})


def translate(text):
    normalized = re.sub(r'\s+', ' ', text.strip())
    result = KO.get(normalized)
    if result is not None:
        return text[:len(text) - len(text.lstrip())] + result + text[len(text.rstrip()):]
    for english, korean in [('Reboot Drink Original', 'Reboot 드링크 오리지널'), ('Reboot Drink Balance', 'Reboot 드링크 밸런스'), ('Reboot Jelly Original', 'Reboot 젤리 오리지널'), ('Reboot Jelly Balance', 'Reboot 젤리 밸런스')]:
        if normalized == english:
            return text.replace(english, korean)
    if normalized.startswith('Your flavor: '):
        return '나의 맛: ' + KO.get(normalized[13:], normalized[13:])
    if normalized.startswith('Shopping bag, '):
        return re.sub(r'Shopping bag, (\d+) items', r'장바구니, \1개', normalized)
    if normalized.endswith(' · ALDICOM US'):
        title = normalized.removesuffix(' · ALDICOM US')
        return KO.get(title, title) + ' · ALDICOM US'
    return text


class KoreanHTML(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        blocked = tag in ('script', 'style', 'textarea', 'code') or 'data-no-i18n' in attr_map or any(block for _, block in self.stack)
        if tag not in self.VOID:
            self.stack.append((tag, blocked))
        changed = False
        result = []
        for key, value in attrs:
            if key in ('aria-label', 'title', 'placeholder') and value and not blocked:
                translated = translate(value)
                changed = changed or translated != value
                value = translated
            result.append((key, value))
        if changed:
            self.output.append('<' + tag + ''.join(' ' + k + ('="' + escape(v, quote=True) + '"' if v is not None else '') for k, v in result) + '>')
        else:
            self.output.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break
        self.output.append('</' + tag + '>')

    def handle_data(self, data):
        if any(block for _, block in self.stack):
            self.output.append(data)
        else:
            translated = translate(data)
            self.output.append(escape(translated, quote=False) if translated != data else data)

    def handle_entityref(self, name):
        self.output.append('&' + name + ';')

    def handle_charref(self, name):
        self.output.append('&#' + name + ';')

    def handle_comment(self, data):
        self.output.append('<!--' + data + '-->')

    def handle_decl(self, decl):
        self.output.append('<!' + decl + '>')


def korean_html(html):
    parser = KoreanHTML()
    parser.feed(html)
    parser.close()
    return ''.join(parser.output)
