import os
import requests
import jwt
import datetime

SECRET = "your-super-secret-jwt-key-min-16-chars"

# Test Users
users_to_test = [
    {
        'role_desc': 'MGM Institution Admin',
        'email': 'mgm@edu.in',
        'sub': 'mgm@edu.in',
        'role': 'institution_admin',
        'inst_id': '5226e678-58c5-4a51-832a-1f658da152bd'
    },
    {
        'role_desc': 'MAHE Institution Admin',
        'email': 'mahe@gmail.com',
        'sub': 'mahe@gmail.com',
        'role': 'institution_admin',
        'inst_id': '9fc04466-ceb5-4b38-baa5-42b94c7fcb92'
    },
    {
        'role_desc': 'MGM Student',
        'email': 'rohu@gmail.com',
        'sub': 'mgm0001',
        'role': 'student',
        'student_subtype': 'institution_linked',
        'inst_id': '5226e678-58c5-4a51-832a-1f658da152bd'
    },
    {
        'role_desc': 'MAHE Student',
        'email': 'mahe_student1@smartkcet.edu',
        'sub': 'mahe_student1@smartkcet.edu',
        'role': 'student',
        'student_subtype': 'institution_linked',
        'inst_id': '9fc04466-ceb5-4b38-baa5-42b94c7fcb92'
    },
    {
        'role_desc': 'Direct Personal Student',
        'email': 'student1@smartkcet.test',
        'sub': 'student1@smartkcet.test',
        'role': 'student',
        'student_subtype': 'direct_subscriber',
        'inst_id': None
    }
]

print("=== COMPREHENSIVE END-TO-END FLOW VERIFICATION ===")

for u in users_to_test:
    payload = {
        'sub': u['sub'],
        'role': u['role'],
        'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
        'jti': 'test-' + u['email'][:5]
    }
    if u.get('student_subtype'):
        payload['student_subtype'] = u['student_subtype']
        payload['subscription_status'] = 'active'
    if u.get('inst_id'):
        payload['institution_id'] = u['inst_id']
        
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"\n--- Testing {u['role_desc']} ({u['email']}) ---")
    
    # Auth /me check
    r_me = requests.get('http://127.0.0.1:8000/api/auth/me', cookies={'smartkcet_session': token}, timeout=15)
    print(f"GET /api/auth/me -> status {r_me.status_code}")
    if r_me.status_code == 200:
        me_data = r_me.json()
        print(f"   Auth payload: sub={me_data.get('sub')}, role={me_data.get('role')}, inst_id={me_data.get('institution_id')}, inst_name={me_data.get('institution_name')}")
    
    if u['role'] == 'student':
        # Student exams
        r1 = requests.get('http://127.0.0.1:8000/api/student/exams', headers=headers, timeout=15)
        print(f"GET /api/student/exams -> status {r1.status_code}")
        if r1.status_code == 200:
            sb_list = r1.json().get('subjects', [])
            total_exams = sum(sb.get('available_exams', 0) for sb in sb_list)
            print(f"   Total Exams: {total_exams} across {len(sb_list)} subjects")

        r2 = requests.get('http://127.0.0.1:8000/api/institution/student/exams', headers=headers, timeout=15)
        print(f"GET /api/institution/student/exams -> status {r2.status_code}")
        if r2.status_code == 200:
            sb_list = r2.json().get('subjects', [])
            total_exams = sum(sb.get('available_exams', 0) for sb in sb_list)
            print(f"   Inst Student Exams: {total_exams} across {len(sb_list)} subjects")

    elif u['role'] == 'institution_admin':
        # Inst admin exams list
        r_exams = requests.get('http://127.0.0.1:8000/api/institution/content/exams?subject=all', headers=headers, timeout=15)
        print(f"GET /api/institution/content/exams?subject=all -> status {r_exams.status_code}")
        if r_exams.status_code == 200:
            ex_data = r_exams.json()
            print(f"   Exams created: total={ex_data.get('total')}")

        # Inst admin question bank list
        r_qb = requests.get('http://127.0.0.1:8000/api/institution/content/questions?subject=all', headers=headers, timeout=15)
        print(f"GET /api/institution/content/questions?subject=all -> status {r_qb.status_code}")
        if r_qb.status_code == 200:
            qb_data = r_qb.json()
            print(f"   Question bank: total={qb_data.get('total')}")

        # Inst admin indexed files
        r_files = requests.get('http://127.0.0.1:8000/api/institution/content/upload/files?subject=all', headers=headers, timeout=15)
        print(f"GET /api/institution/content/upload/files?subject=all -> status {r_files.status_code}")
        if r_files.status_code == 200:
            f_data = r_files.json()
            print(f"   Indexed files: total={len(f_data.get('files', []))}")
