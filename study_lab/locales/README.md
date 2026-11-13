# Euskara eta gaztelania

Euskara (`eu`) da lehenetsitako hizkuntza. Goiko barrako hautagailuak eta saioa hasteko orriak `Español (España)` (`es-ES`) aukeratzeko aukera ematen dute. Hautua nabigatzailean gordetzen da, ikasketa-aurrerapenetik bereizita. Hizkuntza aldatzean zirriborroa gordetzen da; kontuko bertsioan sinkronizazioa amaitu arte itxaroten da.

- `learning.eu.json`: 20 ikasgai eta 106 galdera. Jatorrizko gaztelaniazko edukia `../learning-content.json` fitxategian mantentzen da.
- `cases.eu.json`: ariketen, ibilbideen eta giden testuen itzulpenak; jatorrizkoak `../app.js` fitxategian daude.
- `ui.eu.json`: interfazearen testuak eta `{0}` formatuko parametroak dituzten esaldiak.
- `../i18n.js`: hizkuntza-hautua eta interfazearen testu dinamikoen itzulpena. Ez ditu erabiltzailearen erantzunak, kodea, identifikatzaileak edo jatorrizko apunteak aldatzen.

Itzulpenek galderen ordena, identifikatzaileak, bertsioak eta zuzenketarako indizeak mantentzen dituzte. Termino-galderek bi hizkuntzetako erantzunak onartzen dituzte; hizkuntza aldatzeak ez du aurreko erantzunaren zuzenketa aldatzen.

Eraiki: `python study_lab/build.py`. Eraikuntzak `study_lab/index.html` eta `distribution/login.html` sortzen ditu. Saioa hasteko iturria `distribution/login-shell.html` da. Fitxategi sortuek bi hizkuntzak barne hartzen dituzte; ez dute itzulpen-zerbitzurik behar.

Egiaztatu: `node study_lab/test_i18n.cjs` eta `python study_lab/test_i18n_browser.py`. Bigarren probak Chromium eta ChromeDriver erabiltzen ditu, behin-behineko profilekin eta datu-basearekin.
