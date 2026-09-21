import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_onboarding():
    print("=== STARTING FULL STUDENT ONBOARDING TEST ===")
    ts = int(time.time())

    # 1. Register new student using institution code 'smvitm'
    new_email = f"perm_student_{ts}@example.com"
    reg_payload = {
        "display_name": "Test Onboarded Student",
        "email": new_email,
        "password": "Password123!",
        "role": "student",
        "student_subtype": "institution_linked",
        "invite_code": "smvitm",
        "code": "smvitm",
        "institution_id": "smvitm"
    }

    print(f"\n1. Registering student {new_email} with institution_id='smvitm'...")
    res = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    print(f"   Registration status: {res.status_code}")
    print(f"   Response: {res.json()}")

    assert res.status_code in (200, 201), "Registration failed"

    # 2. Login as SMVITM Institution Admin and verify student is in list
    inst_session = requests.Session()
    login_res = inst_session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": "smvitm@sode-edu.in",
        "password": "password123"
    })
    print(f"\n2. Login as smvitm@sode-edu.in status: {login_res.status_code}")
    assert login_res.status_code == 200, "Institution admin login failed"

    stu_list_res = inst_session.get(f"{BASE_URL}/api/institution/students")
    print(f"   GET /api/institution/students status: {stu_list_res.status_code}")
    stu_data = stu_list_res.json()
    students = stu_data.get("students", [])
    print(f"   Total students listed for SMVITM: {len(students)}")
    
    found = any(s["email"] == new_email for s in students)
    print(f"   Newly registered student found in institution list: {found}")
    assert found, "Student was not found in institution student list!"

    # 3. Test existing student accepting invitation code via /api/institution/accept-invite
    student_session = requests.Session()
    stu_email = f"direct_stu_{ts}@example.com"
    reg_direct = requests.post(f"{BASE_URL}/api/auth/register", json={
        "display_name": "Direct Student",
        "email": stu_email,
        "password": "Password123!",
        "role": "student"
    })
    print(f"\n3. Registered independent student {stu_email}...")
    
    # Login as student
    stu_login = student_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": stu_email,
        "password": "Password123!"
    })
    print(f"   Student login status: {stu_login.status_code}")

    # Redeem invitation code for 'mahe'
    accept_res = student_session.post(f"{BASE_URL}/api/institution/accept-invite", json={
        "code": "mahe"
    })
    print(f"   Accept invite 'mahe' status: {accept_res.status_code}")
    print(f"   Response: {accept_res.json()}")
    assert accept_res.status_code == 200, "Accept invite failed"

    # Login as MAHE institution admin and verify
    mahe_session = requests.Session()
    mahe_session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": "mahe@gmail.com",
        "password": "password123"
    })
    mahe_stu_res = mahe_session.get(f"{BASE_URL}/api/institution/students")
    mahe_students = mahe_stu_res.json().get("students", [])
    found_mahe = any(s["email"] == stu_email for s in mahe_students)
    print(f"   Direct student now in MAHE institution list: {found_mahe}")
    assert found_mahe, "Direct student was not found in MAHE list after accepting invite!"

    print("\nSUCCESS: All student onboarding and institution linking tests passed permanently!")

if __name__ == "__main__":
    test_onboarding()
