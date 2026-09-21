import requests

BASE_URL = "http://127.0.0.1:8000"

def test_inst_endpoints(email, password="password123"):
    print(f"\n--- Testing for Institution Admin: {email} ---")
    session = requests.Session()
    login_resp = session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": email,
        "password": password
    })
    print(f"Login status: {login_resp.status_code}")
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        return

    # 1. GET /api/institution/batches
    res_batches = session.get(f"{BASE_URL}/api/institution/batches")
    print(f"GET /api/institution/batches -> Status: {res_batches.status_code}")
    if res_batches.status_code == 200:
        print(f" Batches count: {len(res_batches.json().get('batches', []))}")
    else:
        print(f" Error: {res_batches.text}")

    # 2. GET /api/institution/students
    res_students = session.get(f"{BASE_URL}/api/institution/students")
    print(f"GET /api/institution/students -> Status: {res_students.status_code}")
    if res_students.status_code == 200:
        data = res_students.json()
        print(f" Total Students field: {data.get('total_students')}")
        print(f" Students array length: {len(data.get('students', []))}")
        print(f" Institution object students length: {len(data.get('institution', {}).get('students', []))}")
        print(f" Sample student in students array: {data.get('students', [])[:1]}")
    else:
        print(f" Error: {res_students.text}")

    # 3. GET /api/institution/invitations
    res_inv = session.get(f"{BASE_URL}/api/institution/invitations")
    print(f"GET /api/institution/invitations -> Status: {res_inv.status_code}")
    if res_inv.status_code == 200:
        print(f" Invitations count: {len(res_inv.json().get('invitations', []))}")
    else:
        print(f" Error: {res_inv.text}")

if __name__ == "__main__":
    # Test for smvitm
    test_inst_endpoints("smvitm@sode-edu.in")
    # Test for mahe
    test_inst_endpoints("mahe@gmail.com")
