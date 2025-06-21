import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# --- 세션 상태 초기화 함수 ---
def initialize_session_state():
    if 'notes' not in st.session_state:
        st.session_state.notes = []
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'current_review_index' not in st.session_state:
        st.session_state.current_review_index = 0
    if 'today_review_items' not in st.session_state:
        st.session_state.today_review_items = []
    if 'user_goal' not in st.session_state:
        st.session_state.user_goal = ""
    if 'selected_review_notes' not in st.session_state:
        st.session_state.selected_review_notes = []
    if 'is_manual_review' not in st.session_state:
        st.session_state.is_manual_review = False

# --- 복습 주기 계산 함수 ---
def calculate_next_review_date(current_date, difficulty, last_interval=0):
    if difficulty == '쉬웠음':
        next_interval = max(1, int(last_interval * 1.8) if last_interval > 0 else 7)
    elif difficulty == '보통':
        next_interval = max(1, int(last_interval * 1.2) if last_interval > 0 else 3)
    elif difficulty == '어려웠음':
        next_interval = max(1, int(last_interval * 0.5) if last_interval > 0 else 1)
    else:
        next_interval = 1
    return current_date + timedelta(days=next_interval), next_interval

# --- 페이지 이동 함수 ---
def go_to_page(page_name):
    st.session_state.page = page_name
    st.session_state.current_review_index = 0
    st.session_state.today_review_items = []
    st.session_state.selected_review_notes = []
    st.session_state.is_manual_review = False
    st.rerun()

# --- Streamlit 앱 설정 ---
st.set_page_config(layout="wide", page_title="망각 곡선 극복 챌린지")
initialize_session_state()

# --- 사이드바 ---
with st.sidebar:
    st.title("메뉴")
    if st.button("홈", key="sidebar_home"):
        go_to_page('home')
    if st.button("새 노트 추가", key="sidebar_add_note"):
        go_to_page('add_note')
    if st.button("오늘의 복습", key="sidebar_review"):
        go_to_page('review')
    if st.button("선택 복습", key="sidebar_manual_review"):
        go_to_page('manual_review')
    if st.button("내 학습 통계", key="sidebar_stats"):
        go_to_page('stats')
    st.markdown("---")
    st.info(f"**🎯 나의 목표:** {st.session_state.user_goal or '아직 설정되지 않음'}")

# --- 리뷰 모듈 함수 정의 ---
def review_module(review_items):
    today = datetime.now().date()
    num_to_review = len(review_items)

    if not review_items:
        st.info("🎉 현재 복습할 노트가 없습니다! 새 노트를 추가하거나 잠시 쉬어가세요.")
        if st.button("새 노트 추가하러 가기", key="review_go_add_note_common"):
            go_to_page('add_note')
        st.session_state.current_review_index = 0
        st.session_state.today_review_items = []
        st.session_state.selected_review_notes = [] 
        st.session_state.is_manual_review = False
        return

    if st.session_state.current_review_index >= num_to_review:
        st.success("🎉 복습을 모두 완료했습니다! 정말 수고하셨습니다!")
        if st.button("학습 통계 보러가기", key="review_done_stats_common"):
            go_to_page('stats')
        st.session_state.current_review_index = 0
        st.session_state.today_review_items = []
        st.session_state.selected_review_notes = [] 
        st.session_state.is_manual_review = False
        return

    current_note = review_items[st.session_state.current_review_index]
    st.markdown(f"### **'{current_note['title']}'**")

    content = current_note['content']
    front = content.get('front') or content.get('question')
    back = content.get('back') or content.get('answer')

    st.write("**앞면:**", front)
    if st.button("뒷면 보기", key=f"show_back_{current_note['id']}"):
        st.write("**뒷면:**", back)

    if st.button("쉬웠음", key=f"easy_{current_note['id']}"):
        next_date, interval = calculate_next_review_date(today, '쉬웠음', current_note.get('current_interval', 1))
        current_note['next_review_date'] = next_date
        current_note['current_interval'] = interval
        st.session_state.current_review_index += 1
        st.rerun()
    if st.button("보통", key=f"normal_{current_note['id']}"):
        next_date, interval = calculate_next_review_date(today, '보통', current_note.get('current_interval', 1))
        current_note['next_review_date'] = next_date
        current_note['current_interval'] = interval
        st.session_state.current_review_index += 1
        st.rerun()
    if st.button("어려웠음", key=f"hard_{current_note['id']}"):
        next_date, interval = calculate_next_review_date(today, '어려웠음', current_note.get('current_interval', 1))
        current_note['next_review_date'] = next_date
        current_note['current_interval'] = interval
        st.session_state.current_review_index += 1
        st.rerun()
    if st.button("전혀 기억나지 않음", key=f"forgot_{current_note['id']}"):
        next_date, interval = calculate_next_review_date(today, '전혀 기억나지 않음', current_note.get('current_interval', 1))
        current_note['next_review_date'] = next_date
        current_note['current_interval'] = interval
        st.session_state.current_review_index += 1
        st.rerun()

# --- 홈 페이지 ---
if st.session_state.page == 'home':
    st.title("🧠 망각 곡선 극복 챌린지: 나만의 복습 스케줄러")
    st.write("홈 페이지입니다.")

# --- 새 노트 추가 페이지 ---
elif st.session_state.page == 'add_note':
    st.title("➕ 새로운 지식 추가하기")
    st.write("새 노트를 추가하는 페이지입니다.")

# --- 선택 복습 페이지 ---
elif st.session_state.page == 'manual_review':
    st.title("📖 원하는 노트 선택해서 복습하기")
    st.session_state.is_manual_review = True
    st.write("선택 복습 페이지입니다.")

# --- 오늘의 복습 페이지 ---
elif st.session_state.page == 'review':
    st.title("📚 오늘의 복습 시작!")
    st.session_state.is_manual_review = False
    today = datetime.now().date()
    if not st.session_state.today_review_items or st.session_state.current_review_index == 0:
        st.session_state.today_review_items = [
            note for note in st.session_state.notes
            if note['next_review_date'] and note['next_review_date'] <= today
        ]
        st.session_state.today_review_items.sort(key=lambda x: x['next_review_date'])
    review_module(st.session_state.today_review_items)

# --- 통계 페이지 ---
elif st.session_state.page == 'stats':
    st.title("📊 내 학습 통계")
    st.write("통계 페이지입니다.")

