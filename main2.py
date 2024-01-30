from flask import Flask,make_response,jsonify
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import os
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
# specify that we're using restful api
api = Api(app)

#config DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
db = SQLAlchemy(app)
# DB: Users
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    secret = db.Column(db.Text, nullable = False, unique = True)
    active = db.Column(db.Boolean, default = True)
    points = db.Column(db.Integer, default = 0, nullable = False)
    username = db.Column(db.Text, nullable = False)
    can_stream = db.Column(db.Boolean, default = False)
    
    donationrecords = db.relationship('DonationRecords', backref = 'users')
    transactions= db.relationship('Transactions', backref = 'users')
    streams = db.relationship('Streams', backref = 'users')

    def __repr__(self):
        return f"User(id = {self.id}, secret = {self.secret}, active = {self.active}, points = {self.points}, username = {self.username}, can_stream = {self.can_stream}) created"

# DB: Donations
class DonationRecords(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    stream_id = db.Column(db.Integer, db.ForeignKey("streams.id"), nullable = False)
    amount = db.Column(db.Integer, nullable = False)
    remain = db.Column(db.Integer, nullable = False)
    create_at = db.Column(db.Float, nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    

    def __repr__(self):
        return f"DonationRecords(donation_id = {self.id}, stream_id = {self.stream_id}, amount = {self.amount}, remain = {self.remain}, create_at = {self.create_at}, donor_id = {self.donor_id})"
    # def __dict__(self):



# DB: Transactions
class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    success = db.Column(db.Boolean)
    amount = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    issue_at = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)

    def __repr__(self):
        return f"Transaction(id = {self.id}, success = {self.success}, amount = {self.amount}, remain = {self.cost}, create_at = {self.issue_at}, user_id = {self.user_id})"

# DB: Streams
class Streams(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    create_at = db.Column(db.Float, nullable=False)
    donationrecords = db.relationship('DonationRecords', backref = 'streams')

    def __repr__(self):
        return f"Streams(id = {self.id}, creator_id = {self.creator_id}, create_at = {self.create_at})"

# Initialize
#db.create_all()

# serialize
resource_fields_donation = {
    'donation_id' : fields.Integer,
    'stream_id' : fields.Integer,
    'amount': fields.Integer,
    'remain': fields.Integer,
    'create_at': fields.Float,
    'donor_id': fields.Integer,
    'username': fields.String
}
resource_fields_transaction= {
    'transaction_id' : fields.Integer,
    'success' : fields.Boolean,
    'amount': fields.Integer,
    'cost': fields.Float,
    'issue_at': fields.Float
}

# def donation_response(dict):
#     return jsonify({
#         'donation_id' : dict.get('id'),
#         'stream_id' : dict.get('stream_id'),
#         'amount': dict.get('amount'),
#         'remain': dict.get('remain'),
#         'create_at': dict.get(',
#         'donor_id': fields.Integer,
#         'username': fields.String
#     })


# Restful API
# 1. Donation API
class Donation(Resource):
    # get donation info
    def get(self, stream_id):
        try:
            search = db.session.query(DonationRecords,Users).outerjoin(Users, (Users.id == DonationRecords.donor_id)).filter(DonationRecords.stream_id==stream_id).all()
            
            result = []
            for row in search:
                d={}
                i=0
                for r in row:
                    d.update(r.__dict__)
                d.update({'donation_id':d.get('id')})

                result.append(d)
                del d['_sa_instance_state']
            if len(result) == 0:
                logging.error('no results')
                abort(400)
            result = jsonify(result)
            result = make_response( (result), 200)

        except Exception as e:
            logging.error('Exception ERROR => ' + str(e))
            abort(400)
        
        else:
            # return 1
            return result
        
        # An Object, must serialize it at line 66
    
    # post a new donation 
    # needs to update donation records, and user points
    @marshal_with(resource_fields_donation)
    def post(self, stream_id):
        # automatically parse the data sent(define the needed parameters)
        # warning!!! nested json requires special parsing techniques
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("signature", type=str, help="signature require", required = True)
            parser.add_argument("payload", type=dict, help="payload require", required = True)
            args = parser.parse_args()
            # extra data info parser
            extra_parser = reqparse.RequestParser()
            extra_parser.add_argument("donor_id", type = int, help = "donor_id require", required = True)
            extra_parser.add_argument("amount", type = int, help = "amount require", required = True)
            extra_parser.add_argument("datetime", type = float, help = "datetime require", required = True)

            # get user info
            date=args["payload"]["datetime"]
            amount=args["payload"]["amount"]
            donor_id=args["payload"]["donor_id"]
            
            user = Users.query.filter_by(id=donor_id).first()
            if user == []:
                logging.error('no user')
                abort(400)

            if user.points < amount:
                logging.error('no enough points')
                abort(400)
                # ///////////////////////
            if datetime.now().timestamp()-date < 0.2 or date - datetime.now().timestamp() > 0:
                logging.error('time out')
                abort(400)
            remain = user.points - amount
            user.points -= amount
            
            result = DonationRecords(stream_id=stream_id, 
                                    amount=amount,
                                    remain=remain, 
                                    donor_id=donor_id,
                                    # /////////////////////////////////////////////////////////
                                    create_at = datetime.now().timestamp()
                                    )
            db.session.add(result)
            db.session.commit()
            
            result = {  'stream_id' : stream_id, 
                        'amount' : amount, 
                        'remain' : remain, 
                        'donor_id' : donor_id,
                        # /////////////////////////////////////////////////////////
                        'create_at' : datetime.now().timestamp(),
                        'username' : user.username,
                        'donation_id':result.id
                        }
        except Exception as e:
            logging.error('Exception ERROR => ' + str(e))
            abort(400)
        
        return result, 200


# 2. Transaction API
class Transaction(Resource):
    @marshal_with(resource_fields_transaction)
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("signature", type=str, help="signature require", required=True)
            parser.add_argument("payload", type=dict, help="payload require", required=True)
            args = parser.parse_args()

            # extra data info parser
            extra_parser = reqparse.RequestParser()
            extra_parser.add_argument("user_id", type=int, help="user_id require", required=True)
            extra_parser.add_argument("datetime", type=float, help="datetime require", required=True)
            datetime = args["payload"]["datetime"]

            if datetime.now().timestamp()-datetime < 0.2 or datetime - datetime.now().timestamp() > 0:
                logging.error('time out')
                abort(400)

            
            result = Transactions.query.filter_by(user_id=args["payload"]["user_id"]).all()
            # issue_at
        except Exception as e:
            logging.error('Exception ERROR => ' + str(e))
            abort(400)

        return result, 200
    
    @marshal_with(resource_fields_transaction)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("signature", type=str, help="signature require", required=True)
        parser.add_argument("payload", type=dict, help="payload require", required=True)
        args = parser.parse_args()

        # extra data info parser
        extra_parser = reqparse.RequestParser()
        extra_parser.add_argument("user_id", type=int, help="user_id require", required=True)
        extra_parser.add_argument("amount", type=int, help="amount require", required=True)
        extra_parser.add_argument("cost", type=float, help="cost require", required=True)
        extra_parser.add_argument("issue_at", type=float, help="issue_at require", required=True)
        #set success true

        amount = args["payload"]["amount"]
        user_id = args["payload"]["user_id"]
        cost = args["payload"]["cost"]
        issue_at = args["payload"]["issue_at"]
        
        if datetime.now().timestamp()-issue_at < 0.2 or issue_at - datetime.now().timestamp() > 0:
                logging.error('time out')
                abort(400)

        try:
            user = Users.query.filter_by(id=user_id).first()
            user.points += amount
            result = Transactions(amount=amount,
                                cost=cost, 
                                user_id=user_id,
                                issue_at=datetime.now().timestamp())
            db.session.add(result)
            db.session.commit()
        except Exception as e:
            logging.error('Exception ERROR => ' + str(e))
            abort(400)
        
        return result, 200
    

# add api
api.add_resource(Donation, "/donation/<int:stream_id>")
api.add_resource(Transaction,"/transaction")



if __name__ == "__main__":
    # result = DonationRecords(
    #                             stream_id=1,
    #                             amount=300, 
    #                             remain=9999, 
    #                             donor_id=1,
    #                             create_at = datetime.now().timestamp()
    #                                 )
    # with app.app_context():
    #     db.session.add(result)
    #     db.session.commit()
    app.run(host="127.0.0.1", port=5555,debug=True)
    # get PORT information form the environment variable
    # app.run(host="0.0.0.0", port=os.environ.get('PORT'),debug=True)