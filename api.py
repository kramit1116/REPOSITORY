from flask_restful import Resource,Api
from models import Category
from app import app

api = Api(app)
class CategoryRe(Resource):
    def get(self):
        categories = Category.query.all()
        return   {'categories' : [ {'id':category.id, 'category':category.name} for category in categories]}   

api.add_resource(CategoryRe,'/api/categories')