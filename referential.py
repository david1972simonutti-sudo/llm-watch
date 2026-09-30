"""
referential.py — Référentiel stable des briques fonctionnelles LLM.

Source de vérité unique. Chaque item du CR est rattaché à UNE brique (clé).
Le schéma (onglet 3) et les tags du CR lisent ce module. Les trajectoires X→Y
et les sous-briques sont éditables ici, à un seul endroit.

Ancres = surveys de référence (voir la discussion). group :
  "amont"    = fabrication du modèle, en amont de tout usage
  "flux"     = chemin d'exécution d'une requête (du prompt au résultat)
  "transverse" = axes qui traversent toutes les couches
flow = position gauche→droite dans le schéma UX (None pour amont/transverse).
"""

BRICKS = {
    "architecture": {
        "label": "Architecture & pré-entraînement",
        "role": "Le modèle brut : structure interne et apprentissage initial.",
        "traj_from": "Transformer dense",
        "traj_to": "MoE sparse, attention GQA, contexte long, non-Transformer (Mamba)",
        "sub": ["Attention (MHA→MQA→GQA)", "Mixture-of-Experts", "Contexte long", "Espaces d'états (SSM)"],
        "anchor": "Zhao et al., arXiv:2303.18223 · lois d'échelle Chinchilla arXiv:2203.15556",
        "group": "amont", "flow": None,
    },
    "alignement": {
        "label": "Post-entraînement & alignement",
        "role": "Rendre le modèle utile, contrôlable et sûr après pré-entraînement.",
        "traj_from": "SFT / instruction tuning",
        "traj_to": "RLHF puis DPO / optimisation de préférences",
        "sub": ["Instruction tuning", "RLHF", "DPO / preference optimization"],
        "anchor": "Instruction Tuning: A Survey, arXiv:2308.10792",
        "group": "amont", "flow": None,
    },
    "prompting": {
        "label": "Interaction & prompting",
        "role": "Comment l'utilisateur formule et pilote la requête.",
        "traj_from": "zero / few-shot",
        "traj_to": "CoT, self-consistency, prompting structuré",
        "sub": ["Few-shot", "Chain-of-Thought", "Self-consistency", "Prompting structuré"],
        "anchor": "The Prompt Report, Schulhoff et al., arXiv:2406.06608",
        "group": "flux", "flow": 1,
    },
    "rag": {
        "label": "Augmentation & RAG",
        "role": "Injecter de la connaissance externe fraîche dans le contexte.",
        "traj_from": "Naive RAG",
        "traj_to": "Advanced RAG puis Modular RAG",
        "sub": ["Naive RAG", "Advanced RAG", "Modular RAG"],
        "anchor": "Gao et al., arXiv:2312.10997",
        "group": "flux", "flow": 2,
    },
    "agentique": {
        "label": "Outils & orchestration agentique",
        "role": "Enveloppe le flux : construit/réécrit le prompt, appelle des outils, boucle, puis formate le résultat.",
        "traj_from": "usage d'outils ponctuel (ReAct, Toolformer)",
        "traj_to": "agent autonome puis multi-agents (Agentic AI)",
        "sub": ["Tool use", "Agent autonome", "Multi-agents", "Mémoire / planification"],
        "anchor": "Wang et al. arXiv:2308.11432 · Xi et al. arXiv:2309.07864 · Agent AI arXiv:2401.03568",
        "group": "controle", "flow": None,
    },
    "raisonnement": {
        "label": "Raisonnement & test-time compute",
        "role": "Allouer plus de calcul au moment de générer pour mieux raisonner.",
        "traj_from": "CoT comme technique de prompt",
        "traj_to": "modèles de raisonnement entraînés (style o1), budget à l'inférence",
        "sub": ["Chain-of-Thought", "Reasoning models (o1-like)", "Inference-time scaling"],
        "anchor": "Towards Reasoning in LLMs: A Survey, arXiv:2212.10403",
        "group": "flux", "flow": 4,
    },
    "inference": {
        "label": "Inférence & efficience",
        "role": "Servir le modèle : vitesse, coût, mémoire à la génération.",
        "traj_from": "FP16 dense",
        "traj_to": "quantization INT4, PagedAttention/vLLM, speculative decoding",
        "sub": ["Quantization", "KV-cache / PagedAttention", "Speculative decoding", "FlashAttention"],
        "anchor": "Efficient LLMs: A Survey arXiv:2312.03863 · Model Compression arXiv:2308.07633",
        "group": "flux", "flow": 5,
    },
}

TRANSVERSE = {
    "evaluation": {"label": "Évaluation & benchmarks",
                   "role": "Mesurer les capacités et détecter la contamination."},
    "multimodal": {"label": "Multimodalité",
                   "role": "Texte, image, audio, vidéo dans un même modèle."},
    "securite":   {"label": "Sécurité & red-teaming",
                   "role": "Robustesse, jailbreaks, garde-fous, alignement en usage."},
}

# étiquettes canoniques pour valider ce que renvoie le modèle
BRICK_KEYS = list(BRICKS.keys())
TRANSVERSE_KEYS = list(TRANSVERSE.keys())
DEFAULT_BRICK = "architecture"


def normalize_brick(value):
    """Ramène une valeur libre du modèle vers une clé de brique valide."""
    if not value:
        return None
    v = str(value).strip().lower()
    if v in BRICKS:
        return v
    aliases = {
        "agent": "agentique", "agents": "agentique", "agentic": "agentique", "tools": "agentique", "outils": "agentique",
        "prompt": "prompting", "interaction": "prompting",
        "retrieval": "rag", "augmentation": "rag",
        "reasoning": "raisonnement", "test-time": "raisonnement", "test-time-compute": "raisonnement",
        "serving": "inference", "efficience": "inference", "efficiency": "inference", "inférence": "inference",
        "alignment": "alignement", "post-training": "alignement", "rlhf": "alignement", "dpo": "alignement",
        "pretraining": "architecture", "pré-entraînement": "architecture", "model": "architecture", "modele": "architecture",
    }
    return aliases.get(v)


def brick_label(key):
    b = BRICKS.get(key)
    return b["label"] if b else "Non classé"
