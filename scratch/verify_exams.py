import os
import requests
import jwt
import datetime

# Exact SECRET from .env
SECRET = "your-super-secret-jwt-key-min-16-chars"

students = [
    {
        'desc': 'MGM Student',
        'email': 'rohu@gmail.com',
        'sub': 'mgm0001',
        'inst_id': '5226e678-58c5-4a51-832a-1f658da152bd',
        'subtype': 'institution_linked'
    },
    {
        'desc': 'MAHE Student',
        'email': 'mahe_student1@smartkcet.edu',
        'sub': 'mahe_student1@smartkcet.edu',
        'inst_id': '9fc04466-ceb5-4b38-baa5-42b94c7fcb92',
        'subtype': 'institution_linked'
    },
    {
        'desc': 'SMVIT Student',
        'email': 'smvit_student1@smartkcet.edu',
        'sub': 'smvit_student1@smartkcet.edu',
        'inst_id': '57252780-bd0d-4de0-8c20-a0b621582186',
        'subtype': 'institution_linked'
    },
    {
        'desc': 'Direct Personal Student',
        'email': 'student1@smartkcet.test',
        'sub': 'student1@smartkcet.test',
        'inst_id': None,
        'subtype': 'direct_subscriber'
    }
]

print("=== VERIFYING STUDENT EXAM ISOLATION & IMMEDIATE DELIVERY ===")

for s in students:
    payload = {
        'sub': s['sub'],
        'role': 'student',
        'student_subtype': s['subtype'],
        'subscription_status': 'active',
        'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
        'jti': 'test-' + s['email'][:5]
    }
    if s['inst_id']:
        payload['institution_id'] = s['inst_id']
        
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get('http://127.0.0.1:8000/api/student/exams', headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            subjects = data.get('subjects', [])
            total_exams = sum(sb.get('available_exams', 0) for sb in subjects)
            print(f"\n{s['desc']} ({s['email']}) | Inst ID: {s['inst_id']}: {total_exams} exams visible across {len(subjects)} subjects")
            for sb in subjects:
                print(f"   Subject: {sb.get('subject')} ({sb.get('available_exams')} exams)")
                for e in sb.get('exams', []):
                    print(f"      - Exam ID: {e.get('exam_id')} | Name: '{e.get('exam_name')}' | Inst ID: {e.get('institution_id')}")
        else:
            print(f"\n{s['desc']} ({s['email']}): Error {r.status_code} - {r.text}")
    except Exception as exc:
        print(f"\n{s['desc']} ({s['email']}): Request error: {exc}")
