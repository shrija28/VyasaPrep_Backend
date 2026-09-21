import os

path = r"C:\Users\SHRIJA SANIL\VyasaPrep_Frontend\src\App.jsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = '<Route path="dashboard" element={<AdminDashboard />} />'
replacement = '''<Route path="dashboard" element={<AdminDashboard />} />
            <Route path="dashboard." element={<Navigate to="/admin/dashboard" replace />} />'''

if target in text:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(target, replacement))
    print("Updated App.jsx with trailing dot route redirect")
else:
    print("Target route not found in App.jsx")
