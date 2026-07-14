"""Customer-support evaluation cases (80) for demo / MVP acceptance."""

from __future__ import annotations

from typing import Any

CATEGORIES = [
    "password_problem",
    "duplicate_charge",
    "refund_problem",
    "account_blocked",
    "general_question",
]

# Explicit seed bank — expanded into 80 distinct cases below.
_TEMPLATES: dict[str, list[tuple[str, str, str]]] = {
    # (input, difficulty, language) — priority implied by category rules
    "password_problem": [
        ("No puedo cambiar mi contraseña.", "easy", "es"),
        ("Olvidé mi password y no me deja resetear.", "easy", "es"),
        ("Mi clave no funciona desde ayer.", "easy", "es"),
        ("I can't change my password.", "easy", "en"),
        ("Forgot password link never arrives.", "medium", "en"),
        ("Quiero actualizar la contraseña del usuario admin pero falla el formulario.", "medium", "es"),
        ("No recuerdo la clave y el botón de recuperar está roto.", "medium", "es"),
        ("Password reset returns error 500.", "medium", "en"),
        ("Intenté cambiar la contraseña tres veces y sigue pidiendo la anterior.", "medium", "es"),
        (
            "Compará mi intento de cambio de contraseña con el procedimiento del contrato "
            "de seguridad y decime si puedo forzar el reset sin multa de bloqueo temporal.",
            "hard",
            "es",
        ),
        ("La contraseña temporal expiró y no puedo generar otra.", "easy", "es"),
        ("Unable to update password from the mobile app.", "easy", "en"),
        ("Me pide clave actual pero nunca la configuré.", "medium", "es"),
        ("Reset de contraseña en portugués: nao consigo alterar minha senha.", "medium", "pt"),
        ("El sistema rechaza mi nueva contraseña aunque cumple las reglas.", "medium", "es"),
        ("Necesito ayuda urgente: bloqueo por intentos de password fallidos.", "hard", "es"),
    ],
    "duplicate_charge": [
        ("Me cobraron dos veces la misma factura.", "easy", "es"),
        ("Hay un cargo duplicado en mi tarjeta.", "easy", "es"),
        ("I was charged twice for invoice 18392.", "easy", "en"),
        ("Aparecen dos débitos idénticos el mismo día.", "medium", "es"),
        ("Double charge on my last bill.", "easy", "en"),
        ("Me cobraron dos veces el servicio premium.", "easy", "es"),
        ("Veo un cobro repetido por la factura 44110.", "medium", "es"),
        ("Pagaron dos veces el mismo recibo desde mi cuenta.", "medium", "es"),
        (
            "Compará estos dos movimientos bancarios: débito A 14:02 y débito B 14:05 "
            "por el mismo monto de la factura 18392 y confirmá si es cobro duplicado.",
            "hard",
            "es",
        ),
        ("Se duplicó el cargo de la suscripción mensual.", "easy", "es"),
        ("Duplicate transaction for the same invoice.", "medium", "en"),
        ("Me figura un cobro doble en el resumen de cuenta.", "medium", "es"),
        ("Fui debitado dos veces por el mismo concepto.", "easy", "es"),
        ("Analizá el contrato adjunto de facturación y el extracto: cobro doble sospechoso.", "hard", "es"),
        ("Hay dos cargos iguales en la factura consolidada.", "medium", "es"),
        ("They billed me twice for the same purchase.", "easy", "en"),
    ],
    "refund_problem": [
        ("Quiero un reembolso de mi última compra.", "easy", "es"),
        ("No me devolvieron el dinero del producto.", "easy", "es"),
        ("I need a refund for order 8821.", "easy", "en"),
        ("Solicité el reembolso hace 10 días y no hay novedades.", "medium", "es"),
        ("Refund still pending after cancellation.", "medium", "en"),
        ("Cancelé el servicio y quiero que me devuelvan el saldo.", "medium", "es"),
        ("El reembolso parcial no coincide con lo prometido.", "medium", "es"),
        ("Cómo hago para pedir la devolución del cargo premium?", "easy", "es"),
        (
            "Según el contrato de cancelación, analízá si puedo cancelarlo sin multa "
            "y obtener reembolso total de los meses no usados.",
            "hard",
            "es",
        ),
        ("Pagué de más y quiero refund del excedente.", "easy", "es"),
        ("My refund request was rejected without explanation.", "medium", "en"),
        ("Necesito recuperar el cobro de un producto defectuoso.", "medium", "es"),
        ("La devolución aparece como procesada pero no llegó a la tarjeta.", "medium", "es"),
        ("Pedido de reembolso por servicio no prestado.", "easy", "es"),
        ("Comparar política de refund vs lo que me cobraron al cancelar.", "hard", "es"),
        ("Please process a refund ASAP.", "easy", "en"),
    ],
    "account_blocked": [
        ("Mi cuenta está bloqueada.", "easy", "es"),
        ("No puedo ingresar, dice cuenta suspendida.", "easy", "es"),
        ("My account is locked after failed logins.", "easy", "en"),
        ("Me bloquearon el acceso sin aviso.", "medium", "es"),
        ("Account suspended for suspicious activity.", "medium", "en"),
        ("Quedé bloqueado después de cambiar el dispositivo.", "medium", "es"),
        ("Mi usuario aparece locked y el soporte no responde.", "medium", "es"),
        ("No me deja operar: cuenta bloqueada por seguridad.", "easy", "es"),
        (
            "Analizá el contrato de uso y las reglas de bloqueo: me suspendieron por "
            "comparación automática de riesgo y quiero apelar la decisión.",
            "hard",
            "es",
        ),
        ("Estoy blocked y necesito reactivar urgente.", "easy", "es"),
        ("The account was locked overnight.", "easy", "en"),
        ("Suspensión temporal que no se levanta.", "medium", "es"),
        ("Me figura cuenta bloqueada en la app y en la web.", "easy", "es"),
        ("Se bloqueó mi perfil empresarial completo.", "medium", "es"),
        ("Locked out and MFA also fails.", "medium", "en"),
        ("Bloqueo injustificado después de un pago fallido.", "hard", "es"),
    ],
    "general_question": [
        ("Cuál es el horario de atención?", "easy", "es"),
        ("How do I update my email address?", "easy", "en"),
        ("Dónde veo mis facturas anteriores?", "easy", "es"),
        ("Puedo cambiar el plan de mi suscripción?", "easy", "es"),
        ("What documents do I need to open an account?", "medium", "en"),
        ("Necesito el comprobante de un pago viejo.", "medium", "es"),
        ("Cómo contacto a un asesor humano?", "easy", "es"),
        ("Quiero saber si hay sucursales en Montevideo.", "easy", "es"),
        (
            "Compará las cláusulas de renovación automática del contrato con lo "
            "publicado en la web y decime qué opción me conviene.",
            "hard",
            "es",
        ),
        ("Tienen app para Android?", "easy", "es"),
        ("Can I share my plan with family members?", "medium", "en"),
        ("Información sobre límites de transferencia diaria.", "medium", "es"),
        ("Cuánto demora una transferencia internacional?", "easy", "es"),
        ("Quiero consultar el estado de un trámite iniciado ayer.", "medium", "es"),
        ("Analizar este contrato extenso: ¿puedo migrar de plan sin penalidad?", "hard", "es"),
        ("Is there a student discount?", "easy", "en"),
    ],
}


def _priority_for(category: str) -> str:
    if category in {"duplicate_charge", "account_blocked"}:
        return "high"
    if category == "general_question":
        return "low"
    return "medium"


def build_customer_support_cases(target: int = 80) -> list[dict[str, Any]]:
    """Build a deterministic list of evaluation cases (default 80)."""
    cases: list[dict[str, Any]] = []
    idx = 1

    # First pass: all templates
    for category, rows in _TEMPLATES.items():
        for text, difficulty, language in rows:
            cases.append(
                {
                    "case_key": f"cs_{idx:03d}",
                    "task_type": "customer_support",
                    "input": text,
                    "expected_output": {
                        "category": category,
                        "priority": _priority_for(category),
                    },
                    "difficulty": difficulty,
                    "language": language,
                    "tags": [category, difficulty, language],
                }
            )
            idx += 1

    # Pad to target with controlled paraphrases if needed
    paraphrases = [
        ("Otra consulta: {base}", "easy"),
        ("Buenas, {base}", "easy"),
        ("Urgente — {base}", "medium"),
        ("Detalle adicional del caso: {base}", "medium"),
    ]
    base_pool = list(cases)
    p = 0
    while len(cases) < target:
        source = base_pool[p % len(base_pool)]
        template, diff = paraphrases[p % len(paraphrases)]
        # Avoid turning easy keyword cases into hard "contrato/compar" text (keeps labels valid)
        new_input = template.format(base=source["input"])
        if "contrato" in new_input.lower() or "compar" in new_input.lower():
            diff = "hard"
        cases.append(
            {
                "case_key": f"cs_{idx:03d}",
                "task_type": "customer_support",
                "input": new_input,
                "expected_output": source["expected_output"],
                "difficulty": diff if source["difficulty"] != "hard" else "hard",
                "language": source["language"],
                "tags": list(source["tags"]) + ["paraphrase"],
            }
        )
        idx += 1
        p += 1

    return cases[:target]


CUSTOMER_SUPPORT_CASES = build_customer_support_cases(80)
