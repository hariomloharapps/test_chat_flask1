# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
from llm_service import LLMService
from models import db, Session, Conversation
import uuid

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize LLM service with error handling
try:
    llm = LLMService(api_key="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")
except Exception as e:
    print(f"Error initializing LLM service: {e}")
    llm = None

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create_session', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create new session
        new_session = Session(
            session_id=session_id,
            system_prompt=system_prompt
        )
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({
            'session_id': session_id,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
    


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not request.is_json:
            return jsonify({
                'error': 'Invalid request format. JSON required.',
                'timestamp': datetime.now().strftime("%H:%M"),
                'status': 'error'
            }), 400

        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()
        
        if not session_id:
            return jsonify({
                'error': 'No session ID provided',
                'status': 'error'
            }), 400

        # Get session from database
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'error': 'Invalid session ID',
                'status': 'error'
            }), 404

        # Store user message
        user_conv = Conversation(
            session_id=session.id,
            role='user',
            content=user_message
        )
        db.session.add(user_conv)
        db.session.commit()

        # Get conversation history
        history = []
        conversations = Conversation.query.filter_by(session_id=session.id).order_by(Conversation.timestamp).all()
        for conv in conversations:
            history.append({
                'content': conv.content,
                'isUser': conv.role == 'user'
            })

        # Update LLM service with session's system prompt
        llm.system_prompt = session.system_prompt

        # Get response from LLM service
        result = llm.get_response(user_message, history)

        if result.get('status') == 'error':
            return jsonify(result), 500

        # Store assistant response
        assistant_conv = Conversation(
            session_id=session.id,
            role='assistant',
            content=result['response']
        )
        db.session.add(assistant_conv)
        db.session.commit()

        return jsonify({
            'response': result['response'],
            'timestamp': datetime.now().strftime("%H:%M"),
            'status': 'success'
        })

    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().strftime("%H:%M"),
            'status': 'error'
        }), 500

@app.route('/get_sessions', methods=['GET'])
def get_sessions():
    try:
        sessions = Session.query.order_by(Session.created_at.desc()).all()
        return jsonify({
            'sessions': [{
                'session_id': session.session_id,
                'system_prompt': session.system_prompt,
                'created_at': session.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for session in sessions],
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/get_conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    try:
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'error': 'Session not found',
                'status': 'error'
            }), 404

        conversations = Conversation.query.filter_by(session_id=session.id).order_by(Conversation.timestamp).all()
        return jsonify({
            'conversations': [{
                'role': conv.role,
                'content': conv.content,
                'timestamp': conv.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for conv in conversations],
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)