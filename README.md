<div align="center">

# AudiTo

<img src="assets/icon.png" alt="Logo de AudiTo" width="175">

<br>

<p>
  <a href="https://github.com/RenzoFernando/AudiTo/releases/latest">
    <img src="https://img.shields.io/github/v/release/RenzoFernando/AudiTo?style=for-the-badge&label=VERSI%C3%93N&color=ff4655" alt="Versión actual">
  </a>
  <a href="https://github.com/RenzoFernando/AudiTo/releases/latest">
    <img src="https://img.shields.io/badge/VER%20RELEASES-20242b?style=for-the-badge" alt="Ver releases">
  </a>
  <a href="https://renzofernando.github.io/AudiTo/">
    <img src="https://img.shields.io/badge/P%C3%81GINA%20OFICIAL-ff4655?style=for-the-badge" alt="Abrir página oficial">
  </a>
</p>

<strong>Transcribe archivos de audio y grabaciones de micrófono a texto con Whisper.</strong>

</div>

---

## Descripción

**AudiTo** es una aplicación de escritorio para Windows que convierte audio en transcripciones TXT. Permite trabajar con archivos existentes o grabar desde el micrófono, elegir el idioma de transcripción y usar distintos perfiles según el equilibrio deseado entre velocidad, precisión y consumo de recursos.

Los perfiles locales procesan el audio en el computador mediante Faster-Whisper. También existe un perfil Online que utiliza GroqCloud cuando se prefiere procesamiento remoto.

## Características

- **Archivos y arrastrar y soltar:** selecciona un audio desde la interfaz o suéltalo directamente sobre la aplicación.
- **Grabación desde micrófono:** guarda la grabación y puede iniciar la transcripción de forma progresiva mientras continúas hablando.
- **Cuatro perfiles de transcripción:** Rápida, Equilibrada, Máxima y Online.
- **Tres modos de idioma:** Español, Inglés y Automático.
- **Marcas de tiempo opcionales:** permite incluir o excluir referencias temporales en el TXT.
- **Carpeta de salida configurable:** define dónde guardar transcripciones y grabaciones.
- **Acceso rápido al resultado:** abre la última transcripción o su carpeta desde la aplicación.
- **Interfaz en español e inglés:** el idioma de la interfaz es independiente del idioma del audio.
- **Descarga controlada de modelos:** la primera descarga muestra progreso y puede cancelarse.

## Perfiles de transcripción

| Perfil | Modelo | Procesamiento | Enfoque |
| --- | --- | --- | --- |
| **Rápida** | Whisper Small | Local | Menor consumo y mayor velocidad |
| **Equilibrada** | Whisper Medium | Local | Balance entre precisión y velocidad |
| **Máxima** | Whisper Large v3 | Local | Mayor precisión y mayor consumo de recursos |
| **Online** | Whisper Large v3 · GroqCloud | Remoto | Evita cargar el modelo en el equipo |

Por defecto, AudiTo inicia con **Español** y el perfil **Equilibrada**.

## Uso

1. Selecciona o arrastra un archivo de audio, o inicia una grabación desde el micrófono.
2. Elige el idioma, el perfil de transcripción y la carpeta de salida.
3. Si utilizas un perfil local por primera vez, descarga el modelo cuando la aplicación lo solicite. Para el perfil Online, configura tu API key de Groq.
4. Pulsa **TRANSCRIBIR**.
5. Abre el TXT generado o su carpeta directamente desde AudiTo.

Formatos de audio compatibles:

`MP3` · `M4A` · `WAV` · `AAC` · `FLAC` · `OGG` · `OPUS` · `WMA` · `AIFF` · `AMR`

## Descarga

AudiTo se distribuye mediante dos artefactos oficiales para Windows:

- **Instalable recomendado:** [`AudiTo-Setup.exe`](https://github.com/RenzoFernando/AudiTo/releases/latest/download/AudiTo-Setup.exe)
- **Portable:** [`AudiTo-Portable.exe`](https://github.com/RenzoFernando/AudiTo/releases/latest/download/AudiTo-Portable.exe)

El instalable integra la aplicación en Windows y es la opción indicada para uso habitual. El portable puede ejecutarse directamente sin realizar una instalación.

Canales oficiales:

- **Página oficial:** https://renzofernando.github.io/AudiTo/
- **Última release:** https://github.com/RenzoFernando/AudiTo/releases/latest
- **Código fuente:** https://github.com/RenzoFernando/AudiTo

## Funcionamiento y privacidad

Los perfiles **Rápida**, **Equilibrada** y **Máxima** utilizan Faster-Whisper y procesan el audio localmente. La primera vez que se utiliza uno de estos perfiles, AudiTo necesita conexión a Internet para descargar el modelo correspondiente; después, el modelo se conserva en los datos locales de la aplicación para usos posteriores.

El perfil **Online** requiere conexión a Internet y una API key propia de Groq. Cuando se selecciona este perfil, el audio se procesa mediante GroqCloud.

## Desarrollo

### Requisitos

- Windows.
- Python 3.11 o 3.12.
- Git.
- Conexión a Internet para instalar dependencias.
- Inno Setup 6 para generar el instalador; `buildinstaller.bat` intenta localizarlo y puede instalarlo mediante `winget` si no está disponible.

### Preparar el entorno

```batch
git clone https://github.com/RenzoFernando/AudiTo.git
cd AudiTo
setupAmp.bat
```

### Ejecutar desde código

```batch
.\.venv\Scripts\python.exe main.py
```

### Generar artefactos

```batch
buildportable.bat
buildinstaller.bat
```

Los artefactos finales se generan en `downloads/`.

## Autor y licencia

[Renzo Fernando Mosquera Daza](https://github.com/RenzoFernando)

Este proyecto se distribuye bajo la **Licencia MIT**. Consulta [`LICENSE`](LICENSE).
