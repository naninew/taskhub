# [Ngày 7] Background tasks module — gửi email notification (dev giả lập qua logger)

import logging

logger = logging.getLogger("taskhub")


def send_assignment_email(user_email: str, task_title: str) -> None:
    """[Ngày 7] Hàm gửi email giả lập (Background Task) khi task được assign cho user."""
    logger.info(f"[BACKGROUND TASK] Email notification sent to '{user_email}' for task assignment: '{task_title}'")
