"""UI component utilities for Macao Demographics Dashboard.

Provides reusable UI components for headers, sections, and decorative elements.
"""
import base64
import os
import logging

import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

def section_header(title: str, emoji: str = "📊") -> None:
    """Render a styled section header.
    
    Args:
        title: The header text
        emoji: Optional emoji icon (default: 📊)
    """
    st.markdown(f"""
    <div style="margin-bottom: 14px; margin-top: 8px;">
        <div class="section-header">
            {emoji} {title}
        </div>
        <div class="section-underline"></div>
    </div>
    """, unsafe_allow_html=True)

def decorative_header(title, subtitle="", badges=None, icon=None, project_root=None, icon_size=36, icon_bg='none', icon_bg_size=None, icon_inner_size=None, icon_margin_right=None, padding='28px 32px', title_font_size='2.5em'):
    """Decorative header with gradient background."""
    badges_html = ""
    if badges:
        badges_html = "<div style='margin-top: 12px; font-size: 0.95em; opacity: 0.85; display: flex; gap: 12px; flex-wrap: wrap;'>"
        for badge in badges:
            badges_html += f"<span style='background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 12px; backdrop-filter: blur(5px);'>{badge}</span>"
        badges_html += "</div>"

    default_icon_svg_base64 = (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIg"
        "eG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNCIgZmlsbD0iIzRhNTU2OCIvPgo8cmVjdCB4PSI0IiB5PSI2IiB3aWR0aD0iMjQiIGhlaWdodD0iMTYiIHJ4PSIyIiBmaWxsPSJ3aGl0ZSIvPgo8cmVjdCB4PSI2IiB5PSI4IiB3aWR0aD0iMjAiIGhlaWdodD0iMyIgZmlsbD0iIzY2N2VlYSIvPgo8cmVjdCB4PSI2IiB5PSIxMyIgd2lkdGg9IjEyIiBoZWlnaHQ9IjIiIGZpbGw9IiM2NjdlZWEiIG9wYWNpdHk9IjAuNyIvPgo8cmVjdCB4PSI2IiB5PSIxNyIgd2lkdGg9IjE2IiBoZWlnaHQ9IjIiIGZpbGw9IiM2NjdlZWEiIG9wYWNpdHk9IjAuNSIvPgo8Y2lyY2xlIGN4PSIyMiIgY3k9IjE4IiByPSIxLjUiIGZpbGw9IiM2NjdlZWEiLz4KPGNpcmNsZSBjeD0iMjUiIGN5PSIxOCIgcj0iMS41IiBmaWxsPSIjNjY3ZWVhIi8+CjxjaXJjbGUgY3g9IjIyIiBjeT0iMjEiIHI9IjEuNSIgZmlsbD0iIzY2N2VlYSIvPgo8L3N2Zz4="
    )

    icon_src = None
    try:
        _base_dir = os.path.dirname(os.path.abspath(__file__))
        project_images_dir = None
        if project_root:
            project_images_dir = os.path.join(project_root, 'images')
        else:
            project_images_dir = os.path.normpath(os.path.join(_base_dir, os.pardir, 'images'))

        if icon is not None and isinstance(icon, str):
            if icon.startswith('data:'):
                icon_src = icon
            elif os.path.isabs(icon) and os.path.exists(icon):
                with open(icon, 'rb') as f:
                    _d = f.read()
                ext = os.path.splitext(icon)[1].lower()
                mime = 'image/png' if ext in ['.png'] else 'image/svg+xml' if ext == '.svg' else 'image/png'
                icon_src = f"data:{mime};base64,{base64.b64encode(_d).decode('utf-8')}"
            elif project_images_dir:
                # Look for <icon>.png, <icon>.svg, icon file; else if icon looks like a filename with extension
                for candidate_name in [icon, f"{icon}.png", f"{icon}.svg"]:
                    candidate_path = os.path.join(project_images_dir, candidate_name)
                    if os.path.exists(candidate_path):
                        with open(candidate_path, 'rb') as f:
                            _d = f.read()
                        ext = os.path.splitext(candidate_path)[1].lower()
                        mime = 'image/png' if ext in ['.png'] else 'image/svg+xml' if ext == '.svg' else 'image/png'
                        icon_src = f"data:{mime};base64,{base64.b64encode(_d).decode('utf-8')}"
                        break
        if icon_src is None and project_images_dir:
            for fallback in ['dashboard.svg', 'dashboard.png', 'analysis.svg', 'analysis.png']:
                candidate_path = os.path.join(project_images_dir, fallback)
                if os.path.exists(candidate_path):
                    with open(candidate_path, 'rb') as f:
                        _d = f.read()
                    ext = os.path.splitext(candidate_path)[1].lower()
                    mime = 'image/png' if ext in ['.png'] else 'image/svg+xml' if ext == '.svg' else 'image/png'
                    icon_src = f"data:{mime};base64,{base64.b64encode(_d).decode('utf-8')}"
                    break
    except Exception:
        icon_src = None
    if not icon_src:
        icon_src = default_icon_svg_base64

    # Allow different icon presentations (inline or rounded circle background)
    if icon_bg == 'circle':
        if not icon_bg_size:
            icon_bg_size = 48
        if not icon_inner_size:
            icon_inner_size = 28
        if not icon_margin_right:
            icon_margin_right = 12
        icon_html = (
            f"<span style='display:inline-flex; align-items:center; justify-content:center; width:{icon_bg_size}px; height:{icon_bg_size}px; background: #fff; border-radius:50%; vertical-align:middle; margin-right:{icon_margin_right}px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);'>"
            f"<img src='{icon_src}' alt='icon' style='display:block; height:{icon_inner_size}px; width:auto; margin:0;' />"
            f"</span>"
        )
    else:
        if not icon_margin_right:
            icon_margin_right = 10
        icon_html = f"<img src='{icon_src}' width='{icon_size}' height='{icon_size}' style='vertical-align: middle; margin-right: {icon_margin_right}px;' alt='icon'/>"

    # Build a styled subtitle — if it begins with 'Year ####', render the year as a pill
    subtitle_html = ""
    if subtitle:
        try:
            import re
            m = re.match(r"^Year\s+(\d{4})\s*(.*)", str(subtitle).strip())
            if m:
                year = m.group(1)
                rest = m.group(2).strip() if m.group(2) else ''
                subtitle_html = (
                    f"<div style=\"margin: 12px 0 0 0; font-size: 1.1em; opacity: 0.95; font-weight: 500;\">"
                    f"Year <span style=\"font-weight: bold; font-size: 1.3em; background: rgba(255,255,255,0.2); padding: 2px 12px; border-radius: 20px; display: inline-block; margin: 0 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);\">{year}</span> {rest}"
                    f"</div>"
                )
            else:
                subtitle_html = f"<div style=\"margin: 12px 0 0 0; font-size: 1.1em; opacity: 0.95; font-weight: 500;\">{subtitle}</div>"
        except Exception:
            subtitle_html = f"<div style=\"margin: 12px 0 0 0; font-size: 1.1em; opacity: 0.95; font-weight: 500;\">{subtitle}</div>"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #5f3d8e 100%);
        color: white;
        padding: {padding};
        border-radius: 18px;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: -50%; right: -10%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%); border-radius: 50%; animation: float 6s ease-in-out infinite;"></div>
        <div style="position: absolute; bottom: -30%; left: -5%; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 70%); border-radius: 50%; animation: float 8s ease-in-out infinite reverse;"></div>
        <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-20px); }}
            }}
        </style>
        <div style="position: relative; z-index: 1;">
            <h1 style="margin: 0; font-size: {title_font_size}; font-weight: 800; letter-spacing: -1px;">
                {icon_html}{title}
            </h1>
            {subtitle_html if subtitle else ''}
            {badges_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def stat_box(title, value, subtitle="", yoy_label="", yoy_style=None):
    """Reusable stat box for KPIs."""
    yoy_html = ""
    if yoy_label and yoy_style:
        yoy_html = f"<div style='{yoy_style}'>{yoy_label}</div>"

    st.markdown(f"""
    <div class='stat-box' style="
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.12) 0%, rgba(41, 128, 185, 0.12) 100%);
        border-left-color: #3498db;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 15px; font-size: 1.2em;">{title}</div>
        <div style="font-size: 2.5em; font-weight: 900; color: #2c3e50; line-height: 1;">{value}</div>
        {f'<div style="font-size: 0.9em; color: #555; margin: 4px 0;">{subtitle}</div>' if subtitle else ''}
        {yoy_html}
    </div>
    """, unsafe_allow_html=True)