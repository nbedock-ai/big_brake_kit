def normalize_bracket_geometry(raw: dict) -> dict:
    return {
        "knuckle_bolt_spacing_mm": raw.get("knuckle_bolt_spacing_mm"),
        "knuckle_bolt_orientation_deg": raw.get("knuckle_bolt_orientation_deg"),
        "rotor_center_offset_mm": raw.get("rotor_center_offset_mm"),
        "wheel_inner_barrel_clearance_mm": raw.get("wheel_inner_barrel_clearance_mm"),
        "max_rotor_diameter_mm": raw.get("max_rotor_diameter_mm"),
        "rotor_thickness_min_mm": raw.get("rotor_thickness_min_mm"),
        "rotor_thickness_max_mm": raw.get("rotor_thickness_max_mm"),
        "is_axial_mount": raw.get("is_axial_mount"),
        "is_radial_mount": raw.get("is_radial_mount"),
        "caliper_clearance_mm": raw.get("caliper_clearance_mm")
    }
