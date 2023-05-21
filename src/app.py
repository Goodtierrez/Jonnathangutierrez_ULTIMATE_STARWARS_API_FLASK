"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# En princpio, esta API será usada con autentificacion. Vamos a emular que un usuario ya se ha identificado. 
current_logged_user_id = 1


# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_user():

    all_user = User.query.all()
    result = [element.serialize() for element in all_user]
    return jsonify(result), 200

@app.route('/people', methods=['GET'])
def get_all_people():

    all_people = People.query.all()
    result = [element.serialize() for element in all_people]
    return jsonify(result), 200

@app.route('/people/<int:id>', methods=['GET'])
def get_one_person(id):


    #Aquí cambia la petición y solicitamos sólo una persona por el ID que hemos definido en el Endpoint de arriba (@app.route('/people/<int:id>')
    person = People.query.get(id)
    if person:
        return jsonify(person.serialize()), 200
    else:
        return jsonify({"message": "Person not found"}), 404

@app.route('/people', methods=['POST'])
def post_people():

    # obtener los datos de la petición que están en formato JSON a un tipo de datos entendibles por pyton (a un diccionario). En principio, en esta petición, deberían enviarnos 3 campos: el nombre, la descripción del planeta y la población
    body = request.get_json()
    print(body)

    name = body['name']
    gender = body['gender']
    height = body['height']
    mass = body['mass']
    
     # creamos un nuevo objeto de tipo Planet
    
    people = People(name=name, gender=gender, height=height, mass=mass)


    # añadimos el planeta a la base de datos
    db.session.add(people)
    db.session.commit()

    response_body = {"msg": "Person inserted successfully. ID = " + str(people.id)}
    return jsonify(response_body), 200



# PLANETS

@app.route('/planet', methods=['GET'])
def get_planets():
    allPlanets = Planet.query.all()
    result = [element.serialize() for element in allPlanets]
    return jsonify(result), 200

@app.route('/planet/<int:id>', methods=['GET'])
def get_one_planet(id):


    #Aquí cambia la petición y solicitamos sólo una planeta por el ID que hemos definido en el Endpoint de arriba (@app.route('/planet/<int:id>')
    planet = Planet.query.get(id)
    if planet:
        return jsonify(planet.serialize()), 200
    else:
        return jsonify({"message": "Planet not found"}), 404
    
@app.route('/planet-galaxy', methods=['GET'])
def get_relation_planet_galaxy():
    planets = Planet.query.all()
    response = []
    for planet in planets:
        response.append({
            'planet': planet.name,
            'galaxy_id': planet.galaxy_id,
            'galaxy_name': planet.galaxy.name
        })
    return jsonify(response)    

@app.route('/planet', methods=['POST'])
def post_planet():
    # recuperamos el cuerpo de la petición POST y la guardamos en una variable. 
    body = request.get_json()
    print(body)

    # tenemos que recuperar cada propiedad del objeto body
    # tenemos que crear una nueva instancia del modelo Planet, usando la información contenida en el body
    # tenemos que añadir esta nueva instancia a la base de datos con db.session.add(new_planet) -> db.session.commit()

    name = body['name']
    population = body['population']
    description = body['description']
    galaxy_id = body['galaxy_id']
    planet = Planet(name=name, population=population, description=description, galaxy_id=galaxy_id)
    db.session.add(planet)
    db.session.commit()

    return jsonify({'msg': 'Planet inserted with id ' + str(planet.id)}), 200

@app.route('/favorites', methods=['POST'])
def add_favorite():
    body = request.json
    user_id = body.get('user_id')
    planet_id = body.get('planet_id')
    people_id = body.get('people_id')

    if not user_id or (not planet_id and not people_id):
        return jsonify({'message': 'Invalid request'}), 

    favorite = Favorite(user_id=user_id, planet_id=planet_id, people_id=people_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'message': 'Favorite added successfully'})

@app.route('/favorite/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    favorite = Favorite.query.get(favorite_id)
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'message': f'Favorite {favorite_id} deleted successfully'}), 200
    else:
        return jsonify({'message': f'Favorite {favorite_id} not found'}), 404

@app.route('/user/favorite', methods=['GET'])
def get_user_favorites():
    user_id = request.json.get('user_id')
    if user_id is None:
        return jsonify({'message': 'User ID is required'}), 400

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    result = [favorite.serialize() for favorite in favorites]
    return jsonify(result), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
