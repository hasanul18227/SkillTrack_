# SkillTrack - Evaluation 1 (Django, three apps)

Three team members work in one repository. Each app is owned by one person.

| Part | Feature (from the report) | App | Owner |
|---|---|---|---|
| Part 1 | Authentication and role-based authorization | `accounts` | Member 1 (Scrum Master) |
| Part 2 | Training module management | `modules` | Member 2 |
| Part 3 | Employee enrollment | `enrollment` | Member 3 |

Shared files (`skilltrack/settings.py`, `skilltrack/urls.py`, `templates/base.html`) are owned by Part 1.
Other members ask Part 1 before changing them.

## File ownership

**Part 1 - accounts (and shared files)**

- `manage.py`, `requirements.txt`, `.gitignore`, `README.md`
- `skilltrack/` (settings, main urls)
- `accounts/` (models, permissions, forms, views, urls, context processor)
- `templates/base.html`, `templates/home.html`, `templates/form_page.html`, `templates/message.html`, `templates/403.html`
- `templates/registration/` (login, password reset)

**Part 2 - modules**

- `modules/` (Module and Feedback models, forms, views, urls)
- `templates/modules/` (catalog, module details, HR dashboard, module list for HR)

**Part 3 - enrollment**

- `enrollment/` (Enrollment, Notification and UserBadge models, forms, services, views, urls, certificate, deadline command)
- `templates/enrollment/` (employee dashboard, manager dashboard, my courses, notifications, team progress)

## Setup

Requires Python 3.10 or newer.

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations accounts modules enrollment
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Always pass the app names to `makemigrations`, for example `python manage.py makemigrations modules`.
Each person runs `makemigrations` only for their own app.

## How the apps depend on each other

- `accounts` provides login, roles (`UserProfile`), permission helpers and the navigation context.
- `modules` owns `Module`. `enrollment` points to it with the string `"modules.Module"`.
- `accounts.views.dashboard` is a router: HR gets `modules.views.hr_dashboard`, managers and employees get pages from `enrollment.views`.
- `modules` and `enrollment` use `accounts.permissions` for role checks.

There is no circular import between Python files. The three apps refer to each other in one direction for models and in both directions only through the permission helpers and the dashboard router. Keep it that way.

## Test roles

1. Register an HR account, a Manager (department "Engineering") and an Employee (same department).
2. HR adds modules under **Manage modules**.
3. Employee enrolls under **Available modules**, then uses **My courses**.
4. Employee opens `/manage/modules/` and gets the Access denied page.
5. Manager uses **Team** and **Assign**.

## Git workflow

- Never push to `main` directly. Use one branch per part: `part1-accounts`, `part2-modules`, `part3-enrollment`.
- Run `git pull origin main` before you start work.
- Commit only files in your own part. Check with `git status` first.
- Open a Pull Request into `main`. Part 1 reviews and merges first, then Part 2, then Part 3.
