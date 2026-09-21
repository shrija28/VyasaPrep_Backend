path = r"C:\Users\SHRIJA SANIL\VyasaPrep_Frontend\src\pages\RegisterPage.jsx"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'student_subtype: joinType === \'via_code\' ? "institutional" : "independent"' in line:
        new_lines.append('        student_subtype: joinType === \'via_code\' ? "institution_linked" : "direct_subscriber",\n')
        new_lines.append('        invite_code: joinType === \'via_code\' ? joinCode : null,\n')
        new_lines.append('        code: joinType === \'via_code\' ? joinCode : null,\n')
    else:
        new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Updated RegisterPage.jsx successfully")
