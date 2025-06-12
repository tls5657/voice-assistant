import re
import urllib.parse

def classify_intent(text: str) -> dict:
    text = text.lower().strip()

    # 1) 종료 의도 (우선순위 높음)
    if any(w in text for w in ["종료", "그만", "끝내"]):
        return {"intent": "EXIT", "parameter": None}

    # 2) 볼륨 제어 (우선순위 높음)
    if "볼륨" in text or "소리" in text:
        if any(w in text for w in ["높여", "올려", "높이"]):
            return {"intent": "VOLUME_UP", "parameter": None}
        elif any(w in text for w in ["낮춰", "줄여", "낮추"]):
            return {"intent": "VOLUME_DOWN", "parameter": None}

    # 3) 계산기 실행 (우선순위 높음)
    if "계산기" in text and any(w in text for w in ["열어", "켜", "실행"]):
        return {"intent": "OPEN_CALCULATOR", "parameter": None}

    # 4) 메모장 실행 (우선순위 높음)
    # '매모장'도 인식하도록 추가
    if any(w in text for w in ["메모장", "매모장", "노트"]) and any(w in text for w in ["열어", "켜", "실행"]):
        return {"intent": "OPEN_NOTEPAD", "parameter": None}

    # 5) 유튜브 검색 (특정 웹사이트 검색은 일반 검색보다 우선)
    # '유투브'도 인식하도록 추가
    m_yt = re.search(r"(?:유튜브|유투브)[^\w]*(?:에서|에)?\s*(.+?)(?:검색)", text)
    if m_yt:
        query = m_yt.group(1).strip()
        # 조사(을/를/이/가/은/는/도/에/에서/한테/에게) 제거
        query = re.sub(r"(을|를|이|가|은|는|도|에|에서|한테|에게)$", "", query)
        param = urllib.parse.quote(query)
        return {"intent": "SEARCH_YOUTUBE", "parameter": param}

    # 6) 네이버 검색 (특정 웹사이트 검색은 일반 검색보다 우선)
    # '내이버'도 인식하도록 추가
    m_naver = re.search(r"(?:네이버|내이버)[^\w]*(?:에서|에)?\s*(.+?)(?:검색)?", text)
    if m_naver:
        query = m_naver.group(1).strip()
        # 조사(을/를/도/이/가) 제거
        query = re.sub(r"(을|를|도|이|가)$", "", query)
        param = urllib.parse.quote(query)
        return {"intent": "SEARCH_NAVER", "parameter": param}

    # 7) 일반 구글 검색 (가장 넓은 범위의 검색 명령)
    # '구글' 명시 없이 "OO 검색해줘", "OO 찾아줘" 등을 인식
    if any(w in text for w in ["검색", "찾아줘", "검색해", "검색해줘", "찾아봐"]): # '찾아봐' 추가
        # "무엇을(을/를/이/가/은/는) 검색(해줘/찾아줘)" 패턴
        m = re.search(r"(.+?)\s*(?:을|를|이|가|은|는|도|에|에서)?\s*(?:검색|찾아줘|검색해|검색해줘|찾아봐)", text)
        if m:
            query = m.group(1).strip()
            # 앞부분에 불필요한 단어가 붙어 있을 수 있으므로 한번 더 정리 (선택적)
            # 예: "파이썬 검색", "파이썬에 대해 검색" 등
            # 더 정교하게 만들려면 여러 패턴을 고려해야 합니다.
            # 지금은 단순히 앞에 있는 내용을 쿼리로 추출합니다.
            param = urllib.parse.quote(query)
            return {"intent": "SEARCH_GOOGLE", "parameter": param}


    # 8) 그 외 → 알 수 없는 명령
    return {"intent": "UNKNOWN", "parameter": None}