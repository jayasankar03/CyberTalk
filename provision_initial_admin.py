
from database import (
    SessionLocal,
    create_db_tables,
    migrate_user_account_lifecycle,
    migrate_audit_log_account_status,
    migrate_primary_admin,
)
from user_model import User


TARGET_USERNAME = "jayasankar_03"


# Ensure the database schema is up to date.
create_db_tables()
migrate_user_account_lifecycle()
migrate_audit_log_account_status()
migrate_primary_admin()


db = SessionLocal()

try:
    user = (
        db.query(User)
        .filter(User.username == TARGET_USERNAME)
        .first()
    )

    if user is None:
        print(f"User '{TARGET_USERNAME}' was not found.")

    elif not user.is_active:
        print("The selected account is inactive. Setup cancelled.")

    else:
        existing_primary = (
            db.query(User)
            .filter(
                User.is_primary_admin.is_(True),
                User.id != user.id,
            )
            .first()
        )

        if existing_primary is not None:
            print(
                "Another primary administrator already exists. "
                "Setup cancelled."
            )

        else:
            user.role = "admin"
            user.is_primary_admin = True

            db.commit()
            db.refresh(user)

            print("Primary administrator configured successfully.")
            print(f"User ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print(f"Primary Admin: {user.is_primary_admin}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
