"""SRI Node Normalizer integration for non-OBO CURIEs.

The SRI Node Normalizer (https://nodenormalization-sri.renci.org/) provides
canonical identifiers and labels for CURIEs that lack OAK SQLite adapters,
such as EC numbers, CAS-RN, and PubChem CIDs.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

SRI_NORMALIZE_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"


@dataclass
class SRINormResult:
    """Result from SRI Node Normalizer."""

    input_curie: str
    normalized_curie: str | None
    label: str | None
    category: str | None
    found: bool


def normalize_curies(curies: list[str], *, timeout: int = 30) -> list[SRINormResult]:
    """Query the SRI Node Normalizer for a batch of CURIEs.

    Args:
        curies: List of CURIEs to normalize.
        timeout: Request timeout in seconds.

    Returns:
        List of SRINormResult for each input CURIE.
    """
    if not curies:
        return []

    results: list[SRINormResult] = []

    try:
        resp = requests.post(
            SRI_NORMALIZE_URL,
            json={"curies": curies, "conflate": True},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        # Return not-found for all on network error
        return [
            SRINormResult(
                input_curie=c,
                normalized_curie=None,
                label=None,
                category=None,
                found=False,
            )
            for c in curies
        ]

    for curie in curies:
        entry = data.get(curie)
        if entry is None:
            results.append(
                SRINormResult(
                    input_curie=curie,
                    normalized_curie=None,
                    label=None,
                    category=None,
                    found=False,
                )
            )
            continue

        norm_id = entry.get("id", {})
        label = norm_id.get("label")
        identifier = norm_id.get("identifier")
        types = entry.get("type", [])

        results.append(
            SRINormResult(
                input_curie=curie,
                normalized_curie=identifier,
                label=label,
                category=types[0] if types else None,
                found=True,
            )
        )

    return results
