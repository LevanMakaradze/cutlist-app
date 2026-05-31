import xml.etree.ElementTree as ET

def generate_xml_project_tree(result, kerf_width, thickness="18"):
    """
    Generates the XML tree structure for a layout result.
    """
    project_el = ET.Element("project")

    no_counter = 0
    cut_counter = 1
    tol = 0.2

    def fmt(v):
        v = round(float(v), 1)
        return str(int(v)) if v.is_integer() else f"{v:.1f}"

    def lw_from_mode(width, height, lw_mode):
        if lw_mode == "XY":
            return fmt(width), fmt(height)
        return fmt(height), fmt(width)

    def child_lw_mode_from_parent_split(parent_split):
        return "XY" if parent_split == "horizontal" else "YX"

    def merge_intervals(intervals):
        if not intervals:
            return []
        intervals = sorted(intervals, key=lambda t: t[0])
        merged = [list(intervals[0])]
        for s, e in intervals[1:]:
            if s <= merged[-1][1] + tol:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        return [(a, b) for a, b in merged]

    def bands_for_orientation(region, rects, orient):
        x, y, w, h = region
        if orient == "horizontal":
            intervals = [(r["y"], r["y"] + r["h"]) for r in rects]
            bands = []
            for ys, ye in merge_intervals(intervals):
                band_rects = [
                    r for r in rects
                    if (r["y"] + r["h"]) >= ys - tol and r["y"] <= ye + tol
                ]
                bands.append({
                    "x": x,
                    "y": ys,
                    "w": w,
                    "h": ye - ys,
                    "rects": band_rects
                })
            bands.sort(key=lambda b: b["y"])
            return bands
        else:
            intervals = [(r["x"], r["x"] + r["w"]) for r in rects]
            bands = []
            for xs, xe in merge_intervals(intervals):
                band_rects = [
                    r for r in rects
                    if (r["x"] + r["w"]) >= xs - tol and r["x"] <= xe + tol
                ]
                bands.append({
                    "x": xs,
                    "y": y,
                    "w": xe - xs,
                    "h": h,
                    "rects": band_rects
                })
            bands.sort(key=lambda b: b["x"])
            return bands

    def band_needs_cut(region, band, orient):
        rx, ry, rw, rh = region
        if orient == "horizontal":
            return (band["h"] < rh - tol)
        return (band["w"] < rw - tol)

    def part_fills_region(band):
        for r in band["rects"]:
            if (
                abs(r["x"] - band["x"]) < tol and
                abs(r["y"] - band["y"]) < tol and
                abs(r["w"] - band["w"]) < tol and
                abs(r["h"] - band["h"]) < tol
            ):
                return r["spec_tuple"]
        return None

    def _collect_sheet_rects(sheet_layout):
        rects = []
        for placement in sheet_layout.placements:
            rects.append({
                "x": float(placement.x),
                "y": float(placement.y),
                "w": float(placement.width),
                "h": float(placement.height),
                "name": placement.part.spec.name,
                "spec_tuple": (placement.part.spec.name, placement.part.spec.width, placement.part.spec.height)
            })
        return rects

    unique_specs = list(set(
        (p.part.spec.name, p.part.spec.width, p.part.spec.height)
        for s in result.sheets
        for p in s.placements
    ))
    unique_specs.sort()
    pad_width = len(str(len(unique_specs))) if unique_specs else 2
    part_code_map = {}
    for idx, spec in enumerate(unique_specs):
        part_code_map[spec] = f"P{idx:0{pad_width}d}"

    total_part_nodes = 0

    def export_stage(panel_xml, sheet_layout, region, rects, lw_mode, region_id, orient, is_root=False):
        nonlocal no_counter, cut_counter, total_part_nodes

        if not rects and not is_root:
            return

        x, y, w, h = region
        bands = bands_for_orientation(region, rects, orient)
        if not bands and not is_root:
            return

        has_cuts = len(bands) > 1 or (len(bands) == 1 and band_needs_cut(region, bands[0], orient))
        if not has_cuts:
            other = "vertical" if orient == "horizontal" else "horizontal"
            bands_other = bands_for_orientation(region, rects, other)
            has_cuts_other = len(bands_other) > 1 or (len(bands_other) == 1 and band_needs_cut(region, bands_other[0], other))
            if has_cuts_other:
                orient = other
                bands = bands_other
                has_cuts = True
            else:
                return

        L, W = lw_from_mode(w, h, lw_mode)
        no_counter += 1
        node_id_str = "0" if is_root else str(region_id)
        
        swap_xy = sheet_layout.sheet.width < sheet_layout.sheet.height
        x_attr = fmt(y) if swap_xy else fmt(x)
        y_attr = fmt(x) if swap_xy else fmt(y)

        no_el = ET.SubElement(
            panel_xml,
            f"no.{no_counter}",
            {
                "l": L,
                "w": W,
                "x": x_attr,
                "y": y_attr,
                "id": node_id_str,
            }
        )

        cut_entries = []
        for band in bands:
            seg_id = cut_counter
            cut_counter += 1
            seg_len = band["h"] if orient == "horizontal" else band["w"]
            spec_tuple = part_fills_region(band)
            cut_type = "1" if spec_tuple is not None else "2"
            code = part_code_map.get(spec_tuple, "") if spec_tuple is not None else ""
            
            cut_entries.append({
                "cut": fmt(seg_len),
                "type": cut_type,
                "id": str(seg_id),
                "code": code,
                "_seg_id": seg_id,
                "_band": band,
                "_final": spec_tuple is not None and len(band["rects"]) == 1
            })

        for entry in cut_entries:
            attrs = {k: v for k, v in entry.items() if not k.startswith("_")}
            ET.SubElement(no_el, "part", attrs)
            total_part_nodes += 1

        next_mode = child_lw_mode_from_parent_split(orient)
        next_orient = "vertical" if orient == "horizontal" else "horizontal"
        for entry in reversed(cut_entries):
            band = entry["_band"]
            if entry["_final"]:
                continue
            export_stage(
                panel_xml,
                sheet_layout,
                region=(band["x"], band["y"], band["w"], band["h"]),
                rects=band["rects"],
                lw_mode=next_mode,
                region_id=entry["_seg_id"],
                orient=next_orient,
                is_root=False,
            )

    panel_index = 1
    for sheet_layout in result.sheets:
        part_rects = _collect_sheet_rects(sheet_layout)
        if not part_rects:
            continue

        # Dynamic Extraction: Material is read directly from the sheet's name
        material_name = getattr(sheet_layout.sheet, "name", "ლამინატი")

        panel = ET.SubElement(
            project_el,
            f"panel{panel_index}",
            {
                "l": fmt(sheet_layout.sheet.height),
                "w": fmt(sheet_layout.sheet.width),
                "material": str(material_name),
                "thickness": str(thickness),
                "saw": fmt(float(kerf_width)),
            }
        )

        export_stage(
            panel,
            sheet_layout,
            region=(0.0, 0.0, float(sheet_layout.sheet.width), float(sheet_layout.sheet.height)),
            rects=part_rects,
            lw_mode="YX",
            region_id=0,
            orient="horizontal",
            is_root=True,
        )
        panel_index += 1

    tree = ET.ElementTree(project_el)
    return tree, no_counter, total_part_nodes


def export_layout_xml(result, kerf, file_path, thickness="18"):
    """Export layout XML directly to a file path."""
    tree, _, _ = generate_xml_project_tree(result, kerf, thickness)
    ET.indent(tree, space="        ", level=0)

    with open(file_path, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)