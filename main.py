import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# --- 세션 상태 초기화 함수 ---
def initialize_session_state():
    if 'notes' not in st.session_state:
        st.session_state.notes = [] # 모든 노트를 저장할 리스트
    if 'page' not in st.session_state:
        st.session_state.page = 'home' # 현재 페이지 관리
    if 'current_review_index' not in st.session_state:
        st.session_state.current_review_index = 0
    if 'today_review_items' not in st.session_state:
        st.session_state.today_review_items = []
    if 'user_goal' not in st.session_state:
        st.session_state.user_goal = ""

# --- 복습 주기 계산 함수 ---
def calculate_next_review_date(current_date, difficulty, last_interval=0):
    """
    난이도와 이전 복습 간격에 따라 다음 복습 날짜를 계산합니다.
    last_interval: 이전 복습까지의 일수 (첫 복습 시 0)
    difficulty: '쉬웠음', '보통', '어려웠음', '전혀 기억나지 않음'
    """
    if difficulty == '쉬웠음':
        # 이전 간격이 길수록 다음 간격도 더 길게 (지수적으로 증가)
        next_interval = max(1, int(last_interval * 1.8) if last_interval > 0 else 7)
    elif difficulty == '보통':
        # 이전 간격보다 조금 더 길게
        next_interval = max(1, int(last_interval * 1.2) if last_interval > 0 else 3)
    elif difficulty == '어려웠음':
        # 이전 간격보다 짧게, 빠르게 다시 복습
        next_interval = max(1, int(last_interval * 0.5) if last_interval > 0 else 1)
    else: # '전혀 기억나지 않음'
        # 거의 즉시 다시 복습 (내일)
        next_interval = 1
    
    return current_date + timedelta(days=next_interval), next_interval

# --- 페이지 이동 함수 ---
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- Streamlit 앱 시작 ---
st.set_page_config(layout="wide", page_title="망각 곡선 극복 챌린지")

initialize_session_state()

# --- 사이드바 메뉴 ---
with st.sidebar:
    st.title("메뉴")
    if st.button("홈", key="sidebar_home"):
        go_to_page('home')
    if st.button("새 노트 추가", key="sidebar_add_note"):
        go_to_page('add_note')
    if st.button("오늘의 복습", key="sidebar_review"):
        go_to_page('review')
    if st.button("내 학습 통계", key="sidebar_stats"):
        go_to_page('stats')
    st.markdown("---")
    st.info(f"**🎯 나의 목표:** {st.session_state.user_goal or '아직 설정되지 않음'}")

# --- 홈 페이지 ---
if st.session_state.page == 'home':
    st.title("🧠 망각 곡선 극복 챌린지: 나만의 복습 스케줄러")
    st.write("---")

    st.header("💡 에빙하우스의 망각 곡선이란?")
    st.markdown("""
    우리는 학습한 내용을 시간이 지나면서 잊어버리게 됩니다. 독일의 심리학자 에빙하우스는 이 **망각의 패턴**을 연구하여 **'망각 곡선'**을 만들었습니다.
    이 곡선에 따르면, 학습 직후에는 기억이 빠르게 감소하지만, **적절한 시기에 반복적으로 복습**하면 망각 속도를 늦추고 기억력을 오래 유지할 수 있습니다.
    저희 앱은 이 원리를 활용하여 여러분의 학습 효율을 극대화하고, **개인 전담 학습 코치**처럼 작동하여 장기 기억으로 전환을 돕습니다!
    """)
    st.write("---")
    
    st.header("🎯 학습 목표 설정")
    current_goal = st.session_state.user_goal
    new_goal = st.text_input("복습 앱을 통해 달성하고 싶은 학습 목표를 입력해주세요. (예: 파이썬 문법 마스터하기, 영어 단어 1000개 암기)", value=current_goal)
    if st.button("목표 설정 및 저장"):
        st.session_state.user_goal = new_goal
        st.success(f"학습 목표가 '{new_goal}'으로 설정되었습니다!")
        st.experimental_rerun() # 사이드바 업데이트를 위해 새로고침

    st.markdown("---")
    st.write("새로운 지식을 추가하고 복습 스케줄을 시작하려면 '새 노트 추가' 메뉴를 이용해주세요.")


# --- 새 노트 추가 페이지 ---
elif st.session_state.page == 'add_note':
    st.title("➕ 새로운 지식 추가하기")
    st.write("학습할 내용을 입력하고 복습 계획을 세워보세요.")

    note_type = st.radio("노트 유형 선택", ["질답(Q&A) 노트", "외우기(플래시카드) 노트"], key="note_type_radio")

    title = st.text_input("노트 제목 (선택 사항)", help="이 노트의 전체적인 주제를 나타내는 제목입니다.")
    tags = st.text_input("태그 (쉼표로 구분, 예: #영어단어, #물리)", help="나중에 노트를 찾거나 분류할 때 유용합니다.")
    category = st.text_input("카테고리 (선택 사항, 예: TOEIC, 정보처리기사)", help="더 큰 범위의 학습 주제를 지정합니다.")

    content = {}
    if note_type == "질답(Q&A) 노트":
        question = st.text_area("질문 (앞면)", help="스스로에게 질문할 내용을 입력하세요.")
        answer = st.text_area("답변 (뒷면)", help="질문에 대한 정답을 입력하세요.")
        content = {"question": question, "answer": answer}
        review_mode = "주관식/객관식"
    else: # 외우기(플래시카드
