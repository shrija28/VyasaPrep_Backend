import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_inst_student():
    ts = str(int(time.time()))
    admin_session = requests.Session()

    # 1. Login as SMVITM Admin
    print("--- 1. Login as SMVITM Admin ---")
    login_admin = admin_session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": "smvitm@sode-edu.in",
        "password": "Password123"
    })
    print(f"Admin login status: {login_admin.status_code}")

    # 2. Generate invite code
    inv_resp = admin_session.post(f"{BASE_URL}/api/institution/invite")
    code = inv_resp.json().get("code")
    print(f"Invite code generated: {code}")

    # 3. Create an exam for SMVITM
    create_exam_resp = admin_session.post(f"{BASE_URL}/content/exams", json={
        "subject": "Biology",
        "exam_name": f"SMVITM Bio Special Test {ts}",
        "is_published": True,
        "question_count": 60
    })
    print(f"Create SMVITM exam status: {create_exam_resp.status_code}")
    print(f"Create exam response: {create_exam_resp.json()}")

    # 4. Register student with invite code
    student_session = requests.Session()
    reg_student = student_session.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"smvitm_student_{ts}@gmail.com",
        "password": "Password123",
        "display_name": "SMVITM Test Student",
        "invite_code": code
    })
    print(f"Student register status: {reg_student.status_code}")

    # 5. Call GET /api/student/exams as SMVITM student
    exams_resp = student_session.get(f"{BASE_URL}/api/student/exams")
    print(f"GET /api/student/exams status: {exams_resp.status_code}")
    exams_data = exams_resp.json()
    print(f"Exams Data for SMVITM Student:\n{json.dumps(exams_data, indent=2)}")

if __name__ == "__main__":
    test_inst_student()
