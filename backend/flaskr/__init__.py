import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    def get_catgories():
        categories = Category.query.all()
        formatted_category = {}
        for cat in categories:
            formatted_category[cat.id] = cat.type
        return jsonify({
            'success': True,
            'categories': formatted_category,
            'total_categories': len(categories)
        })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_category = {}
        for cat in categories:
            formatted_category[cat.id] = cat.type

        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(Question.query.all()),
          'categories': formatted_category
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        search = body.get('searchTerm', None)

        try:
            if search:
                selection = Question.query.order_by(
                    Question.id).filter(
                        Question.question.ilike('%{}%'.format(search)))
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all())
                })
            else:
                question = Question(question=new_question, answer=new_answer,
                                    category=new_category,
                                    difficulty=new_difficulty)
                question.insert()
                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })
        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()
        if len(selection) == 0:
            abort(404)

        current_questions = paginate_questions(request, selection)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_question': len(Question.query.all()),
        })

    @app.route('/quizzes', methods=['POST'])
    def get_quiz():
        body = request.get_json()
        end = False
        next_question = None
        pre_questions = body.get('previous_questions', None)
        category = body.get('quiz_category', None)
        if category.get('id', None) != 0:
            selection = Question.query.filter(
                Question.category == category.get('id', None)).all()
        else:
            selection = Question.query.all()
        all_questions = [question.format() for question in selection
                         if question.id not in pre_questions]
        if len(all_questions) != 0:
            next_question = random.choice(all_questions)
            end = False
        else:
            end = True

        return jsonify({
            'success': True,
            'question': next_question,
            'forceEnd': end
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405
    
    @app.errorhandler(500)
    def Internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app
