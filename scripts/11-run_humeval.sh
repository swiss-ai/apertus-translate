cd humeval
pearmut add campaigns/*.json

pearmut add campaigns/{German-Italian,German-French,German-English,English-Italian,English-French,English-German,Italian-German,Italian-French,Italian-English,French-German,French-Italian,French-English}.json -o

ngrok http 8003 --url=pearmut.ngrok.dev --traffic-policy-file=/home/vilda/pearmut/misc/policy.yml
pearmut run --port 8003 --url https://pearmut.ngrok.dev