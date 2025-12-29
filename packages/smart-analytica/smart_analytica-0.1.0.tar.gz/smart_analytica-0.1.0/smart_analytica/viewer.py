"""
smart_analytica.viewer
----------------------
Functions to display an iframe in Jupyter, CLI, or a web browser.
"""

import webbrowser
import tempfile
import os
from pathlib import Path
from IPython.display import HTML, display
import sys

def _is_jupyter():
    """Check if running in Jupyter Notebook."""
    try:
        from IPython import get_ipython
        if 'IPKernelApp' not in get_ipython().config:
            return False
    except ImportError:
        return False
    return True

def show_iframe(
    url: str = "https://app.sigmacomputing.com/trackly/workbook/workbook-2tfcelIUvOZ9kBhSN70Bfm?:link_source=share",
    width: int = 1000,
    height: int = 400,
    border: bool = True,
    fullscreen: bool = True
):
    """
    Display an iframe containing Sigma Computing content.
    
    Parameters
    ----------
    url : str
        URL of the iframe source.
    width : int
        Width of the iframe (pixels).
    height : int
        Height of the iframe (pixels).
    border : bool
        Show border around iframe.
    fullscreen : bool
        Allow fullscreen mode.
    
    Returns
    -------
    None
    """
    # Build border style
    border_style = "1px solid #000000" if border else "none"
    
    # Build fullscreen attribute
    allow_fullscreen = "allowfullscreen" if fullscreen else ""
    
    # HTML for the iframe
    iframe_html = f"""
    <iframe 
        src="{url}"
        name="myiFrame"
        width="{width}px"
        height="{height}px"
        scrolling="no"
        marginwidth="0"
        marginheight="0"
        style="border:{border_style};"
        {allow_fullscreen}
    ></iframe>
    <div style="overflow:auto; position:absolute; height:0; width:0;">
        <a href="https://www.poper.ai/tools/iframe-generator/">iFrame Generator</a>
    </div>
    """

    # ---- DISPLAY LOGIC ----
    
    if _is_jupyter():
        # Jupyter Notebook/Lab
        display(HTML(iframe_html))
    
    else:
        # CLI → Open in default web browser
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Analytica Viewer</title>
            <style>
                body {{ margin:0; padding:0; overflow:hidden; }}
            </style>
        </head>
        <body>
            {iframe_html}
        </body>
        </html>
        """
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(
            suffix=".html", 
            mode='w', 
            delete=False, 
            encoding='utf-8'
        ) as f:
            f.write(html_content)
            tmp_filename = f.name

        # Open in browser
        webbrowser.open(f'file://{tmp_filename}')
        print(f"✅ Opened iframe in your browser! Temporary file: {tmp_filename}")
        print("📌 This file will self-delete when you close the browser.")
        
        # Optional: Auto-delete file after browser closes (advanced)
        # For simplicity we keep the file until manual deletion.