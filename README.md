# Shower Studies

Este repositorio contiene los estudios relacionados con el desarrollo del algoritmo de detección de showers para el Muon L1T de CMS.

Los estudios se basan en las primitivas de shower generadas mediante el emulador de CMSSW ([DTTrigPhase2ShowerProd.cc](https://github.com/cms-sw/cmssw/blob/master/L1Trigger/DTTriggerPhase2/plugins/DTTrigPhase2ShowerProd.cc)). Usando este plugin, se crean DTNTuples con el código disponible en este repositorio: [DTNtuples](https://github.com/DanielEstrada971102/DTNtuples/tree/shower_ntuples).

Las NTuples se generaron a partir de la muestra de Monte Carlo **6 TeV Zprime candidate to have a source of showers**: ```/ZprimeToMuMu_M-6000_TuneCP5_14TeV-pythia8/Phase2HLTTDRWinter20DIGI-PU200_110X_mcRun4_realistic_v3-v2/GEN-SIM-DIGI-RAW``` (Nota: esta muestra aparece como INVALID en DAS).

Los subdirectorios contienen estudios específicos sobre los datos mencionados:

1. `efficiencies`: Aquí se analiza la eficiencia del algoritmo de showers mediante comparaciones basadas en los simhits de cada evento. Se construyen showers "reales" según si los hits de simulación son producidos por electrones o no. Con esta definición de verdad, se estiman las fracciones de aciertos y fallos del algoritmo.

2. `rates`: En este apartado se estima el rate de las primitivas de showers generadas.

3. `agreement`: Un aspecto importante es analizar el acuerdo entre las primitivas de shower generadas por el emulador y las que serán producidas por el algoritmo en firmware. Usando la información a nivel de DIGI (hits), se utiliza `firmware-emulator` para reproducir la salida esperada del firmware, que luego se compara con las primitivas obtenidas del plugin de CMSSW.

4. `filter-studies`: Antes de que las primitivas de DT se envíen a los track finders, pueden pasar por una etapa intermedia conocida como "Barrel Filter". En esta etapa, se aplican algoritmos más refinados para cruzar la información de las primitivas de DT, shower y RPC. Este directorio contiene los estudios realizados para evaluar qué procesos de filtrado y selección son relevantes para incluir en esta etapa.

Cada directorio contiene más detalles de las cosas especificas que allí se hacen. Y los analasis acá presentados asumen que se esta trabajando con los frameworks [DTPatternRecognition](https://github.com/DanielEstrada971102/DTPatternRecognition) y [mplDTs](https://github.com/DanielEstrada971102/mplDTs). Las versiones especificas se dejan en el archivo de `requeriments.txt`.