import requests
import json
from typing import Optional, Dict, Any, Union

class AgentPay:
    """
    El Conector Universal de AgentPay.
    Se adapta automáticamente a LangChain, OpenAI, AutoGen y CrewAI.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://agentpay-core.onrender.com"):
        self.api_key = api_key
        # Aseguramos que la URL no tenga barra al final
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    # --- NÚCLEO: La función que mueve el dinero ---
    def pay(self, vendor: str, amount: float, description: str) -> str:
        """Ejecuta el pago contra tu Banco en la Nube (Render)."""
        try:
            resp = requests.post(
                f"{self.base_url}/v1/pay",
                json={"vendor": vendor, "amount": float(amount), "description": description},
                headers=self.headers,
                timeout=20
            )
            
            # Manejo de errores de red o servidor
            if resp.status_code >= 500:
                return f"❌ ERROR SERVIDOR: {resp.status_code}. Inténtalo más tarde."
            
            data = resp.json()

            # 1. Éxito total
            if data.get("success"):
                return f"✅ PAGO EXITOSO: ${amount} a '{vendor}' (Ref: {data.get('status')})"
            
            # 2. Requiere aprobación humana (Gobernanza)
            if data.get("status") == "PENDING_APPROVAL":
                return f"⏸️ ALTO: Aprobación requerida. Link enviado al dueño: {data['data']['approval_link']}"
            
            # 3. Rechazado (Fondos, fraude, etc)
            return f"⛔ DENEGADO: {data.get('message')}"

        except Exception as e:
            return f"⚠️ ERROR DE CONEXIÓN: {str(e)}"

    # --- CAMALEÓN: Adaptadores para Frameworks de IA ---

    def to_langchain(self):
        """🔌 Se convierte en una Tool de LangChain"""
        try:
            from langchain.tools import Tool
            # Usamos una lambda para parsear los argumentos que a veces llegan sucios
            return Tool(
                name="AgentPay_Wallet",
                func=lambda x: self._parse_args(x),
                description="Use this tool to pay for services, APIs, or products. Input string format MUST be: 'vendor, amount, description'."
            )
        except ImportError:
            return "❌ Error: La librería 'langchain' no está instalada en este entorno."

    def to_openai(self) -> Dict:
        """🔌 Se convierte en un Schema JSON para GPT-4 / Assistants API"""
        return {
            "type": "function",
            "function": {
                "name": "agentpay_execute_payment",
                "description": "Executes a real money payment. Use ONLY when the user explicitly asks to buy something.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vendor": {"type": "string", "description": "The recipient domain (e.g. google.com)"},
                        "amount": {"type": "number", "description": "Amount in USD"},
                        "description": {"type": "string", "description": "Reason for the transaction"}
                    },
                    "required": ["vendor", "amount", "description"]
                }
            }
        }

    def to_autogen(self) -> Dict:
        """🔌 Se convierte en config para Microsoft AutoGen"""
        return {
            "agentpay_pay": {
                "description": "Secure Payment Tool via AgentPay",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vendor": {"type": "string"},
                        "amount": {"type": "number"},
                        "description": {"type": "string"}
                    },
                    "required": ["vendor", "amount", "description"]
                }
            }
        }

    def _parse_args(self, input_str):
        """Ayudante interno para limpiar el texto que envían los robots"""
        try:
            # Limpia comillas y separa por comas (ej: "google, 10, api" -> ["google", "10", "api"])
            parts = [p.strip().strip("'").strip('"') for p in input_str.split(',')]
            if len(parts) >= 3:
                return self.pay(parts[0], float(parts[1]), parts[2])
            return "❌ Error de formato: Envía 'vendor, amount, description' separados por comas."
        except:
            return "❌ Error procesando los argumentos de pago."