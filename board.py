from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Task, Worker, db
from datetime import date, datetime, timedelta
import logging
import re

board_bp = Blueprint("board", __name__)
logger = logging.getLogger(__name__)

def sanitize_input(text, max_length=500):
    """Sanitize user input to prevent XSS and injection attacks."""
    if not text:
        return ""
    text = str(text)[:max_length].strip()
    # Remove potentially dangerous characters
    text = re.sub(r'[<>\"\'\\]', '', text)
    return text

def promote_scheduled_task(worker_id):
    """Promote first scheduled task for a worker to active status."""
    if not worker_id:
        return
    
    scheduled_task = Task.query.filter_by(
        assigned_worker=worker_id,
        status="scheduled"
    ).order_by(Task.due_date).first()
    
    if scheduled_task:
        scheduled_task.status = "active"
        db.session.commit()
        logger.info(f"Task {scheduled_task.id} promoted to active for worker {worker_id}")


@board_bp.route("/")
@login_required
def index():
    """Redirect to supervisor board for authenticated users."""
    return redirect(url_for("board.supervisor_board"))

@board_bp.route("/public")
@login_required
def public_board():
    tasks = Task.query.all()
    today = date.today()
    workers = Worker.query.all()
    worker_lookup = {w.id: w.name for w in workers}
    return render_template("public_board.html", tasks=tasks, today=today, worker_lookup=worker_lookup)

@board_bp.route("/supervisor", methods=["GET", "POST"])
@login_required
def supervisor_board():

    # ---------- POST: ADD TASK ----------
    if request.method == "POST":
        try:
            worker_id = request.form.get("assigned_worker") or None
            status = "not_started"

            # Validate and sanitize inputs
            title = sanitize_input(request.form.get("title", ""), 100)
            description = sanitize_input(request.form.get("description", ""), 500)
            priority = request.form.get("priority", "medium")
            
            if not title:
                flash("Task title is required", "error")
                return redirect(url_for("board.supervisor_board"))
            
            # Validate priority
            if priority not in ["low", "medium", "high", "critical"]:
                priority = "medium"
            
            # Check worker capacity
            if worker_id:
                try:
                    worker_id = int(worker_id)
                    active_count = Task.query.filter_by(
                        assigned_worker=worker_id,
                        status="active"
                    ).count()

                    if active_count >= 3:
                        status = "scheduled"
                        flash("Worker at capacity - task added to backlog", "info")
                except (ValueError, TypeError):
                    worker_id = None

            try:
                due_date = datetime.strptime(
                    request.form.get("due_date", ""), "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                flash("Invalid due date format", "error")
                return redirect(url_for("board.supervisor_board"))

            task = Task(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                assigned_worker=worker_id,
                status=status
            )

            db.session.add(task)
            db.session.commit()
            
            logger.info(f"Task created by {current_user.username}: {title} (ID: {task.id})")
            flash(f"Task '{title}' created successfully", "info")
            return redirect(url_for("board.supervisor_board"))
        
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            db.session.rollback()
            flash("An error occurred while creating the task", "error")
            return redirect(url_for("board.supervisor_board"))

    # ---------- GET: RENDER BOARD ----------

    current_tasks = Task.query.filter(
        Task.status.in_(["not_started", "active"])
    ).order_by(Task.id.desc()).all()

    backlog_tasks = Task.query.filter_by(
        status="scheduled"
    ).order_by(Task.due_date).all()

    workers = Worker.query.all()
    worker_lookup = {w.id: w.name for w in workers}

    worker_summary = []
    for worker in workers:
        active_count = Task.query.filter_by(
            assigned_worker=worker.id,
            status="active"
        ).count()

        if active_count <= 1:
            label = "Idle"
        elif active_count == 2:
            label = "Available"
        else:
            label = "At capacity"

        worker_summary.append({
            "name": worker.name,
            "count": active_count,
            "label": label
        })
    return render_template(
    "supervisor_board.html",
    current_tasks=current_tasks,
    backlog_tasks=backlog_tasks,
    workers=workers,
    worker_lookup=worker_lookup,
    worker_summary=worker_summary
    )

@board_bp.route("/task/<int:task_id>")
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template("task_modal.html", task=task)

@board_bp.route("/task/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        new_status = request.form.get("status")

        # Validate status
        if new_status not in ["not_started", "active", "scheduled", "done"]:
            flash("Invalid status", "error")
            return redirect(url_for("board.supervisor_board"))

        old_status = task.status
        
        if new_status == "done":
            task.status = "done"
            task.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Task {task_id} marked as done by {current_user.username}")
            
            # Promote scheduled task if worker has one
            if task.assigned_worker:
                promote_scheduled_task(task.assigned_worker)
        else:
            task.status = new_status
            task.completed_at = None
            db.session.commit()
            logger.info(f"Task {task_id} status changed from {old_status} to {new_status} by {current_user.username}")

        return redirect(url_for("board.supervisor_board"))
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        flash("An error occurred while updating task status", "error")
        return redirect(url_for("board.supervisor_board"))

@board_bp.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        task_title = task.title
        
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"Task {task_id} ('{task_title}') deleted by {current_user.username}")
        flash(f"Task '{task_title}' deleted successfully", "info")
        return redirect(url_for("board.supervisor_board"))
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        flash("An error occurred while deleting the task", "error")
        return redirect(url_for("board.supervisor_board"))