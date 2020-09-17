# near warchest bot

# Installa i pacchetti necessari
```bash
sudo apt-get install python3-setuptools
sudo apt-get install python3-dev
```
Installa le librerie in modalità sviluppatore:
```bash
python3 setup.py develop
```

Modifica linea 10 di `warchest.service` con il percorso assoluto al file `warchest.py`
# Account e informazioni dello staking pool
Modifica prime linee di `warchest.py` con le informazioni dello staking pool e i dati del proprietario.

# Avvia il servizio warchest e controlla che sia in esecuzione
Aggiungi il prefisso ```sudo ``` se necessario
```bash
cp warchest.service /etc/systemd/system/warchest.service
systemctl start warchest.service
systemctl status warchest.service
```
# Monitoraggio del bot warchest
```bash
systemctl status warchest.service
journalctl -u warchest.service --since today
```
