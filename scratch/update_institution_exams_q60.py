from pathlib import Path

ie_path = Path("c:/Users/SHRIJA SANIL/VyasaPrep_Frontend/src/pages/auto/InstitutionExams.jsx")
if ie_path.exists():
    txt = ie_path.read_text(encoding="utf-8")
    
    # 1. Update initial state
    txt = txt.replace("const [questionCount, setQuestionCount] = useState(20);", "const [questionCount, setQuestionCount] = useState(60);")
    txt = txt.replace("const [questionCount, setQuestionCount] = useState(40);", "const [questionCount, setQuestionCount] = useState(60);")
    
    # 2. Lock select options to 60 questions
    txt = txt.replace('<option value="20">20 Questions</option>', '')
    txt = txt.replace('<option value="40">40 Questions</option>', '')
    txt = txt.replace('<option value="60">60 Questions (KCET Standard)</option>', '<option value="60">60 Questions (Standard KCET)</option>')
    
    ie_path.write_text(txt, encoding="utf-8")
    print("InstitutionExams.jsx updated successfully!")
