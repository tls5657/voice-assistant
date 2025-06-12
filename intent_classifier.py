# intent_classifier.py

import re
import urllib.parse

def classify_intent(text: str) -> dict:
    """
    ASR(음성→텍스트) 결과 text를 받아서, 다음을 리턴합니다:
      {
        "intent": "EXIT"            # 프로그램 종료
                | "SET_TIMER"         # 타이머 설정
                | "VOLUME_UP"         # 볼륨 높이기
                | "VOLUME_DOWN"       # 볼륨 낮추기
                | "OPEN_CALCULATOR"   # 계산기 실행
                | "OPEN_NOTEPAD"      # 메모장 실행
                | "SEARCH_YOUTUBE"    # 유튜브 검색
                | "SEARCH_GOOGLE"     # 구글 검색
                | "SEARCH_NAVER"      # 네이버 검색
                | "UNKNOWN"           # 알 수 없는 명령
        "parameter": ...            # 필요한 파라미터(숫자, 검색어 등)
      }
    """

    text = text.lower().strip()

    # 1) 종료 의도
    if any(w in text for w in ["종료", "그만", "끝내"]):
        return {"intent": "EXIT", "parameter": None}

    # 2) 타이머 설정 (예: "5분 타이머 설정해줘", "10분짜리 타이머")
    m_timer = re.search(r"(\d+)\s*분(?:짜리)?\s*타이머", text)
    if m_timer:
        minutes = int(m_timer.group(1))
        return {"intent": "SET_TIMER", "parameter": minutes}

    # 3) 볼륨 높이기 (예: "볼륨 높여줘", "소리 올려줘")
    if any(w in text for w in ["볼륨", "소리"]) and any(w in text for w in ["높여", "올려", "높이"]):
        return {"intent": "VOLUME_UP", "parameter": None}

    # 4) 볼륨 낮추기 (예: "볼륨 낮춰줘", "소리 줄여줘")
    if any(w in text for w in ["볼륨", "소리"]) and any(w in text for w in ["낮춰", "줄여", "낮추"]):
        return {"intent": "VOLUME_DOWN", "parameter": None}

    # 5) 계산기 실행 (예: "계산기 실행해줘", "계산기 열어줘")
    if any(w in text for w in ["계산기", "게산기", "개산기"]) and any(w in text for w in ["열어", "켜", "실행"]):
        return {"intent": "OPEN_CALCULATOR", "parameter": None}

    # 6) 메모장 실행 (예: "메모장 열어줘", "노트 열어줘")
    # '매모장' 추가
    if any(w in text for w in ["메모장", "매모장", "노트"]) and any(w in text for w in ["열어", "켜", "실행"]):
        return {"intent": "OPEN_NOTEPAD", "parameter": None}

    # 7) 유튜브 검색 (예: "유튜브에서 고양이 검색해줘", "유튜브 고양이 검색")
    # '유투브' 추가
    m_yt = re.search(r"(?:유튜브|유투브)[^\w]*(?:에서|에)?\s*(.+?)(?:검색)", text)
    if m_yt:
        query = m_yt.group(1).strip()
        # 조사(을/를) 제거(예: "고양이를" → "고양이")
        query = re.sub(r"(을|를|도|도).*$", "", query).strip()
        param = urllib.parse.quote(query)
        return {"intent": "SEARCH_YOUTUBE", "parameter": param}

    # 8) 구글 검색 (예: "구글에 사과 검색해줘", "구글에서 강아지 검색")
    m_google = re.search(r"구글[^\w]*(?:에서|에)?\s*(.+?)(?:검색)", text)
    if m_google:
        query = m_google.group(1).strip()
        query = re.sub(r"(을|를|도|도).*$", "", query).strip()
        param = urllib.parse.quote(query)
        return {"intent": "SEARCH_GOOGLE", "parameter": param}

    # 9) 네이버 검색 (예: "네이버에서 강아지 검색", "네이버에 사과 검색해줘")
    # '내이버' 추가
    m_naver = re.search(r"(?:네이버|내이버)[^\w]*(?:에서|에)?\s*(.+?)(?:검색)", text)
    if m_naver:
        query = m_naver.group(1).strip()
        query = re.sub(r"(을|를|도|도).*$", "", query).strip()
        param = urllib.parse.quote(query)
        return {"intent": "SEARCH_NAVER", "parameter": param}

    # 10) 그 외 알 수 없는 명령
    return {"intent": "UNKNOWN", "parameter": None}