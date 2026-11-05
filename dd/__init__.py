"""DD engine package.

Layering (deliberate):
  collection/  -> existing agents/ + scripts/  (scrapers, harvesters, DB)
  decision/    -> this package                  (deterministic screens + classification)
  assistant/   -> dd/agents_llm.py              (narrow LLM use: PDF fields, reply
                                                 classification, letter drafting)
  gate/        -> human approval before anything leaves the building
"""
__all__ = ["schema", "config", "classify", "underwrite"]
