from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models.session import Session, db
from models.slot import Slot
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
from datetime import datetime

sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    session_obj = Session.query.get_or_404(session_id)
    
    # Check if user is authorized to view this session
    if current_user.id not in [session_obj.mentor_id, session_obj.student_id]:
        flash('You are not authorized to view this session')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('session_detail.html', session=session_obj)

@sessions_bp.route('/session/<int:session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    session_obj = Session.query.get_or_404(session_id)
    
    # Only mentor can complete session
    if current_user.id != session_obj.mentor_id:
        flash('Only the mentor can complete this session')
        return redirect(url_for('sessions.view_session', session_id=session_id))
    
    session_obj.status = 'completed'
    session_obj.summary = request.form['summary']
    session_obj.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Session completed successfully!')
    return redirect(url_for('sessions.view_session', session_id=session_id))

@sessions_bp.route('/session/<int:session_id>/feedback', methods=['POST'])
@login_required
def add_feedback(session_id):
    session_obj = Session.query.get_or_404(session_id)
    
    # Only student can add feedback
    if current_user.id != session_obj.student_id:
        flash('Only the student can add feedback')
        return redirect(url_for('sessions.view_session', session_id=session_id))
    
    session_obj.feedback = request.form['feedback']
    session_obj.rating = int(request.form['rating'])
    session_obj.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Feedback added successfully!')
    return redirect(url_for('sessions.view_session', session_id=session_id))

@sessions_bp.route('/session/<int:session_id>/export_pdf')
@login_required
def export_session_pdf(session_id):
    session_obj = Session.query.get_or_404(session_id)
    
    # Check if user is authorized
    if current_user.id not in [session_obj.mentor_id, session_obj.student_id]:
        flash('You are not authorized to export this session')
        return redirect(url_for('dashboard.dashboard'))
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content to PDF
    p.drawString(100, 750, f"Session Report: {session_obj.title}")
    p.drawString(100, 720, f"Mentor: {session_obj.mentor.full_name}")
    p.drawString(100, 700, f"Student: {session_obj.student.full_name}")
    p.drawString(100, 680, f"Date: {session_obj.slot.start_time.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 660, f"Status: {session_obj.status}")
    
    if session_obj.summary:
        p.drawString(100, 620, "Summary:")
        # Simple text wrapping for summary
        summary_lines = session_obj.summary.split('\n')
        y_pos = 600
        for line in summary_lines:
            if len(line) > 80:
                # Simple word wrap
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if len(current_line + word) < 80:
                        current_line += word + ' '
                    else:
                        p.drawString(100, y_pos, current_line)
                        y_pos -= 20
                        current_line = word + ' '
                if current_line:
                    p.drawString(100, y_pos, current_line)
                    y_pos -= 20
            else:
                p.drawString(100, y_pos, line)
                y_pos -= 20
    
    if session_obj.feedback:
        p.drawString(100, y_pos - 20, "Student Feedback:")
        p.drawString(100, y_pos - 40, session_obj.feedback)
        if session_obj.rating:
            p.drawString(100, y_pos - 60, f"Rating: {session_obj.rating}/5")
    
    p.save()
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"session_{session_id}_report.pdf",
        mimetype='application/pdf'
    )

@sessions_bp.route('/my_sessions')
@login_required
def my_sessions():
    if current_user.role == 'mentor':
        sessions = Session.query.filter_by(mentor_id=current_user.id).all()
    else:
        sessions = Session.query.filter_by(student_id=current_user.id).all()
    
    return render_template('my_sessions.html', sessions=sessions)
