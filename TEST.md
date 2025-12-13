# Team Nexus Testing Strategy & Edge Cases

This document outlines the testing protocols for the AI Conversational Loan Agent. It covers boundary conditions, adversarial inputs, and logic stress tests to ensure compliance with the system architecture.

## 1. Master Agent (Orchestration & State)
**Goal:** Ensure the "Brain" correctly routes users and maintains context without getting stuck.

| ID | Test Scenario | Input / Action | Expected Outcome | 
| :--- | :--- | :--- | :--- | :--- |
| **M-01** | **Context Switching** | User starts KYC, then suddenly asks: *"What is the interest rate again?"* | Agent switches to **Sales Agent** to answer, then guides user back to KYC verification. |
| **M-02** | **Irrelevant Input** | User types: *"Order me a pizza"* or *"Who won the match?"* | Agent politely declines and steers conversation back to the current loan stage. |
| **M-03** | **Agent Loop Prevention** | User repeatedly triggers the same tool error (e.g., bad PAN 5 times). | Agent detects the loop and offers a graceful exit or handover message instead of infinite retries. | 
| **M-04** | **Session Amnesia** | User provides Name, waits 30 mins, then provides PAN. | Agent retains the "Name" from memory and successfully calls the Verification tool with both inputs. |

---

## 2. Sales Agent (Intent & Negotiation)
**Goal:** Validate that the agent captures realistic loan parameters.

| ID | Test Scenario | Input / Action | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | **Negative/Zero Amount** | User asks for: *"-5000"* or *"0"* rupees. | Agent rejects input and asks for a valid positive integer. | 
| **S-02** | **Non-Numeric Amount** | User asks for: *"Five Lakhs"* (text) or *"10k"* (abbreviation). | Agent parses the text correctly OR asks user to enter digits (e.g., 500000). | 
| **S-03** | **Unrealistic Tenure** | User requests: *"1 month"* or *"100 years"*. | Agent enforces standard tenure limits (e.g., 12–60 months) and corrects the user. | 
| **S-04** | **Ambiguous Intent** | User says: *"I need money."* | Agent asks clarification questions to confirm it is for a *Personal Loan*. | 

---

## 3. Verification Agent (KYC & CRM)
**Goal:** Ensure robust handling of user identity data and external API failures.

| ID | Test Scenario | Input / Action | Expected Outcome | 
| :--- | :--- | :--- | :--- | :--- |
| **V-01** | **Invalid PAN Format** | User enters: *"ABC123"* (Too short) or *"$$$@@@"*. | Agent validates regex (e.g., 5 chars, 4 digits, 1 char) *before* calling the tool. | 
| **V-02** | **CRM API Failure** | **Mock CRM Service** is manually stopped (Terminal 1 killed). | Agent reports a system error politely: *"Unable to verify details right now"* (Does not crash). | 
| **V-03** | **Identity Mismatch** | User says name is *"John"*, but PAN provided belongs to *"Jane"*. | Agent flags the discrepancy and asks the user to re-confirm details. | 

---

## 4. Underwriting Agent (Core Logic Gates)
**Goal:** specific logic rules: `Limit`, `2x Limit`, `Score < 700`, `EMI > 50% Salary`.

| ID | Test Scenario | Input / Action | Expected Outcome | 
| :--- | :--- | :--- | :--- | :--- |
| **U-01** | **Exact Pre-Approved Limit** | Loan Amount = **Limit** (e.g., 2L). | **Instant Approval** (No Salary Slip asked). | 
| **U-02** | **Exact 2x Limit** | Loan Amount = **2x Limit** (e.g., 4L). | **Salary Check Triggered** (Request Monthly Salary). | 
| **U-03** | **Just Over 2x Limit** | Loan Amount = **2x Limit + 1** (e.g., 4,00,001). | **Instant Rejection** (Reason: Exceeds 2x limit). | 
| **U-04** | **Credit Score Boundary** | Score = **700**. | **Proceed** (Passes check). | 
| **U-05** | **Credit Score Failure** | Score = **699**. | **Rejection** (Reason: Score below 700). | 
| **U-06** | **EMI/Salary Boundary** | EMI calculated is exactly **50%** of provided Salary. | **Approved**. | 
| **U-07** | **EMI/Salary Failure** | EMI calculated is **50.1%** of provided Salary. | **Rejection** (Reason: EMI burden too high). | 
| **U-08** | **High Score, High Loan** | Score = 850, but Amount > 2x Limit. | **Rejection** (Rule priority: 2x Limit > Credit Score). | 
| **U-09** | **Zero Salary Input** | User enters *"0"* as salary when asked. | Agent handles division error or rejects immediately. | 

---

## 5. Sanction Letter Agent (Output)
**Goal:** Ensure the final deliverable is accurate and accessible.

| ID | Test Scenario | Input / Action | Expected Outcome | 
| :--- | :--- | :--- | :--- | :--- |
| **D-01** | **Special Characters** | User Name: *"Renée O'Connor-Smith"*. | PDF generates correctly without encoding errors (e.g., no `Ã©`). | 
| **D-02** | **Long Name String** | User Name: 100+ characters long. | PDF layout handles wrapping; text does not spill off-page. | 
| **D-03** | **File Permissions** | System attempts to save PDF to a read-only folder. | System catches write error and alerts user (or fallback). | 
