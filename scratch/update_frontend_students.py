import os

path = r"C:\Users\SHRIJA SANIL\VyasaPrep_Frontend\src\pages\auto\InstitutionStudents.jsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = '''      // 2. Fetch Students
      const stuRes = await fetch('/api/institution/students', { credentials: 'include' });
      if (stuRes.ok) {
        const sData = await stuRes.json();
        setStudents(sData.students || []);
      }'''

replacement = '''      // 2. Fetch Students
      const stuRes = await fetch('/api/institution/students', { credentials: 'include' });
      if (stuRes.ok) {
        const sData = await stuRes.json();
        const rawList = sData.students || sData.institution?.students || [];
        const normalized = rawList.map(s => ({
          user_id: s.user_id || s.id,
          display_name: s.display_name || s.name || s.email,
          email: s.email,
          kcet_student_id: s.kcet_student_id || s.id,
          linked_at: s.linked_at,
          student_subtype: s.student_subtype || s.subtype,
          batch_id: s.batch_id || null,
          batch_name: s.batch_name || null
        }));
        setStudents(normalized);
      }'''

if target in text:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(target, replacement))
    print("Updated InstitutionStudents.jsx successfully")
else:
    print("Target string not found in InstitutionStudents.jsx")
