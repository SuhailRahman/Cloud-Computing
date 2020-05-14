FROM python
ADD . /todo
WORKDIR /todo
RUN pip install -r requirements.txt
EXPOSE 80
ENV TEAM_NAME=cc_0788_0794_0847
CMD [“python”, “user.py”]