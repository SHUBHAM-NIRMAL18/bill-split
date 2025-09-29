# 💸 Bill-Split Backend

A collaborative expense-sharing and group management backend built with **Django REST Framework**, designed to power applications like **Splitwise**.  
This backend provides full support for **user management, groups, expenses, balances, settlements, and invitations** with a ready-to-use API.

---

## 🚀 Features Overview

| Feature          | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| **User Management** | Email-based login, JWT authentication, profile management, password reset |
| **Groups**          | Create/manage groups, add/remove members, invite via email               |
| **Expenses**        | Add, split, and manage group expenses (equal/unequal/percentage splits)  |
| **Balances**        | Simplified debt calculation: shows who owes whom and how much            |
| **Settlements**     | Settle debts, with history tracking and validation                        |
| **Activity Feed**   | Track group activities (expenses, settlements, members joining/leaving)   |
| **Invitations**     | Token-based invitation system with expiration support via email           |

---

## 🧩 Core Entities (Database Models)

1. **User** – Custom user model (email as username, avatar support).
2. **Group** – Collection of members & expenses; categorized (Trip, Home, etc.).
3. **Category** – Classifies groups for better organization.
4. **Membership** – Links users to groups (role-based: owner, admin, member).
5. **Expense** – Group expenses with title, amount, payer, split type.
6. **ExpenseParticipant** – Each user’s share in an expense (amount/percentage).
7. **Invitation** – Email invitation system with token acceptance.

---

## 🛠️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL / SQLite (for local development)
- **Auth:** JWT-based authentication
- **Media:** File upload support for avatars (Users & Groups)
- **Email:** SMTP integration for invitations (Mailtrap.io)

---

## ⚡ API Overview

**Base URL:** `/api/v1/`


## ⚙️ Development Setup

Follow the steps below to run the backend locally.

### 1. Clone the Repo
```bash
git clone https://github.com/SHUBHAM-NIRMAL18/bill-split.git
cd bill-split

