# The format is: process_name: command_to_run

# 1. The "Brain" (Runs DB setup first, then starts the app)
# The '&&' ensures the app only starts if the DB setup succeeds
orchestrator: python backend/setup_database.py && python backend/orchestrator/app.py

# 2. The "Bank" Mocks
crm_service: python backend/mock_services/crm.py
credit_service: python backend/mock_services/credit_bureau.py
offer_service: python backend/mock_services/offer_mart.py