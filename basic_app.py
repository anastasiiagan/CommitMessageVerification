from flask import Flask
from flask_restful import Api, Resource, reqparse
import requests
from collections import namedtuple

Book = namedtuple('Book', 'title,author')

app = Flask(__name__)
api = Api(app)


class Library(Resource):

    def __init__(self):
        libraryList = []
        book = Book('Harry Potter', 'Rowling')
        libraryList.append(book)
        book = Book('Martin Eden', 'Jack London')
        libraryList.append(book)
        book = Book('Alice in Wonderland', 'Lewis Carroll')
        libraryList.append(book)


    def list(self):
        for book in self.libraryList:
            print(f'Title: "{book.title}", author: "{book.author}"')
        return "OK", 200


    def add(self,title,author):
        book = Book(title, author)
        self.libraryList.append(book)
        return "OK", 200


    def delete(self,title):
        for book in self.libraryList.items():
            if book.title == title:
                del self.libraryList[book]
            else:
                print("The book isn't in library")
                         
        return "OK", 200

        
library = Library()

app.add_url_rule('/library-app/list', view_func=library.list, methods=['GET'])
app.add_url_rule('/library-app/add/<string:title>/<string:author>', view_func=library.add, methods=['POST'])
app.add_url_rule('/library-app/delete/<string:title>', view_func=library.delete, methods=["DELETE"])


if __name__ == "__main__":
    app.run(debug=True, port=5005, host='0.0.0.0')