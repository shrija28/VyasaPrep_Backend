import requests

BASE_URL = "http://127.0.0.1:8000"

def test_admin_dashboard():
    session = requests.Session()
    login_res = session.post(f"{BASE_URL}/api/auth/admin/login", json={
        "username": "admin@vyasaprep.com",
        "password": "admin"
    })
    print("Admin login status:", login_res.status_code)
    if login_res.status_code != 200:
        login_res = session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "username": "admin@mre.com",
            "password": "admin"
        })
        print("Fallback admin login status:", login_res.status_code)

    dash_res = session.get(f"{BASE_URL}/api/admin/dashboard")
    print("GET /api/admin/dashboard status:", dash_res.status_code)
    if dash_res.status_code == 200:
        d = dash_res.json()
        print("\n--- KPI METRICS ---")
        print(d.get("kpis"))
        print("\n--- INSTITUTION QUESTION COUNTS ---")
        print(d.get("institution_question_counts"))
        print("\n--- RECENT INSTITUTIONS ---")
        print(d.get("recent_institutions"))
        print("\n--- DIRECT STUDENTS ---")
        print(d.get("direct_students")[:3])
        print("\n--- RECENT ACTIVITY ---")
        print(d.get("recent_activity")[:3])
    else:
        print("Error response:", dash_res.text)

if __name__ == "__main__":
    test_admin_dashboard()
