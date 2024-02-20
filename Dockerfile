FROM python:3.9-alpine

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY Database.db ./data/
# COPY app.py ./
COPY main.py ./
ENV FLASK_ENV=development
CMD [ "python", "main.py" ]
# CMD flask run --host=0.0.0.0
EXPOSE 8070