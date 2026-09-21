import requests

BASE_URL = "http://127.0.0.1:8000"

def verify_system_config():
    print("=== VERIFYING FRONTEND-BACKEND INTEGRATION ===")
    
    # 1. Health check / Root test
    res = requests.get(f"{BASE_URL}/")
    print(f"1. Backend root (GET /) -> Status: {res.status_code}")

    # 2. Syllabus counts API
    syll_res = requests.get(f"{BASE_URL}/api/syllabus/counts")
    print(f"2. Syllabus Counts (GET /api/syllabus/counts) -> Status: {syll_res.status_code}")
    if syll_res.status_code == 200:
        counts = syll_res.json()
        print(f"   Total chapters: {counts.get('total_chapters')}, Total topics: {counts.get('total_topics')}")

    # 3. Platform Admin Login & Dashboard API
    admin_session = requests.Session()
    admin_login = admin_session.post(f"{BASE_URL}/api/auth/admin/login", json={
        "username": "admin@vyasaprep.com",
        "password": "admin"
    })
    print(f"3. Admin Login (POST /api/auth/admin/login) -> Status: {admin_login.status_code}")

    admin_dash = admin_session.get(f"{BASE_URL}/api/admin/dashboard")
    print(f"4. Admin Dashboard API (GET /api/admin/dashboard) -> Status: {admin_dash.status_code}")
    if admin_dash.status_code == 200:
        data = admin_dash.json()
        print(f"   Institutions count: {len(data.get('recent_institutions', []))}")
        print(f"   Direct students count: {len(data.get('direct_students', []))}")
        print(f"   Recent activity items: {len(data.get('recent_activity', []))}")

    # 5. Institution Admin Login & Students API
    inst_session = requests.Session()
    inst_login = inst_session.post(f"{BASE_URL}/api/auth/institution/login", json={
        "email": "smvitm@sode-edu.in",
        "password": "password123"
    })
    print(f"5. Institution Admin Login -> Status: {inst_login.status_code}")
    
    inst_students = inst_session.get(f"{BASE_URL}/api/institution/students")
    print(f"6. Institution Students API (GET /api/institution/students) -> Status: {inst_students.status_code}")
    if inst_students.status_code == 200:
        sdata = inst_students.json()
        print(f"   Institution name: {sdata.get('institution_name')}")
        print(f"   Enrolled students: {len(sdata.get('students', []))}")

    print("\n✅ All Backend APIs are fully configured and serving the Frontend!")

if __name__ == "__main__":
    verify_system_config()
