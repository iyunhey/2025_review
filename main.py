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
    if st.button("오늘의 복습", key="sidebar_review
