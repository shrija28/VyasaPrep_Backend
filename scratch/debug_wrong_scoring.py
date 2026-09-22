import requests
import jwt
import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, ExamSet, Exam
from smartkcet.config import validate_startup_config

cfg = validate_startup_config()
session = SessionLocal()

es_b = session.query(ExamSet).filter(ExamSet.set_label == "B").first()
exam = session.get(Exam, es_b.exam_id)

user = session.query(User).filter(User.role == "student").first()
if exam and exam.institution_id:
    user.institution_id = exam.institution_id
    user.student_subtype = "institution_linked"
    session.commit()

token = jwt.encode({
    'sub': str(user.id),
    'role': 'student',
    'student_subtype': user.student_subtype or 'institution_linked',
    'institution_id': str(user.institution_id) if user.institution_id else None,
    'kcet_student_id': user.kcet_student_id,
    'subscription_status': 'active',
    'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
    'exp': int((datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=1)).timestamp()),
    'jti': str(uuid.uuid4())
}, cfg.jwt_secret, algorithm='HS256')
if isinstance(token, bytes):
    token = token.decode('utf-8')

headers = {'Authorization': f'Bearer {token}'}

q_res = requests.get(f'http://127.0.0.1:8000/api/student/exams/{es_b.id}', headers=headers).json()
qs = q_res.get('questions', [])

wrong_ans = {str(idx): ('0' if str(q['ans']) != '0' else '1') for idx, q in enumerate(qs)}

sub_res = requests.post(f'http://127.0.0.1:8000/api/student/submit', headers=headers, json={
    'exam_set_id': str(es_b.id),
    'answers': wrong_ans,
    'time_taken_sec': 600,
    'idempotency_key': str(uuid.uuid4())
}).json()

print(f"Percentage: {sub_res.get('percentage')}%")
q_results = sub_res.get('result', {}).get('questionResults', [])
for i, qr in enumerate(q_results):
    print(f"q {i}: given={qr.get('given')!r}, correctAns={qr.get('correctAns')!r}, status={qr.get('status')}")

session.close()
