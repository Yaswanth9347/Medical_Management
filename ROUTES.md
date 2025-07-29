# Application Route Map for Medical_Management

This file documents the main routes/endpoints in the Flask application and their purpose. Use this as a quick reference for navigation and debugging.

---

## Authentication
- `/login` (GET, POST): User login page
- `/logout`: Log out the current user
- `/register` (GET, POST): User registration page

## Dashboard
- `/` (GET): Main dashboard (requires login)

## Inventory
- `/inventory` (GET): View/search medicines (requires login)
- `/add_medicine` (GET, POST): Add a new medicine (requires login)
- `/edit_medicine/<int:id>` (GET, POST): Edit a medicine (requires login)
- `/delete_medicine/<int:id>` (GET, POST): Delete a medicine (requires login)

## Sales
- `/sales` (GET, POST): Manage sales (requires login)
- `/sales/<int:sale_id>/bill` (GET): Generate PDF bill for a sale (requires login)

## Customers
- `/customers` (GET, POST): List/add customers (requires login)
- `/edit_customer/<int:id>` (GET, POST): Edit a customer (requires login)
- `/delete_customer/<int:id>` (GET, POST): Delete a customer (requires login)
- `/customer/<int:customer_id>/history` (GET): View a customer's purchase history (requires login)

## Reports
- `/reports` (GET): Main reports page (requires login)
- `/download_report/<report_type>` (GET): Download Excel reports (requires login)
- `/reports/profit_loss` (GET): Profit/Loss report (requires login)

## Admin (User Management)
- `/admin/users` (GET): List users (admin only)
- `/admin/users/add` (GET, POST): Add user (admin only)
- `/admin/users/edit/<int:id>` (GET, POST): Edit user (admin only)
- `/admin/users/delete/<int:id>` (GET, POST): Delete user (admin only)

## Backup & Restore
- `/backup` (GET): Download database backup (requires login)
- `/restore` (POST): Restore database from backup (requires login)

## Password Reset
- `/reset_password` (GET, POST): Request password reset
- `/reset_password/<token>` (GET, POST): Reset password with token

---

**Note:** All routes except `/login`, `/register`, `/reset_password`, and `/reset_password/<token>` require authentication. Admin routes require admin privileges.
