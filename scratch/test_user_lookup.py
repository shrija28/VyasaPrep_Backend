import jwt
import datetime
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User
from smartkcet.middleware.rbac import current_user
from smartkcet.auth.tokens import issue_token

session = SessionLocal()

# Test MGM student
u = session.query(User).filter_by(email='rohu@gmail.com').first()
print(f"User in DB: {u.email}, ID: {u.id}, Inst: {u.institution_id}, KCET: {u.kcet_student_id}")

# 1. Test token issued with sub = str(u.id)
t1, _, _, _ = issue_token(sub=str(u.id), role='student', student_subtype='institution_linked', institution_id=str(u.institution_id), subscription_status='active')
# 2. Test token issued with sub = u.kcet_student_id
t2, _, _, _ = issue_token(sub=u.kcet_student_id, role='student', student_subtype='institution_linked', institution_id=str(u.institution_id), subscription_status='active')
# 3. Test token issued with sub = u.email
t3, _, _, _ = issue_token(sub=u.email, role='student', student_subtype='institution_linked', institution_id=str(u.institution_id), subscription_status='active')

print("Token 1 sub=str(u.id):", t1[:20])
print("Token 2 sub=kcet_student_id:", t2[:20])
print("Token 3 sub=email:", t3[:20])

session.close()
