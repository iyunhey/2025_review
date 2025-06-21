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
    # 선택 복습을 위한 변수 추가 (기존 코드에 없던 부분이지만, 복습 모듈 확장 시 필요하여 추가)
    if 'selected_review_notes' not in st.session_state:
        st.session_state.selected_review_notes = []
    if 'is_manual_review' not in st.session_state: # 수동/자동 복습 구분
        st.session_state.is_manual_review = False


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
    # 페이지 이동 시 복습 관련 세션 상태 초기화 추가
    st.session_state.current_review_index = 0
    st.session_state.today_review_items = []
    st.session_state.selected_review_notes = [] 
    st.session_state.is_manual_review = False
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
    # 선택 복습 메뉴 추가 (이전 요청에서 추가되었으나, 이번 요청 범위에 맞춰 주석 처리 또는 제거 가능)
    # 여기서는 유지하겠습니다.
    if st.button("선택 복습", key="sidebar_manual_review"):
        go_to_page('manual_review')
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
        st.rerun() # 사이드바 업데이트를 위해 새로고침

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
        review_mode = "주관식" # 질답 노트는 주관식으로
    else: # 외우기(플래시카드)
        front = st.text_area("앞면 (단어/개념)", help="카드 앞면에 보일 내용을 입력하세요. (예: 'apple', '뉴턴의 운동 제1법칙')")
        back = st.text_area("뒷면 (의미/설명)", help="카드 뒷면에 보일 내용을 입력하세요. (예: '사과', '관성의 법칙')")
        content = {"front": front, "back": back}
        review_mode = "플래시카드" # 플래시카드는 플래시카드로

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
    if not st.session_state.today_review_items: # 목록이 비어있으면 새로 불러오기 (첫 진입 또는 복습 완료 후)
        st.session_state.today_review_items = [
            note for note in st.session_state.notes
            if note['next_review_date'] and note['next_review_date'] <= today
        ]
        # 오래된 복습일수록 먼저 보여주기 위해 정렬
        st.session_state.today_review_items.sort(key=lambda x: x['next_review_date'])

    # 복습할 항목이 없는 경우
    if not st.session_state.today_review_items:
        st.info("🎉 오늘 복습할 노트가 없네요! 새 노트를 추가하거나 잠시 쉬어가세요.")
        st.markdown("---")
        st.write("**💡 팁:** 새로운 지식을 추가하여 꾸준히 복습 스케줄을 만들어보세요.")
        if st.button("새 노트 추가하러 가기", key="review_go_add_note"):
            go_to_page('add_note')
        st.session_state.current_review_index = 0 # 인덱스 초기화
        # 여기서 함수를 종료하여 아래 복습 로직이 실행되지 않도록 함
        # 이 부분이 이전 오류의 핵심 원인 중 하나일 수 있습니다.
        # 이 else 블록에서 return이 없으면, 비어있는 리스트에 접근하려 할 수 있습니다.
        # 그러나 Streamlit의 작동 방식상, UI가 렌더링되면서 자연스럽게 페이지 전환이 이루어지므로
        # 명시적인 return은 필수적이지 않을 수 있지만, 안전을 위해 남겨둡니다.
    else:
        num_to_review = len(st.session_state.today_review_items)

        # 모든 복습을 완료한 경우
        if st.session_state.current_review_index >= num_to_review:
            st.success("🎉 오늘의 복습을 모두 완료했습니다! 정말 수고하셨습니다!")
            st.session_state.today_review_items = [] # 오늘의 복습 목록 초기화
            st.session_state.current_review_index = 0 # 인덱스 초기화
            if st.button("학습 통계 보러가기", key="review_done_stats"):
                go_to_page('stats')
            # 모든 복습 완료 후에는 더 이상 복습 로직을 실행하지 않도록 함수를 여기서 종료합니다.
            # 이 return 문이 중요합니다.
            # 이전에 이 부분이 없어서, 모든 복습 완료 메시지 이후에도
            # current_note = ... 와 같은 라인에 접근하려다 오류가 났을 수 있습니다.
            return 


        # 복습 진행 중
        current_note = st.session_state.today_review_items[st.session_state.current_review_index]

        st.subheader(f"✅ 오늘 복습할 항목: {st.session_state.current_review_index + 1} / {num_to_review}") # 현재 진행 상황 표시
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

            st.subheader("💡 앞면 (단어/개념)")
            st.write(f"**{front_content}**")
            
            # 뒷면 확인 상태를 세션에 저장하여 유지
            unique_key_show_back = f"show_back_{current_note['id']}_{st.session_state.current_review_index}"
            if unique_key_show_back not in st.session_state:
                st.session_state[unique_key_show_back] = False

            if st.button("정답 확인", key=f"show_back_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                st.session_state[unique_key_show_back] = True
                st.rerun() # 뒷면 표시를 위해 새로고침

            if st.session_state[unique_key_show_back]:
                st.subheader("✅ 뒷면 (의미/설명)")
                st.info(f"**{back_content}**")
        
        # 주관식 모드 (Q&A 형식 노트에 적합)
        elif selected_review_mode == "주관식":
            question_content = current_note['content'].get('question') or current_note['content'].get('front')
            answer_content = current_note['content'].get('answer') or current_note['content'].get('back')

            st.subheader("❓ 질문 (앞면)")
            st.write(f"**{question_content}**")
            
            # 답변 입력 및 확인 상태를 세션에 저장
            unique_key_user_answer = f"user_answer_{current_note['id']}_{st.session_state.current_review_index}"
            unique_key_answer_checked = f"answer_checked_{current_note['id']}_{st.session_state.current_review_index}"

            if unique_key_user_answer not in st.session_state:
                st.session_state[unique_key_user_answer] = ""
            if unique_key_answer_checked not in st.session_state:
                st.session_state[unique_key_answer_checked] = False

            user_answer = st.text_area("답변을 입력하세요.", value=st.session_state[unique_key_user_answer], key=f"user_answer_text_{current_note['id']}_{st.session_state.current_review_index}")
            
            if st.button("정답 확인", key=f"check_answer_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                st.session_state[unique_key_user_answer] = user_answer # 입력된 답변 저장
                st.session_state[unique_key_answer_checked] = True
                st.rerun() # 답변 확인 결과를 표시하기 위해 새로고침

            if st.session_state[unique_key_answer_checked]:
                st.subheader("✅ 정답")
                st.info(f"**{answer_content}**")
                if st.session_state[unique_key_user_answer].strip().lower() == answer_content.strip().lower():
                    st.success("입력하신 답변이 정답과 일치합니다!")
                else:
                    st.error("입력하신 답변이 정답과 다릅니다. 다시 한번 확인해보세요.")

        st.write("---")
        st.subheader("이해 난이도 평가:")
        
        # 난이도 평가 버튼을 누르면 바로 다음 노트로 이동 및 데이터 업데이트
        col1, col2, col3, col4 = st.columns(4)
        difficulty_chosen = False
        selected_difficulty = None # 선택된 난이도 초기화

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

        if difficulty_chosen and selected_difficulty: # 선택된 난이도가 있을 때만 진행
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
                # 현재 노트 ID와 관련된 모든 임시 키 삭제
                # Streamlit의 key 관리 방식에 따라 정확한 key만 삭제하도록 수정
                key_to_delete = f"{key_prefix}_{st.session_state.current_review_index}"
                if key_to_delete in st.session_state:
                    del st.session_state[key_to_delete]
            
            # 다음 항목으로 이동
            st.session_state.current_review_index += 1
            st.rerun() # UI 업데이트


# --- 선택 복습 페이지 (기존 코드 유지) ---
# 이 페이지는 이번 요청의 범위에 포함되지 않으므로, 기존 코드를 그대로 유지합니다.
elif st.session_state.page == 'manual_review':
    st.title("📖 원하는 노트 선택해서 복습하기")
    st.write("복습하고 싶은 노트를 직접 선택하고 집중적으로 학습해 보세요.")
    st.session_state.is_manual_review = True # 수동 복습 모드

    if not st.session_state.notes:
        st.info("아직 등록된 노트가 없습니다. '새 노트 추가'에서 복습할 노트를 먼저 생성해주세요!")
        if st.button("새 노트 추가하러 가기", key="manual_review_go_add_note"):
            go_to_page('add_note')
    else:
        # 복습 진행 중이 아니라면 (처음 페이지 진입 또는 복습 완료 후) 노트 선택 UI 표시
        # manual_review 페이지에 들어왔을 때, 선택된 노트가 없고 (초기상태), 현재 복습 인덱스도 0이면 노트 선택 UI를 보여줌.
        # 즉, 복습이 시작되기 전이거나 완료된 후 초기 상태로 돌아왔을 때만 선택 UI를 보여줌.
        if st.session_state.current_review_index == 0 and not st.session_state.selected_review_notes:
            st.subheader("📚 복습할 노트 선택")
            
            display_notes = []
            for note in st.session_state.notes:
                # '선택' 컬럼의 초기값은 항상 False로 설정하여 사용자가 매번 다시 선택하도록 유도
                display_notes.append({
                    "id": note['id'],
                    "선택": False,
                    "제목": note['title'],
                    "유형": note['type'].split('(')[0],
                    "다음 복습일": note['next_review_date'].strftime('%Y-%m-%d') if note['next_review_date'] else "N/A"
                })
            
            edited_df = pd.DataFrame(display_notes)
            # st.data_editor를 사용하여 데이터프레임 편집 및 선택 가능하게 함
            edited_df = st.data_editor(
                edited_df,
                column_config={"선택": st.column_config.CheckboxColumn(required=True)},
                hide_index=True,
                key="manual_review_select_notes_editor"
            )

            selected_notes_from_editor_ids = edited_df[edited_df["선택"] == True]["id"].tolist()
            st.session_state.selected_review_notes = [note for note in st.session_state.notes if note['id'] in selected_notes_from_editor_ids]

            st.markdown("---")

            if not st.session_state.selected_review_notes:
                st.warning("복습할 노트를 하나 이상 선택해주세요.")
            else:
                if st.button(f"선택된 노트 복습 시작 ({len(st.session_state.selected_review_notes)}개)", key="start_manual_review"):
                    st.session_state.current_review_index = 0
                    st.rerun() # 복습 모듈로 진입하기 위해 새로고침
        
        # 복습이 시작되었거나 진행 중인 경우, 또는 모든 복습이 완료된 경우
        else: # 이미 노트가 선택되었거나 복습이 진행 중일 때만 복습 로직을 실행
            num_to_review = len(st.session_state.selected_review_notes)
            
            if not st.session_state.selected_review_notes: # 선택된 노트가 없으면 다시 선택 페이지로
                st.info("선택된 노트가 없습니다. 다시 노트를 선택해주세요.")
                st.session_state.current_review_index = 0
                st.session_state.is_manual_review = False # 상태 초기화
                st.rerun()
                return

            if st.session_state.current_review_index >= num_to_review:
                st.success("🎉 선택된 노트 복습을 모두 완료했습니다! 정말 수고하셨습니다!")
                st.session_state.selected_review_notes = [] # 선택 복습 목록 초기화
                st.session_state.current_review_index = 0
                st.session_state.is_manual_review = False # 상태 초기화
                if st.button("학습 통계 보러가기", key="manual_review_done_stats"):
                    go_to_page('stats')
                return

            current_note = st.session_state.selected_review_notes[st.session_state.current_review_index]

            st.subheader(f"✅ 복습할 항목: {st.session_state.current_review_index + 1} / {num_to_review}")
            st.markdown(f"### **'{current_note['title']}'**")
            
            selected_review_mode = st.radio(
                "복습 모드 선택:",
                ["플래시카드", "주관식"],
                index=0 if current_note['initial_review_mode'] == '플래시카드' else 1,
                key=f"manual_mode_select_{current_note['id']}_{st.session_state.current_review_index}"
            )

            st.write("---")

            if selected_review_mode == "플래시카드":
                front_content = current_note['content'].get('front') or current_note['content'].get('question')
                back_content = current_note['content'].get('back') or current_note['content'].get('answer')

                st.subheader("💡 앞면 (단어/개념)")
                st.write(f"**{front_content}**")
                
                unique_key_show_back = f"manual_show_back_{current_note['id']}_{st.session_state.current_review_index}"
                if unique_key_show_back not in st.session_state:
                    st.session_state[unique_key_show_back] = False

                if st.button("정답 확인", key=f"manual_show_back_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                    st.session_state[unique_key_show_back] = True
                    st.rerun()

                if st.session_state[unique_key_show_back]:
                    st.subheader("✅ 뒷면 (의미/설명)")
                    st.info(f"**{back_content}**")
            
            elif selected_review_mode == "주관식":
                question_content = current_note['content'].get('question') or current_note['content'].get('front')
                answer_content = current_note['content'].get('answer') or current_note['content'].get('back')

                st.subheader("❓ 질문 (앞면)")
                st.write(f"**{question_content}**")
                
                unique_key_user_answer = f"manual_user_answer_{current_note['id']}_{st.session_state.current_review_index}"
                unique_key_answer_checked = f"manual_answer_checked_{current_note['id']}_{st.session_state.current_review_index}"

                if unique_key_user_answer not in st.session_state:
                    st.session_state[unique_key_user_answer] = ""
                if unique_key_answer_checked not in st.session_state:
                    st.session_state[unique_key_answer_checked] = False

                user_answer = st.text_area("답변을 입력하세요.", value=st.session_state[unique_key_user_answer], key=f"manual_user_answer_text_{current_note['id']}_{st.session_state.current_review_index}")
                
                if st.button("정답 확인", key=f"manual_check_answer_btn_{current_note['id']}_{st.session_state.current_review_index}"):
                    st.session_state[unique_key_user_answer] = user_answer
                    st.session_state[unique_key_answer_checked] = True
                    st.rerun()

                if st.session_state[unique_key_answer_checked]:
                    st.subheader("✅ 정답")
                    st.info(f"**{answer_content}**")
                    if st.session_state[unique_key_user_answer].strip().lower() == answer_content.strip().lower():
                        st.success("입력하신 답변이 정답과 일치합니다!")
                    else:
                        st.error("입력하신 답변이 정답과 다릅니다. 다시 한번 확인해보세요.")

            st.write("---")
            st.subheader("이해 난이도 평가:")
            
            col1, col2, col3, col4 = st.columns(4)
            difficulty_chosen = False
            selected_difficulty = None

            with col1:
                if st.button("😊 쉬웠음", key=f"manual_diff_easy_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "쉬웠음"
                    difficulty_chosen = True
            with col2:
                if st.button("🙂 보통", key=f"manual_diff_normal_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "보통"
                    difficulty_chosen = True
            with col3:
                if st.button("🙁 어려웠음", key=f"manual_diff_hard_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "어려웠음"
                    difficulty_chosen = True
            with col4:
                if st.button("😩 전혀 기억 안 남", key=f"manual_diff_forgot_{current_note['id']}_{st.session_state.current_review_index}"):
                    selected_difficulty = "전혀 기억나지 않음"
                    difficulty_chosen = True

            if difficulty_chosen and selected_difficulty:
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

                # 세션 상태에 저장된 임시 변수들 초기화
                for key_prefix in [f"manual_show_back_{current_note['id']}", f"manual_user_answer_{current_note['id']}", f"manual_answer_checked_{current_note['id']}"]:
                    key_to_delete = f"{key_prefix}_{st.session_state.current_review_index}"
                    if key_to_delete in st.session_state:
                        del st.session_state[key_to_delete]

                st.session_state.current_review_index += 1
                st.rerun()


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
