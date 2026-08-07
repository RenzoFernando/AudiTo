<div align="center">

# AudiTo

<img src="assets/icon.png" alt="Logo de AudiTo" width="175">

<br>

<p>
  <img src="https://img.shields.io/badge/VERSIÓN-3.0.2-ff4655?style=for-the-badge" alt="Versión actual">

  <img src="https://img.shields.io/badge/RELEASES-PRÓXIMAMENTE-6B7280?style=for-the-badge" alt="Releases próximamente">

  <img src="https://img.shields.io/badge/DESCARGA-PRÓXIMAMENTE-6B7280?style=for-the-badge" alt="Descarga próximamente">
</p>

<strong>
Convierte audio en texto directamente en tu computador.
</strong>

<br><br>

AudiTo transforma archivos de audio y grabaciones de micrófono en transcripciones TXT con marcas de tiempo, utilizando Whisper de forma local.

</div>

---

## Descripción

**AudiTo** es una aplicación de escritorio para Windows enfocada en convertir audio a texto de forma sencilla y local.

Puedes cargar un archivo existente, arrastrarlo directamente a la aplicación o grabar desde tu micrófono. AudiTo procesa el audio en tu computador y genera un archivo `.txt` organizado con marcas de tiempo automáticas.

La aplicación está pensada para transcribir clases, reuniones, entrevistas, notas de voz, grabaciones y otros contenidos de audio sin depender de un servicio de transcripción por minuto.

## Funciones principales

- **Cargar archivos de audio:** selecciona un archivo desde Windows o arrástralo directamente sobre la aplicación.
- **Grabar desde el micrófono:** crea una grabación en formato WAV y permite transcribirla desde la misma interfaz.
- **Transcripción progresiva durante la grabación:** en grabaciones suficientemente largas, AudiTo comienza a procesar el audio mientras continúas hablando.
- **Marcas de tiempo automáticas:** cada segmento del TXT conserva una referencia temporal para ubicar fácilmente el contenido dentro del audio.
- **Tres perfiles de precisión:** elige entre Rápida, Equilibrada y Máxima según los recursos de tu computador y el nivel de precisión que necesites.
- **Tres modos de idioma:** Español, Inglés o Automático.
- **Carpeta de salida configurable:** decide dónde guardar las transcripciones y grabaciones.
- **Acceso rápido al resultado:** abre la última transcripción o la carpeta de salida directamente desde AudiTo.
- **Interfaz en español e inglés:** el idioma de la aplicación puede cambiarse independientemente del idioma que quieras transcribir.
- **Procesamiento local:** el audio se procesa en tu propio computador.

## Perfiles de transcripción

AudiTo ofrece tres opciones para adaptar la transcripción al equipo y al tipo de trabajo:

### Rápida

Prioriza la velocidad y utiliza menos recursos. Es útil cuando necesitas obtener el texto lo antes posible o estás trabajando en un computador con recursos más limitados.

### Equilibrada

Es la opción predeterminada. Busca un balance entre precisión, velocidad y consumo de recursos.

### Máxima

Prioriza la precisión utilizando un modelo de mayor tamaño. Requiere más recursos y puede tardar más tiempo en completar la transcripción.

## Idiomas

Para cada transcripción puedes elegir:

- **Español:** fuerza la interpretación del audio como español.
- **Inglés:** fuerza la interpretación del audio como inglés.
- **Automático:** AudiTo permite que el modelo detecte el idioma del audio.

Por defecto, AudiTo inicia con **Español** y el perfil **Equilibrada**.

> El idioma de transcripción es independiente del idioma de la interfaz. La aplicación puede mostrarse en español o inglés sin cambiar el idioma seleccionado para el audio.

## Manual de uso

### 1. Carga o graba un audio

Puedes iniciar de tres formas:

- Arrastrando un archivo de audio sobre AudiTo.
- Pulsando **Seleccionar audio**.
- Pulsando **Grabar** para utilizar el micrófono predeterminado de Windows.

AudiTo procesa un archivo a la vez.

Formatos compatibles:

`MP3` · `M4A` · `WAV` · `AAC` · `FLAC` · `OGG` · `OPUS` · `WMA` · `AIFF` · `AMR`

### 2. Configura la transcripción

Selecciona:

- El **idioma** del audio.
- El nivel de **precisión**.
- La carpeta donde quieres **guardar** el resultado.

La configuración inicial utiliza:

- **Idioma:** Español
- **Precisión:** Equilibrada
- **Carpeta:** `Documentos/Transcripciones`

### 3. Transcribe

Pulsa **TRANSCRIBIR**.

AudiTo prepara el audio, carga el modelo seleccionado y muestra el progreso del proceso. Cuando es posible, también muestra una estimación del tiempo restante.

La primera vez que utilices un perfil, AudiTo puede necesitar conexión a Internet para descargar su modelo de transcripción.

### 4. Obtén el resultado

Al finalizar se genera un archivo `.txt` con información básica de la transcripción y segmentos acompañados de marcas de tiempo.

Ejemplo:

```text
[00:03:18]

Texto correspondiente a este momento del audio.
```

Desde la aplicación puedes utilizar:

- **ABRIR TRANSCRIPCIÓN** para abrir directamente el TXT generado.
- **ABRIR CARPETA** para ir a la ubicación donde se guardaron los archivos.

Si cancelas una transcripción en curso, AudiTo conserva el archivo parcial disponible hasta ese momento.

## Grabación desde el micrófono

Al utilizar **Grabar**, AudiTo:

1. Usa el micrófono predeterminado de Windows.
2. Guarda automáticamente la grabación en formato WAV.
3. Comienza la transcripción progresiva aproximadamente después de los primeros 30 segundos cuando la grabación continúa.
4. Sigue procesando nuevos fragmentos mientras grabas.
5. Al detener la grabación, procesa el audio restante y finaliza el TXT.

Las grabaciones se conservan dentro de una carpeta `Grabaciones` en la ubicación de salida seleccionada.

## Privacidad y funcionamiento local

AudiTo utiliza **Faster-Whisper** para realizar la transcripción localmente.

El audio no necesita enviarse a una API de transcripción. Una vez descargado el modelo seleccionado, las transcripciones pueden realizarse sin conexión a Internet.

Esto permite trabajar con archivos y grabaciones directamente desde el computador y sin un costo por minuto de transcripción.

## Estado del proyecto

AudiTo se encuentra actualmente en desarrollo.

- **Versión actual:** `3.0.2`
- **Repositorio:** https://github.com/RenzoFernando/AudiTo
- **Releases públicas:** Próximamente
- **Descarga para Windows:** Próximamente
