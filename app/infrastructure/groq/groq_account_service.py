from __future__ import annotations


class GroqAccountError(RuntimeError):
    pass


class GroqAccountService:
    MODEL = "whisper-large-v3"

    def validate_api_key(self, api_key: str) -> None:
        key = str(api_key or "").strip()
        if not key:
            raise GroqAccountError("Configura una API key de Groq para usar el perfil Online.")
        try:
            import groq
            from groq import Groq
        except ImportError as exc:
            raise GroqAccountError("Falta el cliente de Groq. Reinicia AudiTo después de instalar las dependencias.") from exc
        client = Groq(api_key=key, timeout=15.0, max_retries=0)
        try:
            client.models.retrieve(self.MODEL)
        except groq.AuthenticationError as exc:
            raise GroqAccountError("La API key de Groq no es válida o fue rechazada.") from exc
        except groq.APIConnectionError as exc:
            raise GroqAccountError("No se pudo conectar con Groq. Revisa tu conexión a Internet e inténtalo nuevamente.") from exc
        except groq.APIStatusError as exc:
            raise GroqAccountError("Groq no pudo verificar la API key en este momento. Inténtalo nuevamente.") from exc
        except Exception as exc:
            raise GroqAccountError("No se pudo verificar la API key de Groq.") from exc
