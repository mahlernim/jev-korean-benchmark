# Clinician review packet



All cases and English equivalents were authored before inference. None has clinician approval yet.



For each case, check Korean meaning, English equivalence, gold label, and ambiguity. Record reviewer, date, approval or correction in a separate review file. Corrections require a new manifest and experiment. Do not edit the frozen manifest.



## medical-negation-01

Category: negation; minimal pair: negation-1

Korean: 환자는 흉통을 호소한다.

Query: 흉통

English: The patient reports chest pain.

Query: Chest pain

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: present

Review: PENDING



## medical-negation-02

Category: negation; minimal pair: negation-1

Korean: 환자는 흉통을 부인한다.

Query: 흉통

English: The patient denies chest pain.

Query: Chest pain

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: absent

Review: PENDING



## medical-negation-03

Category: negation; minimal pair: negation-2

Korean: 발열 여부는 기록되지 않았다.

Query: 발열

English: Whether fever is present was not documented.

Query: Fever

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: unknown

Review: PENDING



## medical-negation-04

Category: negation; minimal pair: negation-2

Korean: 발열이 있다.

Query: 발열

English: Fever is present.

Query: Fever

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: present

Review: PENDING



## medical-negation-05

Category: negation; minimal pair: negation-3

Korean: 기록: SOB 없음.

Query: 호흡곤란

English: Note: No SOB.

Query: Shortness of breath

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: absent

Review: PENDING



## medical-negation-06

Category: negation; minimal pair: negation-3

Korean: 기록: SOB 있음.

Query: 호흡곤란

English: Note: SOB present.

Query: Shortness of breath

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: present

Review: PENDING



## medical-negation-07

Category: negation; minimal pair: negation-4

Korean: 폐렴 가능성 있음. 확진되지 않음.

Query: 확진된 폐렴

English: Pneumonia is possible. It is not confirmed.

Query: Confirmed pneumonia

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: unknown

Review: PENDING



## medical-negation-08

Category: negation; minimal pair: negation-4

Korean: 폐렴이 확진됨.

Query: 확진된 폐렴

English: Pneumonia is confirmed.

Query: Confirmed pneumonia

Options KO: {"present": "명시적으로 있음 또는 확진됨", "absent": "명시적으로 없음 또는 부인함", "unknown": "불명확, 가능성만 있음, 또는 미기록"}

Options EN: {"present": "Explicitly present or confirmed", "absent": "Explicitly absent or denied", "unknown": "Unclear, possible only, or undocumented"}

Proposed gold: present

Review: PENDING



## medical-temporality-01

Category: temporality; minimal pair: temporality-1

Korean: 작년 발열은 소실되었고 현재 발열 없음.

Query: 발열

English: Last year's fever resolved; there is no fever now.

Query: Fever

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: historical

Review: PENDING



## medical-temporality-02

Category: temporality; minimal pair: temporality-1

Korean: 작년에는 발열이 없었고 현재 발열 있음.

Query: 발열

English: There was no fever last year; fever is present now.

Query: Fever

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: current

Review: PENDING



## medical-temporality-03

Category: temporality; minimal pair: temporality-2

Korean: 두통이 있었다고 하나 시점은 불명확하다.

Query: 두통

English: Headache was reported, but its timing is unclear.

Query: Headache

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: unknown

Review: PENDING



## medical-temporality-04

Category: temporality; minimal pair: temporality-2

Korean: 현재 두통이 있다.

Query: 두통

English: Headache is present now.

Query: Headache

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: current

Review: PENDING



## medical-temporality-05

Category: temporality; minimal pair: temporality-3

Korean: PMH: 천식. 과거에만 증상이 있었고 현재 증상 없음.

Query: 천식 증상

English: PMH: asthma. Symptoms occurred only in the past; none currently.

Query: Asthma symptoms

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: historical

Review: PENDING



## medical-temporality-06

Category: temporality; minimal pair: temporality-3

Korean: PMH: 천식. 현재 천식 증상 있음.

Query: 천식 증상

English: PMH: asthma. Asthma symptoms are present now.

Query: Asthma symptoms

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: current

Review: PENDING



## medical-temporality-07

Category: temporality; minimal pair: temporality-4

Korean: 기침에 대한 시간 정보 없음.

Query: 기침

English: No timing information is available for the cough.

Query: Cough

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: unknown

Review: PENDING



## medical-temporality-08

Category: temporality; minimal pair: temporality-4

Korean: 기침은 2개월 전에 끝났고 재발하지 않았다.

Query: 기침

English: The cough ended two months ago and has not recurred.

Query: Cough

Options KO: {"current": "현재 있음", "historical": "과거에만 있었고 현재는 없음", "unknown": "시점을 알 수 없음"}

Options EN: {"current": "Present now", "historical": "Past only and not current", "unknown": "Timing cannot be determined"}

Proposed gold: historical

Review: PENDING



## medical-experiencer-01

Category: experiencer; minimal pair: experiencer-1

Korean: 환자에게 DM이 있고 가족력은 없다.

Query: 당뇨병

English: The patient has DM; there is no family history.

Query: Diabetes mellitus

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: patient

Review: PENDING



## medical-experiencer-02

Category: experiencer; minimal pair: experiencer-1

Korean: 환자는 DM이 없고 어머니에게 DM이 있다.

Query: 당뇨병

English: The patient does not have DM; the mother has DM.

Query: Diabetes mellitus

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: family

Review: PENDING



## medical-experiencer-03

Category: experiencer; minimal pair: experiencer-2

Korean: 기록에 고혈압이라고만 적혀 있어 누구의 병력인지 알 수 없다.

Query: 고혈압

English: The note only says hypertension; whose history it is is unclear.

Query: Hypertension

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: unknown

Review: PENDING



## medical-experiencer-04

Category: experiencer; minimal pair: experiencer-2

Korean: 환자 본인이 고혈압 진단을 받았다.

Query: 고혈압

English: The patient was diagnosed with hypertension.

Query: Hypertension

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: patient

Review: PENDING



## medical-experiencer-05

Category: experiencer; minimal pair: experiencer-3

Korean: FHx: 부친 대장암. 환자 본인은 대장암 없음.

Query: 대장암

English: FHx: father with colon cancer. The patient does not have colon cancer.

Query: Colon cancer

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: family

Review: PENDING



## medical-experiencer-06

Category: experiencer; minimal pair: experiencer-3

Korean: 환자 대장암 진단. FHx: 대장암 없음.

Query: 대장암

English: Patient diagnosed with colon cancer. FHx: no colon cancer.

Query: Colon cancer

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: patient

Review: PENDING



## medical-experiencer-07

Category: experiencer; minimal pair: experiencer-4

Korean: 천식 병력의 대상자가 명시되지 않았다.

Query: 천식

English: The person with the history of asthma is not specified.

Query: Asthma

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: unknown

Review: PENDING



## medical-experiencer-08

Category: experiencer; minimal pair: experiencer-4

Korean: 환자의 누나에게 천식이 있고 환자에게는 없다.

Query: 천식

English: The patient's older sister has asthma; the patient does not.

Query: Asthma

Options KO: {"patient": "환자 본인", "family": "가족에게만 있음", "unknown": "대상자를 알 수 없음"}

Options EN: {"patient": "The patient", "family": "Family member only", "unknown": "Person cannot be determined"}

Proposed gold: family

Review: PENDING



## medical-medication-01

Category: medication; minimal pair: medication-1

Korean: 현재 metformin을 매일 복용 중이다.

Query: 현재 metformin 복용

English: Currently taking metformin daily.

Query: Current metformin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: taking

Review: PENDING



## medical-medication-02

Category: medication; minimal pair: medication-1

Korean: metformin은 어제 중단했고 현재 복용하지 않는다.

Query: 현재 metformin 복용

English: Metformin was stopped yesterday and is not currently taken.

Query: Current metformin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: not_taking

Review: PENDING



## medical-medication-03

Category: medication; minimal pair: medication-2

Korean: 내일부터 aspirin 시작 예정. 아직 복용하지 않음.

Query: 현재 aspirin 복용

English: Aspirin is planned to start tomorrow. Not yet taking it.

Query: Current aspirin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: not_taking

Review: PENDING



## medical-medication-04

Category: medication; minimal pair: medication-2

Korean: 어제부터 aspirin을 시작했고 현재 복용 중이다.

Query: 현재 aspirin 복용

English: Aspirin was started yesterday and is currently taken.

Query: Current aspirin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: taking

Review: PENDING



## medical-medication-05

Category: medication; minimal pair: medication-3

Korean: 약 목록에 warfarin이 있으나 현재 복용 여부는 불명확하다.

Query: 현재 warfarin 복용

English: Warfarin appears on the medication list, but current use is unclear.

Query: Current warfarin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: unknown

Review: PENDING



## medical-medication-06

Category: medication; minimal pair: medication-3

Korean: 환자가 현재 warfarin을 복용한다고 확인했다.

Query: 현재 warfarin 복용

English: The patient confirmed current warfarin use.

Query: Current warfarin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: taking

Review: PENDING



## medical-medication-07

Category: medication; minimal pair: medication-4

Korean: 인슐린 처방 여부와 복용 여부가 기록되어 있지 않다.

Query: 현재 인슐린 사용

English: Neither insulin prescribing nor use is documented.

Query: Current insulin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: unknown

Review: PENDING



## medical-medication-08

Category: medication; minimal pair: medication-4

Korean: 인슐린은 중단했고 현재 사용하지 않는다.

Query: 현재 인슐린 사용

English: Insulin was discontinued and is not currently used.

Query: Current insulin use

Options KO: {"taking": "현재 복용 또는 사용 중", "not_taking": "현재 복용하지 않음, 중단 또는 아직 시작 전", "unknown": "현재 복용 여부 불명확"}

Options EN: {"taking": "Currently taking or using", "not_taking": "Not currently taking, stopped, or not yet started", "unknown": "Current use is unclear"}

Proposed gold: not_taking

Review: PENDING



## medical-evidence-01

Category: evidence; minimal pair: evidence-1

Korean: 검사 결과 Na 130 mmol/L이다.

Query: Na 측정값은 130 mmol/L이다.

English: The laboratory result is Na 130 mmol/L.

Query: The measured Na is 130 mmol/L.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: supported

Review: PENDING



## medical-evidence-02

Category: evidence; minimal pair: evidence-1

Korean: 검사 결과 Na 140 mmol/L이다.

Query: Na 측정값은 130 mmol/L이다.

English: The laboratory result is Na 140 mmol/L.

Query: The measured Na is 130 mmol/L.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: contradicted

Review: PENDING



## medical-evidence-03

Category: evidence; minimal pair: evidence-2

Korean: 환자는 항생제를 복용했다. 체온 변화는 기록되지 않았다.

Query: 항생제 복용 후 발열이 소실되었다.

English: The patient took an antibiotic. Temperature changes were not recorded.

Query: Fever resolved after taking the antibiotic.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: unknown

Review: PENDING



## medical-evidence-04

Category: evidence; minimal pair: evidence-2

Korean: 항생제 복용 후 발열이 소실되었다고 기록되어 있다.

Query: 항생제 복용 후 발열이 소실되었다.

English: It is documented that fever resolved after taking the antibiotic.

Query: Fever resolved after taking the antibiotic.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: supported

Review: PENDING



## medical-evidence-05

Category: evidence; minimal pair: evidence-3

Korean: CT에서 출혈이 없다고 판독했다.

Query: CT 판독에서 출혈이 확인되었다.

English: The CT report states that there is no bleeding.

Query: Bleeding was identified in the CT report.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: contradicted

Review: PENDING



## medical-evidence-06

Category: evidence; minimal pair: evidence-3

Korean: CT에서 출혈이 있다고 판독했다.

Query: CT 판독에서 출혈이 확인되었다.

English: The CT report states that bleeding is present.

Query: Bleeding was identified in the CT report.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: supported

Review: PENDING



## medical-evidence-07

Category: evidence; minimal pair: evidence-4

Korean: 혈압은 기록되었으나 Cr 결과는 없다.

Query: Cr이 이전보다 상승했다.

English: Blood pressure was recorded, but no Cr result is available.

Query: Cr increased from its previous value.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: unknown

Review: PENDING



## medical-evidence-08

Category: evidence; minimal pair: evidence-4

Korean: Cr이 이전보다 상승했다고 기록되어 있다.

Query: Cr이 이전보다 상승했다.

English: It is documented that Cr increased from its previous value.

Query: Cr increased from its previous value.

Options KO: {"supported": "기록이 주장을 뒷받침함", "contradicted": "기록이 주장과 모순됨", "unknown": "기록만으로 판단할 수 없음"}

Options EN: {"supported": "The note supports the claim", "contradicted": "The note contradicts the claim", "unknown": "Insufficient evidence in the note"}

Proposed gold: supported

Review: PENDING
