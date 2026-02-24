from __future__ import annotations

from src.domain.models import RetrievedFAQ


def build_grounded_prompt(question: str, retrieved: list[RetrievedFAQ], max_context_chars: int) -> tuple[str, str]:
    context_blocks: list[str] = []
    for idx, entry in enumerate(retrieved, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[FAQ {idx}]",
                    f"Question: {entry.item.question}",
                    f"Answer: {entry.item.answer}",
                    f"URL: {entry.item.url}",
                ]
            )
        )

    context = "\n\n".join(context_blocks)
    if len(context) > max_context_chars:
        context = context[: max_context_chars - 3].rstrip() + "..."

    system = (
        "Tu es un assistant FAQ strictement factuel. "
        "Réponds uniquement à partir des FAQ fournies. "
        "Si l'information n'est pas présente dans les FAQ, réponds: 'Je ne sais pas.' "
        "Ne fabrique pas de politique, prix, ou procédure non citée. "
        "N'utilise pas de Markdown; pas de format [texte](url)."
    )

    user = (
        f"Question utilisateur:\n{question}\n\n"
        f"Contexte FAQ:\n{context}\n\n"
        "Instructions:\n"
        "1) Donne une réponse concise en français.\n"
        "2) Utilise prioritairement les FAQ les plus proches de la question.\n"
        "3) Si aucune FAQ ne permet une réponse fiable, réponds 'Je ne sais pas.'.\n"
        "4) En cas de contradiction, indique-le brièvement et reste prudent."
    )

    return system, user
