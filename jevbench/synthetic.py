"""Authored before inference. Medical labels/translations require clinician review."""


def medical_cases():
    # Each tuple is Korean note, English note, Korean query, English query, gold.
    groups = {
        "negation": [
            ("환자는 흉통을 호소한다.", "The patient reports chest pain.", "흉통", "Chest pain", "present"),
            ("환자는 흉통을 부인한다.", "The patient denies chest pain.", "흉통", "Chest pain", "absent"),
            ("발열 여부는 기록되지 않았다.", "Whether fever is present was not documented.", "발열", "Fever", "unknown"),
            ("발열이 있다.", "Fever is present.", "발열", "Fever", "present"),
            ("기록: SOB 없음.", "Note: No SOB.", "호흡곤란", "Shortness of breath", "absent"),
            ("기록: SOB 있음.", "Note: SOB present.", "호흡곤란", "Shortness of breath", "present"),
            ("폐렴 가능성 있음. 확진되지 않음.", "Pneumonia is possible. It is not confirmed.", "확진된 폐렴", "Confirmed pneumonia", "unknown"),
            ("폐렴이 확진됨.", "Pneumonia is confirmed.", "확진된 폐렴", "Confirmed pneumonia", "present"),
        ],
        "temporality": [
            ("작년 발열은 소실되었고 현재 발열 없음.", "Last year's fever resolved; there is no fever now.", "발열", "Fever", "historical"),
            ("작년에는 발열이 없었고 현재 발열 있음.", "There was no fever last year; fever is present now.", "발열", "Fever", "current"),
            ("두통이 있었다고 하나 시점은 불명확하다.", "Headache was reported, but its timing is unclear.", "두통", "Headache", "unknown"),
            ("현재 두통이 있다.", "Headache is present now.", "두통", "Headache", "current"),
            ("PMH: 천식. 과거에만 증상이 있었고 현재 증상 없음.", "PMH: asthma. Symptoms occurred only in the past; none currently.", "천식 증상", "Asthma symptoms", "historical"),
            ("PMH: 천식. 현재 천식 증상 있음.", "PMH: asthma. Asthma symptoms are present now.", "천식 증상", "Asthma symptoms", "current"),
            ("기침에 대한 시간 정보 없음.", "No timing information is available for the cough.", "기침", "Cough", "unknown"),
            ("기침은 2개월 전에 끝났고 재발하지 않았다.", "The cough ended two months ago and has not recurred.", "기침", "Cough", "historical"),
        ],
        "experiencer": [
            ("환자에게 DM이 있고 가족력은 없다.", "The patient has DM; there is no family history.", "당뇨병", "Diabetes mellitus", "patient"),
            ("환자는 DM이 없고 어머니에게 DM이 있다.", "The patient does not have DM; the mother has DM.", "당뇨병", "Diabetes mellitus", "family"),
            ("기록에 고혈압이라고만 적혀 있어 누구의 병력인지 알 수 없다.", "The note only says hypertension; whose history it is is unclear.", "고혈압", "Hypertension", "unknown"),
            ("환자 본인이 고혈압 진단을 받았다.", "The patient was diagnosed with hypertension.", "고혈압", "Hypertension", "patient"),
            ("FHx: 부친 대장암. 환자 본인은 대장암 없음.", "FHx: father with colon cancer. The patient does not have colon cancer.", "대장암", "Colon cancer", "family"),
            ("환자 대장암 진단. FHx: 대장암 없음.", "Patient diagnosed with colon cancer. FHx: no colon cancer.", "대장암", "Colon cancer", "patient"),
            ("천식 병력의 대상자가 명시되지 않았다.", "The person with the history of asthma is not specified.", "천식", "Asthma", "unknown"),
            ("환자의 누나에게 천식이 있고 환자에게는 없다.", "The patient's older sister has asthma; the patient does not.", "천식", "Asthma", "family"),
        ],
        "medication": [
            ("현재 metformin을 매일 복용 중이다.", "Currently taking metformin daily.", "현재 metformin 복용", "Current metformin use", "taking"),
            ("metformin은 어제 중단했고 현재 복용하지 않는다.", "Metformin was stopped yesterday and is not currently taken.", "현재 metformin 복용", "Current metformin use", "not_taking"),
            ("내일부터 aspirin 시작 예정. 아직 복용하지 않음.", "Aspirin is planned to start tomorrow. Not yet taking it.", "현재 aspirin 복용", "Current aspirin use", "not_taking"),
            ("어제부터 aspirin을 시작했고 현재 복용 중이다.", "Aspirin was started yesterday and is currently taken.", "현재 aspirin 복용", "Current aspirin use", "taking"),
            ("약 목록에 warfarin이 있으나 현재 복용 여부는 불명확하다.", "Warfarin appears on the medication list, but current use is unclear.", "현재 warfarin 복용", "Current warfarin use", "unknown"),
            ("환자가 현재 warfarin을 복용한다고 확인했다.", "The patient confirmed current warfarin use.", "현재 warfarin 복용", "Current warfarin use", "taking"),
            ("인슐린 처방 여부와 복용 여부가 기록되어 있지 않다.", "Neither insulin prescribing nor use is documented.", "현재 인슐린 사용", "Current insulin use", "unknown"),
            ("인슐린은 중단했고 현재 사용하지 않는다.", "Insulin was discontinued and is not currently used.", "현재 인슐린 사용", "Current insulin use", "not_taking"),
        ],
        "evidence": [
            ("검사 결과 Na 130 mmol/L이다.", "The laboratory result is Na 130 mmol/L.", "Na 측정값은 130 mmol/L이다.", "The measured Na is 130 mmol/L.", "supported"),
            ("검사 결과 Na 140 mmol/L이다.", "The laboratory result is Na 140 mmol/L.", "Na 측정값은 130 mmol/L이다.", "The measured Na is 130 mmol/L.", "contradicted"),
            ("환자는 항생제를 복용했다. 체온 변화는 기록되지 않았다.", "The patient took an antibiotic. Temperature changes were not recorded.", "항생제 복용 후 발열이 소실되었다.", "Fever resolved after taking the antibiotic.", "unknown"),
            ("항생제 복용 후 발열이 소실되었다고 기록되어 있다.", "It is documented that fever resolved after taking the antibiotic.", "항생제 복용 후 발열이 소실되었다.", "Fever resolved after taking the antibiotic.", "supported"),
            ("CT에서 출혈이 없다고 판독했다.", "The CT report states that there is no bleeding.", "CT 판독에서 출혈이 확인되었다.", "Bleeding was identified in the CT report.", "contradicted"),
            ("CT에서 출혈이 있다고 판독했다.", "The CT report states that bleeding is present.", "CT 판독에서 출혈이 확인되었다.", "Bleeding was identified in the CT report.", "supported"),
            ("혈압은 기록되었으나 Cr 결과는 없다.", "Blood pressure was recorded, but no Cr result is available.", "Cr이 이전보다 상승했다.", "Cr increased from its previous value.", "unknown"),
            ("Cr이 이전보다 상승했다고 기록되어 있다.", "It is documented that Cr increased from its previous value.", "Cr이 이전보다 상승했다.", "Cr increased from its previous value.", "supported"),
        ],
    }
    definitions = {
        "negation": ({"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}, {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}),
        "temporality": ({"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}, {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}),
        "experiencer": ({"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}, {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}),
        "medication": ({"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}, {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}),
        "evidence": ({"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}, {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}),
    }
    queries = {
        "negation": ("기록만으로 다음 소견의 상태를 분류하세요: ", "Classify the status of this finding using only the note: "),
        "temporality": ("기록만으로 다음 소견의 시점을 분류하세요: ", "Classify the timing of this finding using only the note: "),
        "experiencer": ("기록만으로 다음 병력이 누구에게 있는지 분류하세요: ", "Identify whose history this is using only the note: "),
        "medication": ("기록만으로 다음 약물 사용 상태를 분류하세요: ", "Classify this medication-use status using only the note: "),
        "evidence": ("기록만으로 다음 주장의 근거를 분류하세요: ", "Classify the evidence for this claim using only the note: "),
    }
    cases = []
    for category, rows in groups.items():
        for i, (ko, en, qko, qen, gold) in enumerate(rows):
            cases.append(dict(id=f"medical-{category}-{i+1:02}", task="medical_text", stage=3, category=category,
                pair_id=f"{category}-{i//2+1}", kind="choice", gold=gold, review_status="unreviewed",
                content={"ko": {"note": ko, "query": qko}, "en": {"note": en, "query": qen}},
                options={"ko": definitions[category][0], "en": definitions[category][1]},
                instructions={"ko": queries[category][0].rstrip(': '), "en": queries[category][1].rstrip(': ')}))
    return cases


def development_cases():
    # Separate authored items, with no test-set passages or facts.
    rows = [
        ("상자는 빨간색이다.", "The box is red.", "상자의 색은?", "What color is the box?", "red"),
        ("상자는 파란색이다.", "The box is blue.", "상자의 색은?", "What color is the box?", "blue"),
        ("상자의 색은 적혀 있지 않다.", "The box color is not stated.", "상자의 색은?", "What color is the box?", "unknown"),
        ("공은 빨간색이다.", "The ball is red.", "공의 색은?", "What color is the ball?", "red"),
        ("공은 파란색이다.", "The ball is blue.", "공의 색은?", "What color is the ball?", "blue"),
        ("공의 크기만 적혀 있다.", "Only the size of the ball is stated.", "공의 색은?", "What color is the ball?", "unknown"),
    ]
    cases = []
    for i, (ko, en, qko, qen, gold) in enumerate(rows):
        cases.append(dict(id=f"dev-choice-{i}", stage=0, task="development_choice", kind="choice", gold=gold,
            content={"ko": {"text": ko, "question": qko}, "en": {"text": en, "question": qen}},
            options={"ko": {"red": "빨강", "blue": "파랑", "unknown": "알 수 없음"}, "en": {"red": "Red", "blue": "Blue", "unknown": "Unknown"}}))
    pairs = [
        ("문이 열려 있다.", "문은 열려 있다.", "The door is open.", "The door is not closed.", 1),
        ("문이 열려 있다.", "문이 닫혀 있다.", "The door is open.", "The door is closed.", 0),
        ("민수가 영희를 도왔다.", "영희가 민수를 도왔다.", "Minsu helped Younghee.", "Younghee helped Minsu.", 0),
        ("개가 잔다.", "개는 자고 있다.", "The dog sleeps.", "The dog is sleeping.", 1),
        ("책은 두 권이다.", "책은 세 권이다.", "There are two books.", "There are three books.", 0),
        ("비가 오지 않는다.", "비는 내리지 않는다.", "It is not raining.", "No rain is falling.", 1),
    ]
    for i, (a,b,c,d,gold) in enumerate(pairs):
        cases.append(dict(id=f"dev-noul-{i}", stage=0, task="development_noul", kind="noul", gold=str(gold),
            content={"ko": {"sentence1": a, "sentence2": b}, "en": {"sentence1": c, "sentence2": d}}))
    return cases
