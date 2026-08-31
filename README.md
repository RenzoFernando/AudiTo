<div align="center">

# AudiTo

<img src="assets/icon.png" alt="Logo de AudiTo" width="175">

<br>

<p>
  <a href="https://github.com/RenzoFernando/AudiTo/releases/latest">
    <img src="https://img.shields.io/github/v/tag/RenzoFernando/AudiTo?sort=semver&style=for-the-badge&label=VERSI%C3%93N&color=ff4655" alt="Versión actual">
  </a>
  <a href="https://github.com/RenzoFernando/AudiTo/releases/latest">
    <img src="https://img.shields.io/badge/VER%20RELEASES-20242b?style=for-the-badge" alt="Ver releases">
  </a>
  <a href="https://renzofernando.github.io/AudiTo/">
    <img src="https://img.shields.io/badge/PÁGINA%20OFICIAL-ff4655?style=for-the-badge" alt="Abrir página oficial">
  </a>
</p>

<strong>Convierte audio en texto directamente en tu computador.</strong>

<br><br>

AudiTo transforma archivos de audio y grabaciones de micrófono en transcripciones TXT mediante modelos Whisper, con perfiles locales y una opción online.

</div>

---

## Descripción

**AudiTo** es una aplicación de escritorio enfocada en convertir audio a texto de forma sencilla, con distintos perfiles de transcripción para adaptarse a cada equipo y necesidad.

Puedes seleccionar un archivo, arrastrarlo sobre la aplicación o grabar desde tu micrófono. AudiTo procesa un audio a la vez y genera un `.txt` organizado, con marcas de tiempo opcionales.

## Funciones principales

- **Archivos y arrastrar y soltar:** carga audio desde la interfaz o directamente mediante drag and drop.
- **Grabación desde micrófono:** guarda la grabación y puede comenzar a transcribir progresivamente mientras continúas hablando.
- **Cuatro perfiles:** Rápida, Equilibrada, Máxima y Online.
- **Tres modos de idioma:** Español, Inglés y Automático.
- **Marcas de tiempo opcionales:** activa o desactiva las referencias temporales del TXT.
- **Carpeta de salida configurable:** decide dónde guardar transcripciones y grabaciones.
- **Acceso rápido al resultado:** abre la última transcripción o su carpeta desde AudiTo.
- **Interfaz en español e inglés:** el idioma visual es independiente del idioma que vas a transcribir.
- **Procesamiento flexible:** Rápida, Equilibrada y Máxima funcionan localmente; Online está disponible como alternativa mediante GroqCloud.
- **Descargas de modelos controlables:** la primera descarga muestra progreso y puede cancelarse sin perder la aplicación.

## Perfiles de transcripción

| Perfil | Modelo | Enfoque |
| --- | --- | --- |
| **Rápida** | Whisper Small | Menor consumo y mayor velocidad |
| **Equilibrada** | Whisper Medium | Balance entre precisión y velocidad |
| **Máxima** | Whisper Large v3 | Mayor precisión y mayor consumo de recursos |
| **Online** | Whisper Large v3 · GroqCloud | Procesamiento remoto sin cargar el modelo en el equipo |

Por defecto, AudiTo inicia con **Español** y el perfil **Equilibrada**.

## Uso

1. Selecciona, arrastra o graba un audio.
2. Elige el idioma, el perfil de precisión y la carpeta de salida.
3. Si elegiste un perfil local y el modelo todavía no está disponible, pulsa el botón principal para descargarlo. Si usas Online, configura tu API key de Groq.
4. Pulsa **TRANSCRIBIR**.
5. Abre el TXT generado o la carpeta de salida directamente desde la aplicación.

Formatos compatibles:

`MP3` · `M4A` · `WAV` · `AAC` · `FLAC` · `OGG` · `OPUS` · `WMA` · `AIFF` · `AMR`

La primera vez que uses un perfil local, AudiTo necesita conexión a Internet para obtener su modelo. Los modelos se conservan localmente para usos posteriores. El perfil Online requiere conexión a Internet y una API key propia de Groq.

## Descarga

AudiTo se publica mediante dos artefactos oficiales con nombres estables:

- **Instalable recomendado:** [`AudiTo-Setup.exe`](https://github.com/RenzoFernando/AudiTo/releases/latest/download/AudiTo-Setup.exe)
- **Portable:** [`AudiTo-Portable.exe`](https://github.com/RenzoFernando/AudiTo/releases/latest/download/AudiTo-Portable.exe)

Canales oficiales:

- **Página oficial:** https://renzofernando.github.io/AudiTo/
- **Última release:** https://github.com/RenzoFernando/AudiTo/releases/latest
- **Repositorio:** https://github.com/RenzoFernando/AudiTo
- **Creador:** https://github.com/RenzoFernando

La versión de los ejecutables se obtiene desde `app/app_meta.py`, y la página oficial consulta la última GitHub Release para mostrar la versión publicada y enlazar sus artefactos.

## Privacidad y procesamiento

Los perfiles **Rápida**, **Equilibrada** y **Máxima** utilizan **Faster-Whisper** y procesan el audio directamente en el computador. El perfil **Online** envía el audio a GroqCloud únicamente cuando se selecciona esa opción.

Los modelos descargados se almacenan en los datos locales de AudiTo y pueden reutilizarse sin volver a descargarlos. La API key del perfil Online se configura desde la propia aplicación.

## Licencia

AudiTo se distribuye bajo la **MIT License**.

Copyright © 2026 · Renzo Fernando Mosquera Daza
