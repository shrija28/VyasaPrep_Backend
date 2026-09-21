import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    session = requests.Session()
    
    unique_suffix = str(int(time.time()))
    admin_email = f"perm_admin_{unique_suffix}@inst.com"
    inst_name = f"PermTestInst_{unique_suffix}"
    
    print("--- 1. Register New Institution ---")
    reg_inst_resp = session.post(f"{BASE_URL}/api/institution/register", json={
        "name": inst_name,
        "admin_email": admin_email,
        "admin_password": "Password123",
        "contact_phone": "9876543210"
    })
    print(f"Inst Reg Status: {reg_inst_resp.status_code}")
    print(f"Inst Reg Body: {reg_inst_resp.json()}")
    assert reg_inst_resp.status_code == 201, "Institution registration failed"

    print("\n--- 2. Login as Institution Admin ---")
    resp = session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": admin_email,
        "password": "Password123"
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    assert resp.status_code == 200, "Admin login failed"

    print("\n--- 3. Call GET /api/institution/students ---")
    resp = session.get(f"{BASE_URL}/api/institution/students")
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Total Students initial: {data.get('total_students')}")
    print(f"Students count in list: {len(data.get('students', []))}")
    assert resp.status_code == 200, f"GET /api/institution/students failed: {data}"
    assert data.get("total_students") == 0, "Initial student count should be 0"

    print("\n--- 4. Call GET /api/institution/dashboard ---")
    resp = session.get(f"{BASE_URL}/api/institution/dashboard")
    print(f"Status: {resp.status_code}")
    dash_data = resp.json()
    print(f"Dashboard total_students initial: {dash_data.get('total_students')}")
    assert resp.status_code == 200, "Dashboard endpoint failed"
    assert dash_data.get("total_students") == 0, "Dashboard initial count should be 0"

    print("\n--- 5. Generate Invitation Code ---")
    resp = session.post(f"{BASE_URL}/api/institution/invite")
    print(f"Status: {resp.status_code}")
    inv_data = resp.json()
    code = inv_data.get("code")
    print(f"Generated Invitation Code: {code}")
    assert resp.status_code == 201, "Invitation generation failed"

    print("\n--- 6. Register New Student with mixed-case Code ---")
    student_session = requests.Session()
    mixed_code = "  " + code.upper() + "  "
    reg_student_email = f"perm_student_{unique_suffix}@gmail.com"
    reg_resp = student_session.post(f"{BASE_URL}/api/auth/register", json={
        "email": reg_student_email,
        "password": "Password123",
        "display_name": "Permanent Fix Student",
        "invite_code": mixed_code
    })
    print(f"Registration Status: {reg_resp.status_code}")
    print(f"Registration Response: {reg_resp.json()}")
    assert reg_resp.status_code == 201, "Student registration failed"

    print("\n--- 7. Verify /api/auth/me endpoint for student ---")
    me_resp = student_session.get(f"{BASE_URL}/api/auth/me")
    print(f"Me Status: {me_resp.status_code}")
    me_data = me_resp.json()
    print(f"Me Data: {json.dumps(me_data, indent=2)}")
    assert me_data.get("institution_id") is not None, "Student not linked to institution"

    print("\n--- 8. Re-check Institution Dashboard for Admin ---")
    resp = session.get(f"{BASE_URL}/api/institution/dashboard")
    new_dash_data = resp.json()
    print(f"New Dashboard total_students: {new_dash_data.get('total_students')}")
    assert new_dash_data.get("total_students") == 1, "Student count did not update to 1 on dashboard"

    print("\n--- 9. Re-check Institution Students API for Admin ---")
    resp = session.get(f"{BASE_URL}/api/institution/students")
    new_students_data = resp.json()
    print(f"New Students List Count: {new_students_data.get('total_students')}")
    print(f"Students array length: {len(new_students_data.get('students', []))}")
    assert new_students_data.get("total_students") == 1, "Students count in list did not update to 1"
    assert len(new_students_data.get("students", [])) == 1, "Students array does not contain 1 student"

    print("\n=======================================================")
    print("ALL TESTS PASSED PERFECTLY! THE ISSUE IS PERMANENTLY FIXED.")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
