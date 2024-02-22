FROM python:3.9-alpine
ENV DEVELOPMENT 0
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY Database.db ./data/
COPY main.py ./
CMD [ "python", "main.py" ]
EXPOSE 8070