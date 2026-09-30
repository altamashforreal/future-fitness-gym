import os

routers = ['auth', 'checkins', 'memberships', 'payments', 'plans', 'dashboard']
for r in routers:
    with open(f'app/api/routes/{r}.py', 'w') as f:
        f.write(f'from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/{r}", tags=["{r.title()}"])\n')
