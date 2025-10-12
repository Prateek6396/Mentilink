from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.session import Session
from models.slot import Slot, db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'mentor':
        # Get mentor's upcoming sessions
        upcoming_sessions = Session.query.filter_by(
            mentor_id=current_user.id,
            status='scheduled'
        ).join(Slot).filter(Slot.start_time > datetime.utcnow()).all()
        
        # Get mentor's slots
        slots = Slot.query.filter_by(mentor_id=current_user.id).all()
        
        return render_template('mentor_dashboard.html', 
                             sessions=upcoming_sessions, 
                             slots=slots)
    else:
        # Get student's upcoming sessions
        upcoming_sessions = Session.query.filter_by(
            student_id=current_user.id,
            status='scheduled'
        ).join(Slot).filter(Slot.start_time > datetime.utcnow()).all()
        
        # Get available mentors
        mentors = User.query.filter_by(role='mentor').all()
        
        return render_template('student_dashboard.html', 
                             sessions=upcoming_sessions, 
                             mentors=mentors)

@dashboard_bp.route('/create_slot', methods=['GET', 'POST'])
@login_required
def create_slot():
    if current_user.role != 'mentor':
        flash('Only mentors can create slots')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        
        slot = Slot(
            mentor_id=current_user.id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(slot)
        db.session.commit()
        
        flash('Slot created successfully!')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('create_slot.html')

@dashboard_bp.route('/book_session/<int:slot_id>', methods=['POST'])
@login_required
def book_session(slot_id):
    if current_user.role != 'student':
        flash('Only students can book sessions')
        return redirect(url_for('dashboard.dashboard'))
    
    slot = Slot.query.get_or_404(slot_id)
    
    if not slot.is_available:
        flash('This slot is no longer available')
        return redirect(url_for('dashboard.dashboard'))
    
    # Create session
    session_obj = Session(
        mentor_id=slot.mentor_id,
        student_id=current_user.id,
        slot_id=slot.id,
        title=request.form['title'],
        description=request.form.get('description', '')
    )
    
    # Mark slot as unavailable
    slot.is_available = False
    
    db.session.add(session_obj)
    db.session.commit()
    
    flash('Session booked successfully!')
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/available_slots')
@login_required
def available_slots():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    slots = Slot.query.filter_by(is_available=True).filter(
        Slot.start_time > datetime.utcnow()
    ).all()
    
    slots_data = []
    for slot in slots:
        slots_data.append({
            'id': slot.id,
            'mentor_name': slot.mentor_user.full_name,
            'title': slot.title,
            'description': slot.description,
            'start_time': slot.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': slot.end_time.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(slots_data)
