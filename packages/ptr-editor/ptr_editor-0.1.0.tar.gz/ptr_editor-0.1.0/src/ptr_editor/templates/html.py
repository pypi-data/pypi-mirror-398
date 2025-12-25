"""HTML generation utilities for template registry display."""

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
    from .register import TemplateRegister


def generate_notebook_html(registry: "TemplateRegister") -> str:
    """
    Generate HTML suitable for Jupyter notebook display.

    Returns only the content div without full HTML structure to avoid
    affecting the notebook's global styles.

    :param registry: The TemplateRegister instance to render
    :return: HTML string for notebook display
    """
    groups = registry.list_groups()
    ungrouped = [k for k in registry._templates if ":" not in k]

    # Use scoped styles that won't affect the notebook
    html = """
    <div class="ptr-template-registry">
        <style scoped>
            .ptr-search-box {
                margin-bottom: 12px;
                width: 100%;
                max-width: 350px;
                padding: 6px 10px;
                font-size: 0.9em;
                border: 1px solid var(--jp-border-color2, #e0e0e0);
                border-radius: 3px;
                background: transparent;
                color: inherit;
                box-sizing: border-box;
            }
            .ptr-template-registry {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 0.9em;
                margin: 8px 0;
            }
            .ptr-template-registry h1 {
                border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);
                padding-bottom: 8px;
                margin-top: 0;
                font-size: 1.2em;
                font-weight: 600;
            }
            .ptr-tabs {
                margin-bottom: 12px;
            }
            .ptr-tab-buttons {
                display: flex;
                border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);
                flex-wrap: wrap;
                gap: 4px;
            }
            .ptr-tab-button {
                background: transparent;
                border: 1px solid var(--jp-border-color2, #e0e0e0);
                border-bottom: none;
                padding: 6px 16px;
                cursor: pointer;
                border-radius: 3px 3px 0 0;
                color: inherit;
                outline: none;
                transition: all 0.2s;
                font-size: 0.9em;
            }
            .ptr-tab-button:hover {
                border-color: var(--jp-brand-color1, #2196F3);
            }
            .ptr-tab-button.active {
                border-color: var(--jp-brand-color1, #2196F3);
                font-weight: 600;
                background: var(--jp-layout-color1, transparent);
            }
            .ptr-tab-content {
                display: none;
                padding: 12px 0;
            }
            .ptr-tab-content.active {
                display: block;
            }
            .ptr-summary {
                padding: 8px 0;
                border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);
                margin-bottom: 12px;
                font-size: 0.9em;
            }
            .ptr-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 8px;
                font-size: 0.9em;
            }
            .ptr-table th, .ptr-table td {
                border-bottom: 1px solid var(--jp-border-color3, #f0f0f0);
                padding: 4px 8px;
                text-align: left;
                vertical-align: middle;
            }
            .ptr-table th {
                border-bottom: 1px solid var(--jp-border-color2, #e0e0e0);
                font-weight: 600;
            }
            .ptr-table tr:last-child td {
                border-bottom: none;
            }
            .ptr-table tr {
                margin: 0;
                padding: 0;
            }
            .ptr-expand-btn {
                background: transparent;
                color: inherit;
                border: 1px solid var(--jp-border-color2, #e0e0e0);
                padding: 3px 10px;
                cursor: pointer;
                border-radius: 3px;
                transition: all 0.2s;
                font-size: 0.85em;
            }
            .ptr-expand-btn:hover {
                border-color: var(--jp-brand-color1, #2196F3);
            }
            .ptr-xml-content {
                display: none;
                margin-top: 4px;
            }
            .ptr-xml-content.show {
                display: block;
            }
            .ptr-template-xml {
                background: transparent;
                padding: 8px;
                border-radius: 3px;
                overflow-x: auto;
                font-family: var(--jp-code-font-family, 'Consolas', 'Monaco', monospace);
                font-size: 0.85em;
                border: 1px solid var(--jp-border-color2, #e0e0e0);
                max-height: 300px;
                overflow-y: auto;
                line-height: 1.4;
                text-align: left !important;
            }
            .ptr-template-xml pre {
                margin: 0;
                padding: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
                text-align: left !important;
            }
            .ptr-template-xml code {
                background: transparent;
                padding: 0;
                text-align: left !important;
            }
            .ptr-template-xml * {
                text-align: left !important;
            }
        </style>
        <script>
            // Search/filter functionality for template tables
            function filterTemplates() {
                var input = document.getElementById('ptr-template-search');
                var filter = input.value.toLowerCase();
                var tables = document.querySelectorAll('.ptr-table');
                tables.forEach(function(table) {
                    var rows = table.querySelectorAll('tbody tr');
                    var showCount = 0;
                    for (var i = 0; i < rows.length; i += 2) {
                        var nameCell = rows[i].querySelector('td');
                        if (!nameCell) continue;
                        var name = nameCell.textContent || nameCell.innerText;
                        var match = name.toLowerCase().indexOf(filter) !== -1;
                        rows[i].style.display = match ? '' : 'none';
                        rows[i+1].style.display = match ? '' : 'none';
                        if (match) showCount++;
                    }
                });
            }

            // Tab switching functionality
            function openTab(evt, tabName) {
                var i, tabcontent, tabbuttons;
                tabcontent = document.querySelectorAll('.ptr-tab-content');
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].classList.remove('active');
                }
                tabbuttons = document.querySelectorAll('.ptr-tab-button');
                for (i = 0; i < tabbuttons.length; i++) {
                    tabbuttons[i].classList.remove('active');
                }
                var tab = document.getElementById(tabName);
                if (tab) tab.classList.add('active');
                if (evt && evt.currentTarget) {
                    evt.currentTarget.classList.add('active');
                }
            }

            // Toggle XML visibility
            function toggleXml(templateId) {
                var content = document.getElementById('xml-' + templateId);
                if (content) {
                    content.classList.toggle('show');
                }
            }
        </script>

    """


    # Search box
    html += """
        <input id='ptr-template-search' class='ptr-search-box'
               type='text' placeholder='Search templates...'
               onkeyup='filterTemplates()'>
    """

    # Summary section
    html += f"""
        <div class="ptr-summary">
            <strong>Total Templates:</strong> {len(registry._templates)}<br>
            <strong>Groups:</strong> {len(groups)}<br>
            <strong>Ungrouped:</strong> {len(ungrouped)}
        </div>
    """

    # Tabs container
    html += '<div class="ptr-tabs">'

    # Tab buttons
    html += '<div class="ptr-tab-buttons">'
    tab_count = 0
    for i, group in enumerate(groups):
        active_class = " active" if tab_count == 0 else ""
        html += (
            f'<button class="ptr-tab-button{active_class}" '
            f'onclick="openTab(event, \'tab-{i}\')">{html_module.escape(str(group))}</button>'
        )
        tab_count += 1
    if ungrouped:
        active_class = " active" if tab_count == 0 else ""
        html += (
            f'<button class="ptr-tab-button{active_class}" '
            f'onclick="openTab(event, \'tab-ungrouped\')">Ungrouped</button>'
        )
        tab_count += 1
    html += "</div>"  # Close ptr-tab-buttons

    # Tab contents
    tab_count = 0
    for i, group in enumerate(groups):
        templates = registry.list_templates(group=group)
        active_class = " active" if tab_count == 0 else ""
        html += f'<div id="tab-{i}" class="ptr-tab-content{active_class}">'  # Tab content
        html += f"<h3>{html_module.escape(str(group))} ({len(templates)} templates)</h3>"
        html += _generate_template_table(
            registry, templates, show_simple_name=True, group_prefix=str(i),
        )
        html += "</div>"
        tab_count += 1

    if ungrouped:
        active_class = " active" if tab_count == 0 else ""
        html += f'<div id="tab-ungrouped" class="ptr-tab-content{active_class}">'  # Tab content
        html += f"<h3>Ungrouped ({len(ungrouped)} templates)</h3>"
        html += _generate_template_table(
            registry, ungrouped, show_simple_name=False, group_prefix="ungrouped",
        )
        html += "</div>"
        tab_count += 1

    html += "</div>"  # Close ptr-tabs
    html += "</div>"  # Close ptr-template-registry
    return html


def _generate_template_table(
    registry: "TemplateRegister",
    template_names: list[str],
    show_simple_name: bool = True,
    group_prefix: str = "",
) -> str:
    """
    Generate HTML table for templates.

    :param registry: The TemplateRegister instance
    :param template_names: List of template names
    :param show_simple_name: Whether to strip group prefix from display
    :param group_prefix: Prefix for unique IDs
    :return: HTML string for the table
    """
    html = """
    <table class="ptr-table">
        <thead>
            <tr>
                <th>Template Name</th>
                <th>Type</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    """

    for template_name in sorted(template_names):
        template = registry._templates[template_name]


        if show_simple_name and ":" in template_name:
            display_name = template_name.split(":", 1)[1]
        else:
            display_name = template_name

        type_name = type(template.element).__name__

        # Get XML representation
        xml_str = _get_xml_string(template.element)
        
        # Apply syntax highlighting if available
        if PYGMENTS_AVAILABLE:
            formatter = HtmlFormatter(
                style="default",
                noclasses=True,
                nobackground=True,
            )
            xml_highlighted = highlight(xml_str, XmlLexer(), formatter)
        else:
            xml_highlighted = f"<pre><code>{html_module.escape(xml_str)}</code></pre>"

        # Make unique, safe HTML id
        unique_id = (
            f"{group_prefix}-{template_name}"
        )
        unique_id = unique_id.replace(":", "-").replace(" ", "-").replace("/", "-")

        html += f"""
        <tr style="margin:0;padding:0;">
            <td style="margin:0;padding:4px 6px;">{html_module.escape(str(display_name))}</td>
            <td style="margin:0;padding:4px 6px;"><code>{html_module.escape(str(type_name))}</code></td>
            <td style="margin:0;padding:4px 6px;">
                <button class="ptr-expand-btn" onclick="toggleXml('{unique_id}')">
                    Show XML
                </button>
            </td>
        </tr>
        <tr style="margin:0;padding:0;">
            <td colspan="3" style="margin:0;padding:0;">
                <div id="xml-{unique_id}" class="ptr-xml-content">
                    <div class="ptr-template-xml">
                        {xml_highlighted}
                    </div>
                </div>
            </td>
        </tr>
        """

    html += """
        </tbody>
    </table>
    """
    return html


def _get_xml_string(template) -> str:
    """
    Extract XML string representation from a template object.

    :param template: Template object (BaseElement or similar)
    :return: XML string representation
    """
    if hasattr(template, "xml"):
        return str(template.xml)  # type: ignore[attr-defined]
    if hasattr(template, "to_xml"):
        return str(template.to_xml())  # type: ignore[attr-defined]
    return str(template)
