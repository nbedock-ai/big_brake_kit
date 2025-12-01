# data_scraper/vision_scraper.py
"""
Vision-based extraction pour les sources non-HTML :
- catalogues PDF (Zimmermann, StopTech, etc.)
- pages avec tableaux non parseables par BeautifulSoup
- fiches techniques d'atelier (knuckles, entraxes spécifiques)

V1 du projet BigBrakeKit n'utilise PAS ce module.
Il est préparé pour les missions ultérieures.
"""

from typing import List, Dict

# Placeholder pour le client Vision (Sonnet / autre LLM)
# Dans Windsurf, ce module sera adapté au SDK concret utilisé.
class VisionClient:
    def __init__(self):
        pass

    def extract_table(self, image_bytes: bytes, prompt: str) -> List[Dict]:
        """
        image_bytes : contenu binaire d'une page (PDF -> image ou screenshot HTML)
        prompt : consigne d'extraction (colonnes attendues)
        Retourne une liste de dicts, proche des schémas JSON internes.
        """
        # TODO: Implémentation spécifique à l'API Vision
        raise NotImplementedError


def extract_rotor_specs_from_pdf_page(image_bytes: bytes) -> List[Dict]:
    """
    Utilise Vision pour extraire les specs rotor d'une page de catalogue.
    Colonnes attendues (au minimum):
    - outer_diameter_mm
    - nominal_thickness_mm
    - hat_height_mm
    - overall_height_mm
    - center_bore_mm
    - bolt_circle_mm
    - bolt_hole_count
    - ventilation_type
    - directionality (si texte explicite)
    - rotor_weight_kg (si dispo)
    - oem_part_number (si dispo)
    """
    client = VisionClient()
    prompt = (
        "Extract a table of brake disc specifications. "
        "One row per rotor reference. "
        "Use metric units (mm, kg). "
        "Return structured data with keys matching the RotorSpec schema."
    )
    records = client.extract_table(image_bytes, prompt=prompt)
    return records


def extract_vehicle_knuckle_data_from_image(image_bytes: bytes) -> List[Dict]:
    """
    Vision pour extraire/estimer :
    - knuckle_bolt_spacing_mm
    - knuckle_bolt_orientation_deg
    à partir de vues techniques, plans ou photos annotées.

    V1 pourra rester NotImplemented, mais la signature est figée.
    """
    client = VisionClient()
    prompt = (
        "From this technical drawing or annotated photo, "
        "extract bolt spacing in millimeters and bolt orientation in degrees, "
        "for the brake caliper mounting points on the knuckle."
    )
    records = client.extract_table(image_bytes, prompt=prompt)
    return records
