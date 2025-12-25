"""
Database error handling utilities.
"""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from apex.core.exceptions import ConflictError, DatabaseError


def handle_database_error(error: Exception, context: str = "database operation") -> Exception:
    """
    Convert SQLAlchemy errors to Apex exceptions without assuming user-required fields.

    Args:
        error: SQLAlchemy exception
        context: Context description for error message

    Returns:
        Appropriate Apex exception
    """
    if isinstance(error, IntegrityError):
        error_str = str(error.orig).lower() if hasattr(error, "orig") else str(error).lower()

        # Unique/duplicate constraints we can safely identify
        if "unique" in error_str or "duplicate" in error_str:
            if "email" in error_str:
                return ConflictError("Email already exists", details={"field": "email"})
            if "username" in error_str:
                return ConflictError("Username already exists", details={"field": "username"})
            return ConflictError(
                "Duplicate entry violation",
                details={"original_error": str(error), "hint": "Check your model's unique constraints"},
            )

        # Foreign key issues
        if "foreign key" in error_str:
            return DatabaseError(
                "Foreign key constraint violation",
                details={"original_error": str(error), "hint": "Ensure related record exists"},
            )

        # Generic integrity issue – do not guess missing required fields
        return DatabaseError(
            f"Database integrity error: {context}",
            details={"original_error": str(error), "hint": "Review your model constraints"},
        )

    if isinstance(error, SQLAlchemyError):
        return DatabaseError(
            f"Database error during {context}: {str(error)}",
            details={"original_error": str(error)},
        )

    return DatabaseError(
        f"Unexpected database error during {context}: {str(error)}",
        details={"original_error": str(error)},
    )


__all__ = ["handle_database_error"]







