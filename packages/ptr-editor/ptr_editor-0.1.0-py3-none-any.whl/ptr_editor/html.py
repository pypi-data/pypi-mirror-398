from __future__ import annotations

import html as html_module
from typing import TYPE_CHECKING

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import XmlLexer
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

if TYPE_CHECKING:
    from ptr_editor.elements.blocks import ObsBlock
    from ptr_editor.elements.timeline import Timeline


def extract_human_readable_properties(block: ObsBlock) -> dict[str, str]:
    """Extract human-readable properties from an observation block.

    Args:
        block: The ObsBlock to extract properties from

    Returns:
        Dictionary of property names to human-readable values
    """
    properties = {}

    # Basic block properties
    properties["Type"] = block.element_type
    properties["Id"] = block.id
    properties["Start"] = str(block.start.isoformat() if block.start else "N/A")
    properties["End"] = str(block.end.isoformat() if block.end else "N/A")
    properties["Duration"] = str(block.duration)
    properties["Designer"] = block.designer or "N/A"

    # Attitude information
    if block.attitude:
        properties["Attitude"] = block.attitude.element_type

        # Phase angle information
        if hasattr(block.attitude, "phase_angle") and block.attitude.phase_angle:
            properties["Phase Angle"] = block.attitude.phase_angle.element_type

        # Offset angles information
        if hasattr(block.attitude, "offset_angles"):
            if block.attitude.offset_angles:
                properties["Offset"] = block.attitude.offset_angles.element_type
            else:
                properties["Offset"] = "No"

        if hasattr(block.attitude, "target"):
            properties["Target"] = str(block.attitude.target.element_type)

        if hasattr(block.attitude, "boresight"):
            properties["Boresight"] = str(block.attitude.boresight.element_type)

    return properties



def extract_human_readable_properties2(block: ObsBlock) -> dict[str, str]:
    """Extract human-readable properties from an observation block.

    Args:
        block: The ObsBlock to extract properties from

    Returns:
        Dictionary of property names to human-readable values
    """
    from ptr_editor.io.simplified_converter2 import conv
    props = conv.unstructure(block)
    from pandas import json_normalize

    table = json_normalize(props, sep=":")
    return table.to_dict()


def render_dict_as_html(data: dict[str, str]) -> str:
    """Render a dictionary as a styled HTML section.

    Args:
        data: Dictionary of key-value pairs to render

    Returns:
        HTML string with a visually appealing representation of the data
    """
    if not data:
        return ""

    # Container and table styles
    container_style = (
        "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        "border-radius: 8px; "
        "padding: 2px; "
        "margin-bottom: 15px; "
        "box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);"
    )

    inner_container_style = (
        "background-color: white; "
        "border-radius: 6px; "
        "padding: 15px;"
    )

    table_style = (
        "width: 100%; "
        "border-collapse: separate; "
        "border-spacing: 0 8px;"
    )

    key_cell_style = (
        "padding: 8px 12px; "
        "font-weight: 600; "
        "color: #4a5568; "
        "text-align: right; "
        "white-space: nowrap; "
        "width: 20%; "
        "font-family: -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, sans-serif; "
        "font-size: 0.875rem;"
    )

    value_cell_style = (
        "padding: 8px 12px; "
        "color: #2d3748; "
        "background-color: #f7fafc; "
        "border-radius: 4px; "
        "font-family: 'Consolas', 'Monaco', monospace; "
        "font-size: 0.875rem; "
        "word-break: break-word;"
    )

    # Build the HTML table
    rows = []
    for key, value in data.items():
        escaped_key = html_module.escape(str(key))
        escaped_value = html_module.escape(str(value))
        rows.append(
            f"<tr>"
            f"<td style='{key_cell_style}'>{escaped_key}:</td>"
            f"<td style='{value_cell_style}'>{escaped_value}</td>"
            f"</tr>",
        )

    return (
        f"<div style='{container_style}'>"
        f"<div style='{inner_container_style}'>"
        f"<table style='{table_style}'>"
        f"{''.join(rows)}"
        f"</table>"
        f"</div>"
        f"</div>"
    )


def render_xml_html(
    xml_content: str,
    header_info: dict[str, str] | None = None,
) -> str:
    """Return syntax-highlighted XML representation of XML for Jupyter notebooks.

    Args:
        xml_content: The XML string to render
        header_info: Optional dictionary of key-value pairs to display in a header
                     before the XML content

    Returns:
        HTML string with syntax highlighting if pygments is available,
        otherwise plain escaped HTML
    """
    # XML content container
    xml_container_style = (
        "max-height:500px;"
        "overflow:auto;"
        "background:#1e1e1e;"
        "border-radius:6px;"
        "padding:12px;"
    )

    if PYGMENTS_AVAILABLE:
        # Use monokai style for dark theme
        formatter = HtmlFormatter(
            style="monokai",
            noclasses=True,
            nobackground=True,
        )
        highlighted = highlight(xml_content, XmlLexer(), formatter)
        xml_html = f"<div style='{xml_container_style}'>{highlighted}</div>"
    else:
        # Fallback if pygments is not available
        xml_str = html_module.escape(xml_content)
        xml_html = (
            f"<div style='{xml_container_style}'>"
            f"<pre style='color:#d4d4d4;margin:0;'><code>{xml_str}</code></pre>"
            f"</div>"
        )

    # If no header info, return just the XML
    if not header_info:
        return xml_html

    # Create clean, minimal header with scroll support
    header_style = (
        "background:#2d3748;"
        "border-radius:6px;"
        "padding:12px 16px;"
        "overflow:auto;"
        "max-height:500px;"
    )

    table_style = (
        "border-collapse:collapse;"
        "border-spacing:0;"
        "width:100%;"
    )

    key_style = (
        "padding:6px 12px 6px 0;"
        "font-weight:500;"
        "color:#a0aec0;"
        "text-align:right;"
        "font-size:11px;"
        "font-family:'SF Mono','Monaco','Consolas',monospace;"
        "letter-spacing:0.3px;"
        "white-space:nowrap;"
        "vertical-align:top;"
    )

    value_style = (
        "padding:6px 0 6px 12px;"
        "color:#e2e8f0;"
        "font-size:11px;"
        "font-family:'SF Mono','Monaco','Consolas',monospace;"
        "word-break:break-word;"
        "overflow-wrap:anywhere;"
        "vertical-align:top;"
        "line-height:1.4;"
    )

    # Build header table
    rows = []
    for key, value in header_info.items():
        escaped_key = html_module.escape(str(key))
        escaped_value = html_module.escape(str(value))
        rows.append(
            f"<tr>"
            f"<td style='{key_style}'>{escaped_key}</td>"
            f"<td style='{value_style}'>{escaped_value}</td>"
            f"</tr>",
        )

    header_html = (
        f"<div style='{header_style}'>"
        f"<table style='{table_style}'>{''.join(rows)}</table>"
        f"</div>"
    )

    # Two-column layout with 50/50 split and proper overflow handling
    layout_style = (
        "display:flex;"
        "gap:12px;"
        "align-items:stretch;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;"
    )

    header_col_style = "flex:1;min-width:0;max-width:50%;overflow:auto;"
    xml_col_style = "flex:1;min-width:0;max-width:50%;"

    return (
        f"<div style='{layout_style}'>"
        f"<div style='{header_col_style}'>{header_html}</div>"
        f"<div style='{xml_col_style}'>{xml_html}</div>"
        f"</div>"
    )


def render_xml_html2(
    xml_content: str,
    header_info: dict[str, str] | None = None,
) -> str:
    """Return theme-neutral XML representation for Jupyter notebooks.

    Uses CSS variables and minimal styling to blend with notebook themes.

    Args:
        xml_content: The XML string to render
        header_info: Optional dictionary of key-value pairs to display in a header
                     before the XML content

    Returns:
        HTML string with theme-neutral styling
    """
    # XML content container - theme neutral with subtle borders
    xml_container_style = (
        "max-height: 500px; "
        "overflow: auto; "
        # "border: 1px solid var(--jp-border-color2, #e0e0e0); "
        # "border-radius: 4px; "
        # "padding: 12px; "
        "font-family: var(--jp-code-font-family, 'Consolas', 'Monaco', monospace); "
        "font-size: 0.9em; "
        "line-height: 1.4;"
    )

    if PYGMENTS_AVAILABLE:
        # Use a minimal formatter that respects theme
        formatter = HtmlFormatter(
            style="default",
            noclasses=True,
            nobackground=True,
        )
        highlighted = highlight(xml_content, XmlLexer(), formatter)
        xml_html = f"<div style='{xml_container_style}'>{highlighted}</div>"
    else:
        # Fallback if pygments is not available
        xml_str = html_module.escape(xml_content)
        xml_html = (
            f"<div style='{xml_container_style}'>"
            f"<pre style='margin: 0; white-space: pre-wrap; word-wrap: break-word;'>"
            f"<code>{xml_str}</code></pre>"
            f"</div>"
        )

    # If no header info, return just the XML
    if not header_info:
        return xml_html

    # Create minimal, theme-neutral header
    header_style = (
        # "border: 1px solid var(--jp-border-color2, #e0e0e0); "
        # "border-radius: 4px; "
        # "padding: 8px; "
        "overflow: auto; "
        "max-height: 500px; "
        # "margin-bottom: 8px;"
    )

    table_style = (
        "border-collapse: collapse; "
        "width: 100%; "
        "font-size: 0.9em;"
    )

    key_style = (
        "padding: 4px 8px 4px 0; "
        "font-weight: 500; "
        "text-align: right; "
        "white-space: nowrap; "
        "vertical-align: top; "
        "opacity: 0.8;"
    )

    value_style = (
        "padding: 4px 0 4px 8px; "
        "font-family: var(--jp-code-font-family, 'Consolas', 'Monaco', monospace); "
        "word-break: break-word; "
        "vertical-align: top; "
        "border-left: 1px solid var(--jp-border-color2, #e0e0e0);"
    )

    # Build header table
    rows = []
    for key, value in header_info.items():
        escaped_key = html_module.escape(str(key))
        escaped_value = html_module.escape(str(value))
        rows.append(
            f"<tr>"
            f"<td style='{key_style}'>{escaped_key}</td>"
            f"<td style='{value_style}'>{escaped_value}</td>"
            f"</tr>",
        )

    header_html = (
        f"<div style='{header_style}'>"
        f"<table style='{table_style}'>{''.join(rows)}</table>"
        f"</div>"
    )

    # Two-column layout with proper overflow handling
    layout_style = (
        "display: flex; "
        "gap: 8px; "
        "align-items: stretch; "
        "margin: 8px 0;"
    )

    header_col_style = "flex: 1; min-width: 0; max-width: 50%; overflow: auto;"
    xml_col_style = "flex: 1; min-width: 0; max-width: 50%;"

    return (
        f"<div style='{layout_style}'>"
        f"<div style='{xml_col_style}'>{xml_html}</div>"
        f"<div style='{header_col_style}'>{header_html}</div>"
        f"</div>"
    )


def render_html_timeline(timeline: Timeline) -> str:
    """Return HTML representation of a Timeline for Jupyter notebooks.

    Args:
        timeline: The Timeline object to render

    Returns:
        HTML string with a table representation of the timeline blocks
    """
    blocks = list(timeline)  # Use the iterator interface instead of _blocks

    if not blocks:
        return f"<b>Timeline&lt;{id(timeline)}&gt;</b>: <i>empty</i>"

    # Build table header with timeline info
    html_parts = [
        f"<h3>Timeline&lt;{id(timeline)}&gt;: "
        f"frame={timeline.frame}, "
        f"blocks={len(blocks)}, "
        f"start={timeline.start}, "
        f"end={timeline.end}</h3>",
        "<table border='1' style='border-collapse:collapse;'>",
        "<thead><tr>"
        "<th>#</th>"
        "<th>Type</th>"
        "<th>Start</th>"
        "<th>End</th>"
        "<th>Designer</th>"
        "</tr></thead>",
        "<tbody>",
    ]

    # Add rows for each block
    for idx, block in enumerate(blocks):
        block_type = block.element_type
        start = getattr(block, "start_time", getattr(block, "start", ""))
        end = getattr(block, "end_time", getattr(block, "end", ""))
        designer = getattr(block, "designer", "")
        html_parts.append(
            f"<tr>"
            f"<td>{idx}</td>"
            f"<td>{block_type}</td>"
            f"<td>{start}</td>"
            f"<td>{end}</td>"
            f"<td>{designer}</td>"
            f"</tr>",
        )

    html_parts.append("</tbody></table>")
    return "".join(html_parts)


def render_html_obs_block(block: ObsBlock) -> str:
    """Returns HTML representation for Jupyter notebooks."""
    # CSS styles for better readability with darker colors
    container_style = (
        "border: 2px solid #2E7D32; border-radius: 8px; "
        "padding: 15px; margin: 10px 0; background-color: #fafafa; "
        "box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
    )
    header_style = "color: #1B5E20; margin-top: 0; font-weight: bold;"
    table_style = "width: 100%; border-collapse: collapse; margin-top: 10px;"
    header_cell_style = (
        "padding: 8px; border: 1px solid #666; font-weight: bold; "
        "color: #1B5E20; background-color: #E8F5E8;"
    )
    cell_style = "padding: 8px; border: 1px solid #888; color: #333;"
    property_cell_style = (
        "padding: 8px; border: 1px solid #888; color: #1B5E20; font-weight: 500;"
    )
    header_bg_style = "background-color: #E8F5E8;"
    meta_bg_style = "background-color: #E3F2FD;"
    meta_header_style = (
        "padding: 8px; border: 1px solid #666; font-weight: bold; "
        "text-align: center; color: #0D47A1; background-color: #E3F2FD;"
    )

    html = f"""
    <div style="{container_style}">
        <h3 style="{header_style}">ObsBlock: {block.id}</h3>
        <table style="{table_style}">
            <tr style="{header_bg_style}">
                <td style="{header_cell_style}">Property</td>
                <td style="{header_cell_style}">Value</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">ID</td>
                <td style="{cell_style}">{block.id}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">Designer</td>
                <td style="{cell_style}">{block.designer or "N/A"}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">Start Time</td>
                <td style="{cell_style}">{block.start or "N/A"}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">End Time</td>
                <td style="{cell_style}">{block.end or "N/A"}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">Duration</td>
                <td style="{cell_style}">{block.duration or "N/A"}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">Index</td>
                <td style="{cell_style}">{block.index or "N/A"}</td>
            </tr>
            <tr>
                <td style="{property_cell_style}">Attitude Type</td>
                <td style="{cell_style}">
                    {type(block.attitude).__name__ if block.attitude else "N/A"}
                </td>
            </tr>
    """

    # Add attitude details if available
    if block.attitude:
        html += f"""
            <tr>
                <td style="{cell_style}">Attitude Details</td>
                <td style="{cell_style}">{block.attitude!s}</td>
            </tr>
        """

    # Add metadata information if available
    if block.metadata:
        html += f"""
            <tr style="{meta_bg_style}">
                <td colspan="2" style="{meta_header_style}">Metadata</td>
            </tr>
        """

        if block.metadata.planning:
            html += f"""
                <tr>
                    <td style="{property_cell_style} padding-left: 20px;">
                        Planning Available
                    </td>
                    <td style="{cell_style}">✓ Yes</td>
                </tr>
            """

            if (
                hasattr(block.metadata.planning, "observations")
                and block.metadata.planning.observations
            ):
                obs = block.metadata.planning.observations
                if hasattr(obs, "designer") and obs.designer:
                    html += f"""
                        <tr>
                            <td style="{property_cell_style} padding-left: 20px;">
                                Observations Designer
                            </td>
                            <td style="{cell_style}">{obs.designer}</td>
                        </tr>
                    """

                if hasattr(obs, "designer_observations") and obs.designer_observations:
                    obs_count = len(obs.designer_observations)
                    html += f"""
                        <tr>
                            <td style="{property_cell_style} padding-left: 20px;">
                                Designer Observations Count
                            </td>
                            <td style="{cell_style}">{obs_count}</td>
                        </tr>
                    """

                    # Show first few designer observations
                    max_display = 3
                    for i, des_obs in enumerate(
                        obs.designer_observations[:max_display],
                    ):
                        if hasattr(des_obs, "definition"):
                            html += f"""
                                <tr>
                                    <td style="{property_cell_style} padding-left: 40px;">
                                        Observation {i + 1}
                                    </td>
                                    <td style="{cell_style}">
                                        {des_obs.definition}
                                    </td>
                                </tr>
                            """

                    if obs_count > max_display:
                        remaining = obs_count - max_display
                        html += f"""
                            <tr>
                                <td style="{property_cell_style} padding-left: 40px;">
                                    ...
                                </td>
                                <td style="{cell_style}">
                                    +{remaining} more observations
                                </td>
                            </tr>
                        """
        else:
            html += f"""
                <tr>
                    <td style="{property_cell_style} padding-left: 20px;">Planning</td>
                    <td style="{cell_style}">N/A</td>
                </tr>
            """
    else:
        html += f"""
            <tr>
                <td style="{property_cell_style}">Metadata</td>
                <td style="{cell_style}">N/A</td>
            </tr>
        """

    html += """
        </table>
    </div>
    """

    return html
