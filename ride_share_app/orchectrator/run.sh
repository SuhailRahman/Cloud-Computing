sudo docker stop $(sudo docker ps -a -q)
sudo docker rm $(sudo docker ps -a -q)
cd slave
rm -rf tmp.txt db.sqlite3
rm -rf new*
cd ..
sudo docker-compose up --build
