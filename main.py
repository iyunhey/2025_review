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
    # 오류 수정: st.text_input 문자열 닫는 따옴표 추가
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
    else: # 외우기(플래시카드)
        front = st.text_area("앞면 (단어/개념)", help="카드 앞면에 보일 내용을 입력하세요. (예: 'apple', '뉴턴의 운동 제1법칙')")
        back = st.text_area("뒷면 (의미/설명)", help="카드 뒷면에 보일 내용을 입력하세요. (예: '사과', '관성의 법칙')")
        content = {"front": front, "back": back}
        review_mode = "플래시카드"

    st.markdown("---")
    st.subheader("💡 이 노트의 추천 복습 모드")
    st.info(f"선택하신 노트 유형에 따라 **'{review_mode}'** 모드로 복습을 진행하게 됩니다.")
    st.write("물론, '오늘의 복습'에서 다른 모드를 선택할 수도 있습니다.")

    if st.button("노트 저장 및 복습 스케줄 생성"):
        # 입력된 내용이 하나라도 비어있는지 확인 (예: 질문만 있고 답변이 없는 경우)
        is_content_empty = False
        if note_type == "질답(Q&A) 노트":
            if not content.get("question") or not content.get("answer"):
                is_content_empty = True
        else: # 외우기(플래시카드) 노트
            if not content.get("front") or not content.get("back"):
                is_content_empty = True

        if is_content_empty:
            st.error("노트의 질문/앞면과 답변/뒷면 내용을 모두 입력해주세요.")
        else:
            today = datetime.now().date()
            # 초기 복습 스케줄 (에빙하우스 곡선 기본)
            initial_review_intervals = [1, 3, 7, 30] 
            
            note_id = len(st.session_state.notes) # 간단한 ID 부여
            
            new_note = {
                "id": note_id,
                "type": note_type,
                "title": title if title else (content.get("front") or content.get("question") or "새 노트")[:30] , # 제목 없으면 내용 앞부분 30자
                "tags": [t.strip() for t in tags.split(',') if t.strip()],
                "category": category,
                "content": content,
                "created_date": today,
                "last_reviewed_date": None,
                "next_review_date": today + timedelta(days=initial_review_intervals[0]), # 첫 복습은 1일 뒤
                "review_history": [], # [{'date': date, 'difficulty': difficulty, 'interval': interval}]
                "current_interval": initial_review_intervals[0], # 현재 적용된 복습 간격
                "initial_review_mode": review_mode # 추천 복습 모드 저장
            }
            st.session_state.notes.append(new_note)
            st.success(f"'{new_note['title']}' 노트가 저장되었고, 복습 스케줄이 생성되었습니다! 🎉")
            st.info(f"첫 복습은 **{new_note['next_review_date'].strftime('%Y년 %m월 %d일')}** 예정입니다.")
            st.balloons()
            st.rerun()


# --- 오늘의 복습 페이지 ---
elif st.session_state.page == 'review':
    st.title("📚 오늘의 복습 시작!")
    st.write("기억을 되살리고 장기 기억으로 전환할 시간입니다!")

    today = datetime.now().date()
    
    # 오늘 복습할 항목 필터링 (아직 복습하지 않은 항목)
    if not st.session_state.today_review_items:
        st.session_state.today_review_items = [
            note for note in st.session_state.notes
            if note['next_review_date'] and note['next_review_date'] <= today
        ]
        # 오래된 복습일수록 먼저 보여주기 위해 정렬
        st.session_state.today_review_items.sort(key=lambda x: x['next_review_date'])

    if not st.session_state.today_review_items:
        st.info("🎉 오늘 복습할 노트가 없네요! 새 노트를 추가하거나 잠시 쉬어가세요.")
        st.markdown("---")
        st.write("**💡 팁:** 새로운 지식을 추가하여 꾸준히 복습 스케줄을 만들어보세요.")
        if st.button("새 노트 추가하러 가기", key="review_go_add_note"):
            go_to_page('add_note')
        st.session_state.current_review_index = 0 # 인덱스 초기화
    else:
        num_to_review = len(st.session_state.today_review_items)
        st.subheader(f"✅ 오늘 복습할 항목: {st.session_state.current_review_index + 1} / {num_to_review}") # 현재 진행 상황 표시

        if st.session_state.current_review_index < num_to_review:
            current_note = st.session_state.today_review_items[st.session_state.current_review_index]

            st.markdown(f"### **'{current_note['title']}'**")
            
            # 복습 모드 선택 (기본은 추천 모드)
            selected_review_mode = st.radio(
                "복습 모드 선택:",
                ["플래시카드", "주관식"], # 이미지 등은 복잡하므로 일단 두 가지로 제한
                index=0 if current_note['initial_review_mode'] == '플래시카드' else 1,
                key=f"mode_select_{current_note['id']}_{st.session_state.current_review_index}" # key 고유하게 만들기
            )

            st.write("---")

            # 플래시카드 모드
            if selected_review_mode == "플래시카드":
                front_content = current_note['content'].get('front') or current_note['content'].get('question')
                back_content = current_note['content'].get('back') or current_note['content'].get('answer')

                st.subheader("💡 앞면")
                st.write(f"**{front_content}**")
                
                # 뒷면 확인 상태를 세션에 저장하여 유지
                if f"show_back_{current_note['id']}_{st.session_state.current_review_index}" not in st.session_state:
                    st.session_state[f"show_back_{current_note['id']}_{st.session_state.current_review_index}"] = False

                if st.button("뒷면 확인", key=f"show_back_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                    st.session_state[f"show_back_{current_note['id']}_{st.session_state.current_review_index}"] = True
                    st.rerun() # 뒷면 표시를 위해 새로고침

                if st.session_state[f"show_back_{current_note['id']}_{st.session_state.current_review_index}"]:
                    st.subheader("✅ 뒷면")
                    st.info(f"**{back_content}**")
            
            # 주관식 모드 (Q&A 형식 노트에 적합)
            elif selected_review_mode == "주관식":
                question_content = current_note['content'].get('question') or current_note['content'].get('front')
                answer_content = current_note['content'].get('answer') or current_note['content'].get('back')

                st.subheader("❓ 질문")
                st.write(f"**{question_content}**")
                
                # 답변 입력 및 확인 상태를 세션에 저장
                if f"user_answer_{current_note['id']}_{st.session_state.current_review_index}" not in st.session_state:
                    st.session_state[f"user_answer_{current_note['id']}_{st.session_state.current_review_index}"] = ""
                if f"answer_checked_{current_note['id']}_{st.session_state.current_review_index}" not in st.session_state:
                    st.session_state[f"answer_checked_{current_note['id']}_{st.session_state.current_review_index}"] = False

                user_answer = st.text_area("답변을 입력하세요.", value=st.session_state[f"user_answer_{current_note['id']}_{st.session_state.current_review_index}"], key=f"user_answer_text_{current_note['id']}_{st.session_state.current_review_index}")
                
                if st.button("답변 확인", key=f"check_answer_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                    st.session_state[f"user_answer_{current_note['id']}_{st.session_state.current_review_index}"] = user_answer # 입력된 답변 저장
                    st.session_state[f"answer_checked_{current_note['id']}_{st.session_state.current_review_index}"] = True
                    st.rerun() # 답변 확인 결과를 표시하기 위해 새로고침

                if st.session_state[f"answer_checked_{current_note['id']}_{st.session_state.current_review_index}"]:
                    st.subheader("✅ 정답")
                    st.info(f"**{answer_content}**")
                    if st.session_state[f"user_answer_{current_note['id']}_{st.session_state.current_review_index}"].strip().lower() == answer_content.strip().lower():
                        st.success("정답입니다!")
                    else:
                        st.error("아쉽지만 틀렸습니다. 다시 한번 확인해보세요.")

            st.write("---")
            st.subheader("이해 난이도 평가:")
            
            # 난이도 평가 버튼을 누르면 바로 다음 노트로 이동 및 데이터 업데이트
            col1, col2, col3, col4 = st.columns(4)
            difficulty_chosen = False

            with col1:
                if st.button("😊 쉬웠음", key=f"diff_easy_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "쉬웠음"
                    difficulty_chosen = True
            with col2:
                if st.button("🙂 보통", key=f"diff_normal_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "보통"
                    difficulty_chosen = True
            with col3:
                if st.button("🙁 어려웠음", key=f"diff_hard_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "어려웠음"
                    difficulty_chosen = True
            with col4:
                if st.button("😩 전혀 기억 안 남", key=f"diff_forgot_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "전혀 기억나지 않음"
                    difficulty_chosen = True

            if difficulty_chosen:
                # 다음 복습일 계산 및 업데이트
                next_review_date, next_interval = calculate_next_review_date(
                    today,
                    selected_difficulty,
                    current_note['current_interval']
                )

                current_note['last_reviewed_date'] = today
                current_note['next_review_date'] = next_review_date
                current_note['current_interval'] = next_interval
                current_note['review_history'].append({
                    'date': today,
                    'difficulty': selected_difficulty,
                    'interval_used': next_interval
                })

                if selected_difficulty in ["어려웠음", "전혀 기억나지 않음"]:
                    st.warning("이 노트를 오답 노트에 추가합니다. 다음에 더 자주 복습하게 됩니다!")
                else:
                    st.success(f"난이도 '{selected_difficulty}'로 평가되었습니다. 다음 복습은 **{next_review_date.strftime('%Y년 %m월 %d일')}**입니다.")

                # 세션 상태에 저장된 임시 변수들 초기화 (다음 복습 항목을 위해)
                for key_prefix in [f"show_back_{current_note['id']}", f"user_answer_{current_note['id']}", f"answer_checked_{current_note['id']}"]:
                    for key in list(st.session_state.keys()):
                        if key.startswith(key_prefix):
                            del st.session_state[key]
                
                # 다음 항목으로 이동
                st.session_state.current_review_index += 1
                st.rerun() # UI 업데이트
        else:
            st.success("🎉 오늘의 복습을 모두 완료했습니다! 정말 수고하셨습니다!")
            st.session_state.today_review_items = [] # 오늘의 복습 목록 초기화
            st.session_state.current_review_index = 0
            if st.button("학습 통계 보러가기", key="review_done_stats"):
                go_to_page('stats')


# --- 내 학습 통계 페이지 ---
elif st.session_state.page == 'stats':
    st.title("📊 내 학습 통계")
    st.write("등록된 노트와 복습 현황을 한눈에 확인하세요.")

    st.subheader(f"🎯 나의 목표: {st.session_state.user_goal or '목표 미설정'}")
    st.markdown("---")
    
    st.subheader("📝 나의 노트 목록")
    if not st.session_state.notes:
        st.info("아직 등록된 노트가 없습니다. '새 노트 추가'에서 새로운 지식을 등록해보세요!")
    else:
        # 데이터프레임으로 보기 좋게 표시
        notes_df_data = []
        for note in st.session_state.notes:
            notes_df_data.append({
                "제목": note['title'],
                "유형": note['type'],
                "카테고리": note['category'],
                "태그": ", ".join(note['tags']),
                "생성일": note['created_date'].strftime('%Y-%m-%d'),
                "마지막 복습일": note['last_reviewed_date'].strftime('%Y-%m-%d') if note['last_reviewed_date'] else "N/A",
                "다음 복습 예정일": note['next_review_date'].strftime('%Y-%m-%d'),
                "복습 횟수": len(note['review_history']),
            })
        
        notes_df = pd.DataFrame(notes_df_data)
        st.dataframe(notes_df, use_container_width=True)

        st.markdown("---")
        st.subheader("오답 노트 (어려웠던 지식)")
        # '어려웠음' 또는 '전혀 기억나지 않음'으로 평가된 이력이 있는 노트 목록
        difficult_notes = []
        for note in st.session_state.notes:
            # 마지막 평가가 어려웠거나 기억 안 나는 경우만 오답 노트에 보여주도록 수정
            if note['review_history'] and note['review_history'][-1]['difficulty'] in ["어려웠음", "전혀 기억나지 않음"]:
                 difficult_notes.append({
                    "제목": note['title'],
                    "유형": note['type'],
                    "마지막 난이도": note['review_history'][-1]['difficulty'],
                    "마지막 평가일": note['review_history'][-1]['date'].strftime('%Y-%m-%d'),
                    "다음 복습 예정일": note['next_review_date'].strftime('%Y-%m-%d')
                })
        
        if difficult_notes:
            difficult_df = pd.DataFrame(difficult_notes)
            st.dataframe(difficult_df, use_container_width=True)
        else:
            st.info("아직 어려운 노트가 없네요! 잘하고 계십니다! 👍")

        st.markdown("---")
        st.subheader("💡 팁: 복습 스케줄")
        st.write("각 노트의 다음 복습 예정일은 당신의 기억 난이도 평가에 따라 자동으로 조절됩니다.")
        st.write("자주 틀리는 내용은 더 짧은 주기로, 쉽게 기억하는 내용은 더 긴 주기로 복습하게 됩니다.")
