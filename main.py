from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil import parser as datetime_parser

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
    points = db.Column(db.Integer, nullable = False)
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
    stream_id = db.Column(db.Integer, nullable = False)
    amount = db.Column(db.Integer, nullable = False)
    remain = db.Column(db.Integer, nullable = False)
    create_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    

    def __repr__(self):
        return f"DonationRecords(donation_id = {self.id}, stream_id = {self.stream_id}, amount = {self.amount}, remain = {self.remain}, create_at = {self.create_at}, donor_id = {self.user_id})"

# DB: Transactions
class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    success = db.Column(db.Boolean, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    issue_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)

    def __repr__(self):
        return f"Transaction(id = {self.id}, stream_id = {self.success}, amount = {self.amount}, remain = {self.cost}, create_at = {self.issue_at}, user_id = {self.user_id})"

# DB: Streams
class Streams(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    create_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"Streams(id = {self.id}, creator_id = {self.creator_id}, create_at = {self.create_at})"

# Initialize
db.create_all()

# serialize
resource_fields_donation = {
    'id' : fields.Integer,
    'stream_id' : fields.Integer,
    'amount': fields.Integer,
    'remain': fields.Integer,
    'create_at': fields.DateTime(dt_format='iso8601'),
    'user_id': fields.Integer,
}
resource_fields_transaction= {
    'id' : fields.Integer,
    'success' : fields.Boolean,
    'amount': fields.Integer,
    'cost': fields.Float,
    'issue_at': fields.DateTime(dt_format='iso8601'),
    'user_id': fields.Integer,
}

# Restful API
# 1. Donation API
class Donation(Resource):
    # get donation info
    @marshal_with(resource_fields_donation)
    def get(self, stream_id):
        result = DonationRecords.query.filter_by(stream_id=stream_id).all()
        # An Object, must serialize it at line 66
        return result, 200
    
    # post a new donation 
    # needs to update donation records, and user points
    @marshal_with(resource_fields_donation)
    def post(self, stream_id):
        # automatically parse the data sent(define the needed parameters)
        # warning!!! nested json requires special parsing techniques
        parser = reqparse.RequestParser()
        parser.add_argument("signature", type=str, help="signature require", required = True)
        parser.add_argument("payload", type=dict, help="payload require", required = True)
        args = parser.parse_args()
        # extra data info parser
        extra_parser = reqparse.RequestParser()
        extra_parser.add_argument("user_id", type = int, help = "user_id require", required = True)
        extra_parser.add_argument("amount", type = int, help = "amount require", required = True)
        # time is not able to take in datetime type from json
        #extra_parser.add_argument("datetime", type = datetime, help = "datetime require", required = True)

        # create a new Donation istance
        # check signature
        # remain -> get from user model
        # amount -> original - amount
        donate = DonationRecords(stream_id=stream_id, 
                                 amount=args["payload"]["amount"], 
                                 remain=100, 
                                 user_id=args['payload']['user_id']
                                )
        db.session.add(donate)
        db.session.commit()
        return donate, 200


# 2. Transaction API
class Transaction(Resource):
    @marshal_with(resource_fields_transaction)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("signature", type=str, help="signature require", required=True)
        parser.add_argument("payload", type=dict, help="payload require", required=True)
        args = parser.parse_args()

        # extra data info parser
        extra_parser = reqparse.RequestParser()
        extra_parser.add_argument("user_id", type=int, help="user_id require", required=True)
        #extra_parser.add_argument("datetime", type=str, help="datetime require", required=True)
        #extra_args = extra_parser.parse_args()

        # if 'user_id' not in extra_args or extra_args['user_id'] is None:
        #     # Abort the request with a custom error message
        #     abort(400, message={"user_id": "user_id is required"})

        #datetime_str = extra_args['datetime']
        #datetime_obj = datetime_parser.parse(datetime_str)
        #after_format = datetime_parser.parse(args['payload']['datetime'])
        result = Transactions.query.filter_by(user_id=args['payload']['user_id']).all()
        result = Transactions.query.filter_by(issue_at = datetime(2024, 1, 14, 13, 45, 52, 293900)).all()
        #result = Transactions.query.filter_by(issue_at=after_format).all()
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
        extra_parser.add_argument("issue_at", type=int, help="issue_at require")
        #set success true
        result = Transactions(success = True, amount=args['payload']['amount'],cost=args['payload']['cost'], user_id=args["payload"]['user_id'])
        db.session.add(result)
        db.session.commit()
        return result, 200
# add api
api.add_resource(Donation, "/donation/<int:stream_id>")
api.add_resource(Transaction,"/transaction")



if __name__ == "__main__":
    app.run(debug=True)
