# gmail_html_utils.py
# HTML template functions for MediLink Gmail HTTPS server
# Python 3.4.4 + XP SP3 compatible


def _format_cert_field(field_data, default='Unknown'):
    """Format certificate subject or issuer field data for display.
    
    The ssl._ssl._test_decode_cert() function returns subject/issuer as a tuple
    of tuples, where each entry is like: (('fieldName', 'value'),)
    
    Args:
        field_data: Tuple of tuples from certificate parsing, or None
        default: Default value if field_data is empty/None
    
    Returns:
        str: Formatted string like "commonName: localhost, organizationName: MediLink"
    """
    if not field_data:
        return default
    
    parts = []
    try:
        for item in field_data:
            # item is like (('countryName', 'US'),) - a tuple containing a tuple
            if isinstance(item, tuple) and len(item) > 0:
                inner = item[0]
                if isinstance(inner, tuple) and len(inner) == 2:
                    # Normal case: (('fieldName', 'value'),)
                    parts.append('{}: {}'.format(inner[0], inner[1]))
                elif isinstance(inner, str):
                    # Simple string case
                    parts.append(inner)
                else:
                    parts.append(str(inner))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
    except Exception:
        # If any parsing fails, return what we have or the default
        if parts:
            return ', '.join(parts)
        return default
    
    return ', '.join(parts) if parts else default

def build_cert_info_html(cert_info, fingerprint=None, browser_info=None, server_port=8000):
    """Build HTML page showing certificate information for trust instructions.
    
    Args:
        cert_info: Dictionary with certificate details from get_certificate_summary()
        fingerprint: Optional dict with certificate fingerprint (from get_certificate_fingerprint)
        browser_info: Optional dict with browser detection info (name, version, isWindowsXP)
        server_port: Server port number (default 8000)
    
    Returns:
        str: HTML content for certificate info page
    """
    expires = cert_info.get('notAfter', 'Unknown')
    subject = cert_info.get('subject', [])
    issuer = cert_info.get('issuer', [])
    subject_str = _format_cert_field(subject, 'Unknown')
    issuer_str = _format_cert_field(issuer, 'Self-signed')
    warning = cert_info.get('warning')
    error = cert_info.get('error')
    
    # Detect Firefox 52 on Windows XP for special instructions
    is_firefox_52_xp = False
    if browser_info:
        is_firefox_52_xp = (browser_info.get('name') == 'Firefox' and 
                           browser_info.get('version') == '52' and 
                           browser_info.get('isWindowsXP') is True)
    
    # Build fingerprint display section
    fingerprint_html = ""
    if fingerprint and (fingerprint.get('sha256_colon') or fingerprint.get('sha1_colon')):
        fp_section = '<h4>Certificate Fingerprint</h4><div style="background: #f0f0f0; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 0.9em; word-break: break-all; margin-top: 12px;">'
        if fingerprint.get('sha256_colon'):
            fp_section += '<div><strong>SHA-256:</strong><br>{}</div>'.format(fingerprint['sha256_colon'])
        if fingerprint.get('sha1_colon'):
            fp_section += '<div style="margin-top: 8px;"><strong>SHA-1:</strong><br>{}</div>'.format(fingerprint['sha1_colon'])
        fp_section += '</div><p style="font-size: 0.9em; color: #666; margin-top: 8px;">Verify this fingerprint matches what Firefox shows when adding the exception.</p>'
        fingerprint_html = fp_section
    
    # Build instructions based on browser
    if is_firefox_52_xp:
        instructions = """
        <div style="background: #fff4e6; border: 1px solid #f0ad4e; padding: 16px; border-radius: 6px; margin: 16px 0;">
            <h3 style="margin-top: 0; color: #8b4513;">Firefox 52 on Windows XP - Certificate Trust Instructions</h3>
            <ol style="line-height: 1.8;">
                <li><strong>Open https://127.0.0.1:{port} directly in Firefox</strong> (you should see a security warning)</li>
                <li>Click the <strong>"Advanced"</strong> or <strong>"I Understand the Risks"</strong> button</li>
                <li>Click <strong>"Add Exception..."</strong> or <strong>"Confirm Security Exception"</strong></li>
                <li><strong>Verify the certificate fingerprint</strong> matches the one shown above</li>
                <li>Check the box for <strong>"Permanently store this exception"</strong></li>
                <li>Click <strong>"Confirm Security Exception"</strong></li>
                <li><strong>Important:</strong> After adding the exception, you may need to <strong>close and reopen Firefox</strong> for the exception to take effect</li>
                <li>Return to the MediLink web app and run the connectivity test again</li>
            </ol>
            <p style="margin-top: 12px; margin-bottom: 0;"><strong>Note:</strong> If the certificate dialog doesn't appear, try closing all Firefox windows and reopening, then navigate to https://127.0.0.1:{port} again.</p>
        </div>
        """.format(port=server_port)
    else:
        instructions = """
        <ol style="line-height: 1.8;">
            <li>Click the "Advanced" or "More information" button in your browser's warning page.</li>
            <li>Select "Accept the risk" / "Add exception" to trust https://127.0.0.1:{port}.</li>
            <li>Return to the MediLink web app and run the connectivity test again.</li>
        </ol>
        """.format(port=server_port)
    
    # Build download link (if fingerprint available, offer download)
    download_link = ""
    if fingerprint:
        download_link = '<p style="margin-top: 16px;"><a href="/_cert_download" download="medilink-local.crt" style="padding: 8px 16px; background: #3B2323; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">Download Certificate (.crt)</a></p>'
    
    extra = ""
    if warning:
        # Escape HTML in warning message for safety
        safe_warning = str(warning).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        extra += "<p><strong>Note:</strong> {}</p>".format(safe_warning)
    if error:
        # Escape HTML in error message for safety
        safe_error = str(error).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        extra += "<p><strong>Error decoding certificate:</strong> {}</p>".format(safe_error)

    html = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>MediLink Local Certificate</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #2b2b2b; max-width: 800px; }}
            h1 {{ color: #3B2323; }}
            .card {{ border: 1px solid #d9cbbd; border-radius: 8px; padding: 16px; background: #faf8f5; }}
            ol {{ margin-top: 10px; }}
            .meta {{ margin-top: 12px; font-size: 0.95em; }}
            .meta div {{ margin-bottom: 4px; }}
        </style>
    </head>
    <body>
        <h1>Local HTTPS Certificate</h1>
        <div class="card">
            <div class="meta">
                <div><strong>Subject:</strong> {subject}</div>
                <div><strong>Issuer:</strong> {issuer}</div>
                <div><strong>Expires:</strong> {expires}</div>
            </div>
            {fingerprint}
            {extra}
            {download_link}
            <h3>How to trust this certificate</h3>
            {instructions}
        </div>
    </body>
    </html>""".format(
        subject=subject_str, 
        issuer=issuer_str, 
        expires=expires,
        fingerprint=fingerprint_html,
        instructions=instructions, 
        extra=extra,
        download_link=download_link
    )
    return html


def build_root_status_html(safe_status, cert_info, recent_requests, server_port, firefox_diagnosis=None, ca_details=None, use_http_mode=False):
    """Build a friendly status page for the server root (HTTP or HTTPS).
    
    Args:
        safe_status: Dictionary with server status from get_safe_status()
        cert_info: Dictionary with certificate details from get_certificate_summary()
        recent_requests: List or deque of recent request records
        server_port: Integer port number for the server
        firefox_diagnosis: Optional dictionary with Firefox certificate diagnostic results
        use_http_mode: Boolean indicating if server is in HTTP mode (no SSL/TLS)
    
        ca_details: Optional dict describing certificate authority status
    
    Returns:
        str: HTML content for root status page
    """
    # Determine protocol based on HTTP mode
    protocol = 'http' if use_http_mode else 'https'
    
    # Determine status display
    phase = safe_status.get('phase', 'idle')
    safe_to_close = safe_status.get('safeToClose', False)

    if safe_to_close:
        status_class = 'status-safe'
        status_icon = '[OK]'
        status_text = 'Safe to close'
        status_desc = 'All processing complete. You can close this tab.'
    elif phase in ['processing', 'downloading', 'cleanup_triggered']:
        status_class = 'status-working'
        status_icon = '[...]'
        status_text = 'Working'
        status_desc = 'Processing files in the background.'
    else:
        status_class = 'status-attention'
        status_icon = '[!]'
        status_text = 'Attention needed'
        status_desc = 'Check the main app for next steps.'

    # Certificate info
    cert_present = cert_info.get('present', False)
    cert_expires = cert_info.get('notAfter', 'Unknown') if cert_present else 'Not available'
    cert_status = 'Present' if cert_present else 'Missing'

    # Recent activity
    recent_activity = ""
    try:
        if recent_requests:
            # Convert to list if deque, take last 3
            try:
                requests_list = list(recent_requests)
                if len(requests_list) > 3:
                    requests_list = requests_list[-3:]
            except Exception:
                requests_list = []
            
            if requests_list:
                recent_activity = "<ul style='margin: 8px 0; padding-left: 20px;'>"
                for req in requests_list:
                    time_str = req.get('time', '')[:19]  # YYYY-MM-DDTHH:MM:SS
                    method = req.get('method', 'GET')
                    path = req.get('path', '/')
                    status = req.get('status', 200)
                    recent_activity += "<li>{} {} {} (status {})</li>".format(time_str, method, path, status)
                recent_activity += "</ul>"
            else:
                recent_activity = "<p style='color: #666; font-style: italic; margin: 8px 0;'>No recent activity</p>"
        else:
            recent_activity = "<p style='color: #666; font-style: italic; margin: 8px 0;'>No recent activity</p>"
    except Exception:
        # Fallback if any error occurs processing recent requests
        recent_activity = "<p style='color: #666; font-style: italic; margin: 8px 0;'>No recent activity</p>"

    # Build Firefox diagnostic section if provided
    firefox_diag_html = ""
    if firefox_diagnosis and firefox_diagnosis.get('profile_found'):
        # Helper function to escape HTML
        def html_escape(s):
            if not s:
                return ''
            s = str(s)
            s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            return s
        
        # Determine severity and recommendations
        has_exception = len(firefox_diagnosis.get('matching_exceptions', [])) > 0
        fingerprint_matches = False
        if has_exception:
            fingerprint_matches = firefox_diagnosis['matching_exceptions'][0].get('matches_current_cert', False)
        
        # Build diagnostic display
        if not has_exception:
            # No exception found - show prominent warning
            firefox_diag_html = """
            <div class="info-section" style="background: #fff4e6; border: 2px solid #f0ad4e;">
                <h3 style="color: #8b4513; margin-top: 0;">[!] Firefox Certificate Issue Detected</h3>
                <p><strong>Problem:</strong> No certificate exception found in Firefox.</p>
                <p><strong>Solution:</strong></p>
                <ol>
                    <li>Click the link below to view certificate details</li>
                    <li>Follow the instructions to add a permanent exception</li>
                    <li>After adding, close and reopen Firefox</li>
                </ol>
                <p style="margin-top: 12px;"><a href="/_cert" class="action-btn">View Certificate &amp; Instructions</a></p>
            </div>
            """
        elif not fingerprint_matches:
            # Exception exists but fingerprint doesn't match
            exc = firefox_diagnosis['matching_exceptions'][0]
            stored_fp = html_escape(exc.get('stored_fingerprint', 'Unknown'))
            current_fp = html_escape(firefox_diagnosis.get('current_cert_fingerprint_sha1', 'Unknown'))
            firefox_diag_html = """
            <div class="info-section" style="background: #fdecea; border: 2px solid #dc2626;">
                <h3 style="color: #dc2626; margin-top: 0;">[!] Certificate Exception Mismatch</h3>
                <p><strong>Problem:</strong> Firefox has an exception for this server, but it's for a different certificate (certificate was likely regenerated).</p>
                <p><strong>Stored Fingerprint:</strong> <code>{stored_fp}</code></p>
                <p><strong>Current Fingerprint:</strong> <code>{current_fp}</code></p>
                <p><strong>Solution:</strong></p>
                <ol>
                    <li>Remove the old exception: Firefox Options &gt; Privacy &amp; Security &gt; Certificates &gt; View Certificates &gt; Servers tab</li>
                    <li>Find and remove any entry for <code>127.0.0.1:{port}</code></li>
                    <li>Click the link below to add a new exception</li>
                    <li>Restart Firefox after adding</li>
                </ol>
                <p style="margin-top: 12px;"><a href="/_cert" class="action-btn">View Certificate &amp; Add Exception</a></p>
            </div>
            """.format(
                stored_fp=stored_fp,
                current_fp=current_fp,
                port=server_port
            )
        elif fingerprint_matches:
            # Exception exists and matches - but fetch() might still fail (Firefox quirk)
            firefox_diag_html = """
            <div class="info-section" style="background: #fff4e6; border: 2px solid #f0ad4e;">
                <h3 style="color: #8b4513; margin-top: 0;">[i] Certificate Exception Found</h3>
                <p><strong>Status:</strong> Firefox has a certificate exception that matches the current certificate.</p>
                <p><strong>If JavaScript requests are still failing:</strong></p>
                <ol>
                    <li>Close all Firefox windows completely</li>
                    <li>Reopen Firefox and try again</li>
                    <li>If still failing, remove and re-add the exception</li>
                </ol>
            </div>
            """
        
        # Add diagnostic details section (collapsible)
        installed = 'Yes' if firefox_diagnosis.get('firefox_installed') else 'No'
        profile = 'Yes' if firefox_diagnosis.get('profile_found') else 'No'
        exceptions = firefox_diagnosis.get('exceptions_found', 0)
        sha1 = html_escape(firefox_diagnosis.get('current_cert_fingerprint_sha1', 'N/A'))
        diagnosis = html_escape(firefox_diagnosis.get('diagnosis', 'N/A'))
        
        diag_details = """
        <div class="info-section" style="margin-top: 16px; font-size: 0.9em;">
            <details>
                <summary style="cursor: pointer; font-weight: bold; color: #666;">Diagnostic Details (click to expand)</summary>
                <table class="meta-table" style="margin-top: 12px;">
                    <tr><td class="meta-label">Firefox Installed:</td><td>{installed}</td></tr>
                    <tr><td class="meta-label">Profile Found:</td><td>{profile}</td></tr>
                    <tr><td class="meta-label">Exceptions Found:</td><td>{exceptions}</td></tr>
                    <tr><td class="meta-label">Current SHA-1:</td><td style="font-family: monospace; font-size: 0.85em; word-break: break-all;">{sha1}</td></tr>
                </table>
                <p style="margin-top: 12px; color: #666;"><strong>Diagnosis:</strong> {diagnosis}</p>
            </details>
        </div>
        """.format(
            installed=installed,
            profile=profile,
            exceptions=exceptions,
            sha1=sha1,
            diagnosis=diagnosis
        )
        firefox_diag_html += diag_details

    ca_section = ""
    if ca_details and ca_details.get('managed'):
        ca_status = ca_details.get('status') or {}
        root_meta = ca_status.get('root') or {}
        server_meta = ca_status.get('server') or {}
        san_values = ca_status.get('san') or []
        san_display = ', '.join(san_values) if san_values else '127.0.0.1'
        root_expires = root_meta.get('notAfter', 'Unknown')
        root_subject = root_meta.get('subject', 'Managed CA')
        server_subject = server_meta.get('subject', '127.0.0.1')
        ca_section = """
        <div class="info-section" style="background: #edf8ff;">
            <h3>Managed Certificate Authority</h3>
            <p style="margin-top: 0;">Trust once, then skip exception prompts. The Gmail helper keeps certificates aligned with this managed root.</p>
            <table class="meta-table">
                <tr><td class="meta-label">Root Subject:</td><td>{root_subject}</td></tr>
                <tr><td class="meta-label">Root Expires:</td><td>{root_expires}</td></tr>
                <tr><td class="meta-label">Server Subject:</td><td>{server_subject}</td></tr>
                <tr><td class="meta-label">SubjectAltName:</td><td>{sans}</td></tr>
            </table>
            <p style="margin-top: 12px;">
                <a href="/ca/root.crt" class="action-btn" style="float: none; width: auto; display: inline-block;">Download CA Root</a>
                <a href="/ca/server-info.json" class="action-btn secondary" style="float: none; width: auto; display: inline-block; margin-left: 8px;">View status JSON</a>
            </p>
            <div style="clear: both;"></div>
        </div>
        """.format(
            root_subject=root_subject,
            root_expires=root_expires,
            server_subject=server_subject,
            sans=san_display
        )

    html = """<!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>MediLink Local Server</title>
        <style type="text/css">
            body {{
                font-family: Arial, Helvetica, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f3e8;
                color: #2b2b2b;
                line-height: 1.6;
            }}
            .container {{
                width: 600px;
                margin: 0 auto;
                background: white;
                border: 1px solid #ccc;
                overflow: hidden;
            }}
            .header {{
                background: #3B2323;
                color: white;
                padding: 24px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2em;
                font-weight: normal;
            }}
            .header p {{
                margin: 8px 0 0 0;
                font-size: 1.1em;
            }}
            .status-card {{
                padding: 24px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .status-badge {{
                display: inline-block;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 0.95em;
                text-transform: uppercase;
            }}
            .status-safe {{ background: #e8f7ee; color: #1f5132; border: 1px solid #30a46c; }}
            .status-working {{ background: #fff4e6; color: #8b4513; border: 1px solid #f0ad4e; }}
            .status-attention {{ background: #fdecea; color: #dc2626; border: 1px solid #dc2626; }}
            .actions {{
                margin-top: 20px;
                overflow: hidden;
            }}
            .action-btn {{
                display: block;
                float: left;
                width: 48%;
                margin-right: 2%;
                padding: 12px 20px;
                background: #3B2323;
                color: white;
                text-decoration: none;
                text-align: center;
                font-weight: bold;
            }}
            .action-btn:hover {{ background: #4E3B3B; }}
            .action-btn.secondary {{ background: #6b5b5b; }}
            .action-btn.secondary:hover {{ background: #7a6a6a; }}
            .info-section {{
                padding: 20px 24px;
                background: #f8f7f5;
                border-bottom: 1px solid #e0e0e0;
            }}
            .info-section h3 {{
                margin: 0 0 12px 0;
                color: #3B2323;
                font-size: 1.1em;
            }}
            .meta-table {{
                width: 100%;
                font-size: 0.9em;
                border-collapse: collapse;
            }}
            .meta-table td {{
                padding: 4px 8px;
            }}
            .meta-label {{
                font-weight: bold;
                color: #666;
                width: 40%;
            }}
            .footer {{
                padding: 16px 24px;
                background: #faf9f7;
                text-align: center;
                font-size: 0.85em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MediLink Local Server</h1>
                <p>Secure file processing service</p>
            </div>

            <div class="status-card">
                <h2 style="margin: 0 0 16px 0; color: #3B2323;">Server Status</h2>
                <div class="status-badge {status_class}">
                    <span>{status_icon}</span> <span>{status_text}</span>
                </div>
                <p style="margin: 12px 0; color: #666;">{status_desc}</p>

                <div class="actions">
                    <a href="/_diag" class="action-btn">Run diagnostics</a>
                    <a href="/_cert" class="action-btn secondary">View certificate</a>
                </div>
            </div>

            <div class="info-section">
                <h3>System Information</h3>
                <table class="meta-table">
                    <tr>
                        <td class="meta-label">Certificate:</td>
                        <td>{cert_status}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Expires:</td>
                        <td>{cert_expires}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Phase:</td>
                        <td>{phase}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Port:</td>
                        <td>{server_port}</td>
                    </tr>
                </table>
            </div>

            {ca_section}

            <div class="info-section">
                <h3>Recent Activity</h3>
                {recent_activity}
            </div>

            {firefox_diag_html}

            <div class="footer">
                <p>This local server handles secure file processing for MediLink. Keep this page open during active processing.</p>
            </div>
        </div>
        <script>
        (function() {{
            var useHttpMode = {use_http_mode_js};
            var certDialogOpened = false; // Track if we've already opened the certificate dialog
            
            // Test if fetch() works (detects if JavaScript requests are blocked)
            setTimeout(function() {{
                fetch('{protocol}://127.0.0.1:{server_port}/_health', {{ 
                    method: 'GET', 
                    mode: 'cors', 
                    cache: 'no-store',
                    credentials: 'omit'
                }}).then(function(response) {{
                    if (response.ok) {{
                        console.log('Fetch API test: SUCCESS');
                    }} else {{
                        console.warn('Fetch API test: HTTP ' + response.status);
                    }}
                }}).catch(function(err) {{
                    // Fetch failed - likely certificate issue for JavaScript requests
                    var warningDiv = document.createElement('div');
                    warningDiv.className = 'info-section';
                    warningDiv.style.cssText = 'background: #fdecea; border: 2px solid #dc2626; margin-top: 16px;';
                    
                    // Automatically open certificate dialog if not in HTTP mode and not already opened
                    var opened = false;
                    if (!certDialogOpened && !useHttpMode) {{
                        certDialogOpened = true;
                        var rootUrl = window.location.origin; // Use same origin (https://127.0.0.1:8000)
                        
                        // Method 1: window.open()
                        try {{
                            var newWindow = window.open(rootUrl, '_blank');
                            if (newWindow && !newWindow.closed) {{
                                opened = true;
                                console.log('Certificate dialog opened in new tab via window.open()');
                            }} else if (newWindow === null) {{
                                console.debug('window.open() returned null - popup likely blocked');
                            }}
                        }} catch (e) {{
                            console.debug('window.open() failed:', e);
                        }}
                        
                        // Method 2: Link element fallback
                        if (!opened) {{
                            try {{
                                var link = document.createElement('a');
                                link.href = rootUrl;
                                link.target = '_blank';
                                link.rel = 'noopener noreferrer';
                                link.style.display = 'none';
                                document.body.appendChild(link);
                                link.click();
                                setTimeout(function() {{
                                    try {{
                                        if (link.parentNode) {{
                                            document.body.removeChild(link);
                                        }}
                                    }} catch (removeErr) {{
                                        // Ignore removal errors
                                    }}
                                }}, 100);
                                opened = true;
                                console.log('Certificate dialog opened via link element fallback');
                            }} catch (e) {{
                                console.debug('Link element method failed:', e);
                            }}
                        }}
                    }}
                    
                    // Build warning message based on whether dialog was opened
                    if (opened) {{
                        warningDiv.innerHTML = '<h3 style="color: #dc2626; margin-top: 0;">[!] Certificate Trust Required</h3>' +
                            '<p><strong>Action:</strong> A new tab has been opened to accept the certificate.</p>' +
                            '<p>Please accept the security certificate in the new tab, then return here. The page will automatically retry the connection.</p>' +
                            '<p><a href="/_cert" style="display: inline-block; padding: 8px 16px; background: #3B2323; color: white; text-decoration: none; margin-top: 8px;">View Certificate Instructions</a></p>';
                    }} else {{
                        warningDiv.innerHTML = '<h3 style="color: #dc2626; margin-top: 0;">[!] JavaScript Requests Blocked</h3>' +
                            '<p><strong>Issue:</strong> The page loaded, but JavaScript API requests (fetch) are being blocked by Firefox.</p>' +
                            '<p>This usually means the certificate exception needs to be re-added or Firefox needs to be restarted.</p>' +
                            '<p><a href="/_cert" style="display: inline-block; padding: 8px 16px; background: #3B2323; color: white; text-decoration: none; margin-top: 8px;">View Certificate Instructions</a></p>';
                    }}
                    
                    var container = document.querySelector('.container');
                    if (container) {{
                        var footer = container.querySelector('.footer');
                        if (footer) {{
                            container.insertBefore(warningDiv, footer);
                        }} else {{
                            container.appendChild(warningDiv);
                        }}
                    }}
                    console.warn('Fetch API test: FAILED -', err);
                }});
            }}, 1000); // Small delay to let page render first
        }})();
        </script>
    </body>
    </html>""".format(
        status_class=status_class,
        status_icon=status_icon,
        status_text=status_text,
        status_desc=status_desc,
        cert_status=cert_status,
        cert_expires=cert_expires,
        phase=phase,
        server_port=server_port,
        protocol=protocol,
        recent_activity=recent_activity,
        firefox_diag_html=firefox_diag_html,
        ca_section=ca_section,
        use_http_mode_js='true' if use_http_mode else 'false'
    )
    return html


def build_managed_ca_contextual_guidance(certificate_provider=None, diag_report=None, 
                                         firefox_diagnosis=None, ca_status=None, 
                                         cert_info=None, server_port=8000):
    """
    Build contextual, progressive guidance for managed CA certificate issues.
    
    Provides issue-specific guidance with progressive disclosure:
    - Level 1: Summary + primary action (always visible)
    - Level 2: Step-by-step instructions (expandable)
    - Level 3: Technical details (expandable)
    
    Args:
        certificate_provider: Dict with CA mode and status
        diag_report: Diagnostics report with issues/warnings
        firefox_diagnosis: Firefox certificate diagnosis results
        ca_status: Managed CA status from get_managed_ca_status()
        cert_info: Current certificate information
        server_port: Server port number
    
    Returns:
        str: HTML with contextual guidance, or empty string if not applicable
    """
    try:
        provider = certificate_provider or {}
        mode = (provider.get('mode') or '').lower()
        
        # Only provide contextual guidance in managed CA mode with issues
        if mode != 'managed_ca':
            return ''
        
        if not diag_report or not diag_report.get('issues'):
            return ''  # No issues - return empty to fall back to standard section
        
        issues = diag_report.get('issues', [])
        ca_status_dict = ca_status or {}
        root_info = ca_status_dict.get('root', {}) if isinstance(ca_status_dict, dict) else {}
        server_info = ca_status_dict.get('server', {}) if isinstance(ca_status_dict, dict) else {}
        
        # Determine issue type and priority
        issue_type = None
        issue_severity = 'warning'
        issue_icon = '[!]'  # ASCII warning indicator
        issue_title = ''
        issue_summary = ''
        primary_action = ''
        primary_action_url = ''
        
        # Check for root certificate missing/invalid (highest priority)
        root_present = root_info.get('present', False) if isinstance(root_info, dict) else False
        if not root_present:
            issue_type = 'root_missing'
            issue_severity = 'critical'
            issue_icon = '[ERROR]'  # ASCII error indicator
            issue_title = 'Managed CA Root Certificate Missing'
            issue_summary = 'The managed CA root certificate cannot be found or is invalid. The root must be recreated and re-imported into Firefox.'
            primary_action = 'Recreate Root Certificate'
            primary_action_url = '/ca/enable'  # Trigger root recreation
        
        # Check for server certificate expired
        elif any(i.get('category') == 'certificate_expiry' for i in issues):
            issue_type = 'server_expired'
            issue_severity = 'info'
            issue_icon = '[i]'  # ASCII info indicator
            issue_title = 'Server Certificate Needs Renewal'
            issue_summary = 'The server certificate has expired, but the managed root is still valid. Once renewed, Firefox will continue to trust it without re-importing the root.'
            primary_action = 'View Certificate Status'
            primary_action_url = '/ca/server-info.json'
        
        # Check for certificate decode/validation errors
        elif any(i.get('category') == 'certificate' and 'decode' in i.get('message', '').lower() 
                 for i in issues):
            issue_type = 'cert_invalid'
            issue_severity = 'critical'
            issue_icon = '[ERROR]'  # ASCII error indicator
            issue_title = 'Certificate Validation Error'
            issue_summary = 'The server certificate file exists but cannot be decoded or validated. The certificate will need to be regenerated.'
            primary_action = 'View Diagnostics'
            primary_action_url = '/_diag?html=1'
        
        # Check for Firefox root import needed (common case)
        elif firefox_diagnosis and firefox_diagnosis.get('profile_found'):
            # Check if Firefox has exceptions but root not in Authorities
            has_exception = len(firefox_diagnosis.get('matching_exceptions', [])) > 0
            if has_exception:
                issue_type = 'firefox_conflict'
                issue_severity = 'info'
                issue_icon = '[i]'  # ASCII info indicator
                issue_title = 'Remove Old Certificate Exception'
                issue_summary = 'Firefox has an old certificate exception that conflicts with managed CA trust. Remove it and verify the root is in Authorities.'
                primary_action = 'View Instructions'
                primary_action_url = '/_cert'
            else:
                issue_type = 'root_not_imported'
                issue_severity = 'warning'
                issue_icon = '[!]'  # ASCII warning indicator
                issue_title = 'Managed CA Root Not Trusted in Firefox'
                issue_summary = 'Firefox doesn\'t trust the managed root certificate yet. Import the root into Firefox Authorities to enable full trust.'
                primary_action = 'Download Root Certificate'
                primary_action_url = '/ca/root.crt'
        
        # Default: generic certificate issue
        else:
            issue_type = 'generic_issue'
            issue_severity = 'warning'
            issue_icon = '[!]'  # ASCII warning indicator
            issue_title = 'Certificate Issue Detected'
            issue_summary = 'A certificate issue has been detected with the managed CA setup.'
            primary_action = 'View Diagnostics'
            primary_action_url = '/_diag?html=1'
        
        # Build progressive disclosure HTML
        root_subject = provider.get('root_subject', 'CN=MediLink Managed Root CA')
        server_subject = provider.get('server_subject', 'CN=127.0.0.1')
        san_list = provider.get('san', ['127.0.0.1', 'localhost'])
        san_display = ', '.join(san_list) if isinstance(san_list, list) else str(san_list)
        
        # Determine styling based on severity
        border_color = '#dc2626' if issue_severity == 'critical' else '#f0ad4e' if issue_severity == 'warning' else '#3B2323'
        bg_color = '#fdecea' if issue_severity == 'critical' else '#fff4e6' if issue_severity == 'warning' else '#f0f4ff'
        text_color = '#dc2626' if issue_severity == 'critical' else '#8b4513' if issue_severity == 'warning' else '#3B2323'
        
        # Build step-by-step guidance based on issue type
        steps_html = ''
        technical_html = ''
        
        if issue_type == 'root_not_imported':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>Download the managed root certificate using the button above</li>
                <li>In Firefox, go to <strong>Options &gt; Privacy &amp; Security &gt; Certificates &gt; View Certificates</strong></li>
                <li>Click the <strong>"Authorities"</strong> tab</li>
                <li>Click <strong>"Import"</strong> and select the downloaded root.crt file</li>
                <li>Check the box for <strong>"Trust this CA to identify websites"</strong> and click OK</li>
                <li>Close <strong>all</strong> Firefox windows completely</li>
                <li>Wait 5 seconds, then reopen Firefox and try MediLink again</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Note:</strong> After importing the root, Firefox will trust all certificates signed by this managed CA, eliminating the need for individual exceptions.</p>
            """
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Root Subject:</td><td>{root_subject}</td></tr>
                <tr><td style="font-weight: bold;">Server Subject:</td><td>{server_subject}</td></tr>
                <tr><td style="font-weight: bold;">SubjectAltName:</td><td>{san}</td></tr>
                <tr><td style="font-weight: bold;">Root Expires:</td><td>{root_expiry}</td></tr>
                <tr><td style="font-weight: bold;">Storage Location:</td><td>{storage_path}</td></tr>
            </table>
            """.format(
                root_subject=root_subject,
                server_subject=server_subject,
                san=san_display,
                root_expiry=root_info.get('notAfter', 'Unknown') if isinstance(root_info, dict) else 'Unknown',
                storage_path=ca_status_dict.get('storage', 'Unknown') if isinstance(ca_status_dict, dict) else 'Unknown'
            )
        
        elif issue_type == 'server_expired':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>The server certificate has expired and needs to be renewed</li>
                <li>Since the root is still trusted, Firefox will automatically accept the new server certificate</li>
                <li>Restart the MediLink helper server to trigger automatic certificate renewal</li>
                <li>No need to re-import the root or change Firefox settings</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Good News:</strong> Because the managed root is already trusted, you won't see certificate warnings after renewal.</p>
            """
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Current Cert Expiry:</td><td>{server_expiry}</td></tr>
                <tr><td style="font-weight: bold;">Root Still Valid:</td><td>{root_expiry}</td></tr>
                <tr><td style="font-weight: bold;">Auto-Renewal:</td><td>Automatic on server restart</td></tr>
            </table>
            """.format(
                server_expiry=server_info.get('notAfter', 'Unknown') if isinstance(server_info, dict) else 'Unknown',
                root_expiry=root_info.get('notAfter', 'Unknown') if isinstance(root_info, dict) else 'Unknown'
            )
        
        elif issue_type == 'firefox_conflict':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>In Firefox, go to <strong>Options &gt; Privacy &amp; Security &gt; Certificates &gt; View Certificates</strong></li>
                <li>Click the <strong>"Servers"</strong> tab</li>
                <li>Find and remove any entries for <code>127.0.0.1:{port}</code></li>
                <li>Click the <strong>"Authorities"</strong> tab</li>
                <li>Verify that the MediLink managed root is present and trusted</li>
                <li>If root is missing, download and import it using the steps in the "Root Not Imported" guidance</li>
                <li>Close all Firefox windows and restart Firefox</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Why this happens:</strong> When migrating from self-signed to managed CA, old server exceptions can conflict with root trust. Removing the server exception allows root trust to work properly.</p>
            """.format(port=server_port)
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Server Port:</td><td>{port}</td></tr>
                <tr><td style="font-weight: bold;">Root Subject:</td><td>{root_subject}</td></tr>
                <tr><td style="font-weight: bold;">Firefox Profile:</td><td>{profile_status}</td></tr>
            </table>
            """.format(
                port=server_port,
                root_subject=root_subject,
                profile_status='Found' if (firefox_diagnosis and firefox_diagnosis.get('profile_found')) else 'Not found'
            )
        
        elif issue_type == 'cert_invalid':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>The server certificate file cannot be decoded or validated</li>
                <li>This usually means the certificate file is corrupted or in an invalid format</li>
                <li>Restart the MediLink helper server to regenerate the certificate</li>
                <li>If the issue persists, you may need to recreate the managed CA root</li>
                <li>Check the diagnostics page for detailed error messages</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Note:</strong> Certificate regeneration will create new certificates. If you had previously imported the root into Firefox, you may need to re-import it.</p>
            """
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Root Subject:</td><td>{root_subject}</td></tr>
                <tr><td style="font-weight: bold;">Server Subject:</td><td>{server_subject}</td></tr>
                <tr><td style="font-weight: bold;">Storage Location:</td><td>{storage_path}</td></tr>
                <tr><td style="font-weight: bold;">Action:</td><td>Certificate regeneration required</td></tr>
            </table>
            """.format(
                root_subject=root_subject,
                server_subject=server_subject,
                storage_path=ca_status_dict.get('storage', 'Unknown') if isinstance(ca_status_dict, dict) else 'Unknown'
            )
        
        elif issue_type == 'root_missing':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>The managed CA root certificate needs to be recreated</li>
                <li>Click the button above to recreate the root certificate</li>
                <li>After recreation, download the new root certificate</li>
                <li>Import the new root into Firefox Authorities (see "Root Not Imported" steps)</li>
                <li>Close all Firefox windows and restart Firefox</li>
                <li>The server certificate will be automatically re-issued with the new root</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Important:</strong> After recreating the root, you must re-import it in Firefox. The old root import will no longer work.</p>
            """
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Root Status:</td><td>Missing or invalid</td></tr>
                <tr><td style="font-weight: bold;">Storage Location:</td><td>{storage_path}</td></tr>
                <tr><td style="font-weight: bold;">Expected Subject:</td><td>{root_subject}</td></tr>
                <tr><td style="font-weight: bold;">Action:</td><td>Root recreation required</td></tr>
            </table>
            """.format(
                storage_path=ca_status_dict.get('storage', 'Unknown') if isinstance(ca_status_dict, dict) else 'Unknown',
                root_subject=root_subject
            )
        
        elif issue_type == 'generic_issue':
            steps_html = """
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>Review the diagnostic information using the button above</li>
                <li>Check for specific error messages or warnings</li>
                <li>Try restarting the MediLink helper server</li>
                <li>If the issue persists, check the managed CA status page</li>
                <li>Contact support with diagnostic information if needed</li>
            </ol>
            <p style="margin-top: 12px;"><strong>Tip:</strong> The diagnostics page provides detailed information about the detected issues.</p>
            """
            
            technical_html = """
            <table style="width: 100%; margin-top: 12px; font-size: 0.9em;">
                <tr><td style="font-weight: bold; width: 40%;">Issue Type:</td><td>Generic certificate issue</td></tr>
                <tr><td style="font-weight: bold;">Mode:</td><td>Managed CA</td></tr>
                <tr><td style="font-weight: bold;">Storage Location:</td><td>{storage_path}</td></tr>
                <tr><td style="font-weight: bold;">Action:</td><td>Review diagnostics for details</td></tr>
            </table>
            """.format(
                storage_path=ca_status_dict.get('storage', 'Unknown') if isinstance(ca_status_dict, dict) else 'Unknown'
            )
        
        # Build the complete HTML structure (XP-compatible: no flexbox, no gap, ASCII-only)
        html = """
        <div class="managed-ca-guidance" data-issue-type="{issue_type}" style="border: 2px solid {border_color}; border-radius: 4px; padding: 16px; margin: 16px 0; background: {bg_color};">
            <div class="guidance-summary" style="overflow: hidden;">
                <div class="guidance-icon" style="float: left; font-size: 20px; font-weight: bold; width: 40px; margin-right: 12px;">{icon}</div>
                <div class="guidance-content" style="overflow: hidden;">
                    <h4 style="margin-top: 0; margin-bottom: 8px; color: {text_color};">{title}</h4>
                    <p style="margin: 0 0 12px 0;">{summary}</p>
                    <div class="guidance-actions" style="margin-top: 12px;">
                        <a href="{action_url}" class="btn" style="display: inline-block; padding: 8px 16px; background: #3B2323; color: white; text-decoration: none; border-radius: 4px;">{action_text}</a>
                        <a href="/ca/server-info.json" class="btn secondary" style="display: inline-block; padding: 8px 16px; background: #6b5b5b; color: white; text-decoration: none; border-radius: 4px; margin-left: 8px;">View CA Status</a>
                    </div>
                </div>
            </div>
            <div style="clear: both;"></div>
            
            <details class="guidance-details" style="margin-top: 12px; border-top: 1px solid #e0e0e0; padding-top: 12px;">
                <summary class="guidance-toggle" style="cursor: pointer; font-weight: bold; color: #3B2323; user-select: none;">Show step-by-step instructions</summary>
                <div class="guidance-steps" style="margin-top: 12px;">
                    {steps}
                </div>
            </details>
            
            <details class="guidance-technical" style="margin-top: 12px; border-top: 1px solid #e0e0e0; padding-top: 12px;">
                <summary class="guidance-toggle" style="cursor: pointer; font-weight: bold; color: #3B2323; user-select: none;">Show technical details</summary>
                <div class="guidance-technical-content" style="margin-top: 12px; font-size: 0.9em;">
                    {technical}
                </div>
            </details>
        </div>
        """.format(
            issue_type=issue_type,
            border_color=border_color,
            bg_color=bg_color,
            text_color=text_color,
            icon=issue_icon,
            title=issue_title,
            summary=issue_summary,
            action_url=primary_action_url,
            action_text=primary_action,
            steps=steps_html,
            technical=technical_html
        )
        
        return html
        
    except Exception as e:
        # Fail gracefully - return empty string to fall back to standard section
        # Error is silently ignored to prevent breaking the page
        return ''


def _build_managed_ca_section_for_troubleshoot(certificate_provider=None, diag_report=None, 
                                               firefox_diagnosis=None, cert_info=None, 
                                               server_port=8000):
    """
    Build managed CA section for troubleshoot page - uses contextual guidance if issues detected.
    
    Args:
        certificate_provider: Certificate provider config dict
        diag_report: Diagnostics report with issues
        firefox_diagnosis: Firefox certificate diagnosis
        cert_info: Current certificate info
        server_port: Server port number
    
    Returns:
        str: HTML for managed CA section (contextual or standard)
    """
    try:
        provider = certificate_provider or {}
        mode = (provider.get('mode') or '').lower()
        
        # If managed CA is active and issues are detected, use contextual guidance
        if mode == 'managed_ca' and diag_report and diag_report.get('issues'):
            ca_status = provider.get('status', {}) if isinstance(provider, dict) else {}
            contextual = build_managed_ca_contextual_guidance(
                certificate_provider=provider,
                diag_report=diag_report,
                firefox_diagnosis=firefox_diagnosis,
                ca_status=ca_status,
                cert_info=cert_info,
                server_port=server_port
            )
            if contextual:
                return contextual
        
        # Fall back to standard section (no issues, or not managed CA, or contextual failed)
        return _build_managed_ca_section(certificate_provider, server_port)
    except Exception:
        # Fall back to standard section on any error
        return _build_managed_ca_section(certificate_provider, server_port)


def _build_managed_ca_section(certificate_provider, port):
    try:
        provider = certificate_provider or {}
        mode = (provider.get('mode') or '').lower()
        san = provider.get('san') or ['127.0.0.1', 'localhost']
        san_display = ', '.join(san)
        root_subject = provider.get('root_subject', 'CN=MediLink Managed Root CA')
        server_subject = provider.get('server_subject', 'CN=127.0.0.1')
        if mode == 'managed_ca':
            return """
            <div class="warning" style="border-color:#3B2323;background:#f0f4ff;">
                <h4>Managed Certificate Authority Active</h4>
                <p>This workstation now trusts a MediLink-managed root. If Firefox still complains:</p>
                <div class="step"><span class="step-num">Step 1:</span> Download the root again if needed <a href="/ca/root.crt" class="btn" style="padding:6px 12px;">Download</a></div>
                <div class="step"><span class="step-num">Step 2:</span> In Firefox, go to Options → Privacy &amp; Security → Certificates → View Certificates → Authorities and confirm the MediLink root is present. Import if missing and check “Trust this CA to identify websites”.</div>
                <div class="step"><span class="step-num">Step 3:</span> Close <strong>all</strong> Firefox windows, wait five seconds, then reopen and retry MediLink.</div>
                <div class="step"><span class="step-num">Step 4:</span> If prompts persist, restart the MediLink helper so it reissues the managed server certificate.</div>
                <p style="margin-top:12px; font-size:0.9em;">Root Subject: {root_subject}<br/>Server Subject: {server_subject}<br/>SAN: {san}</p>
                <p style="margin-top:12px;"><a href="/ca/server-info.json" class="btn secondary" style="padding:6px 12px;">View CA Status JSON</a></p>
            </div>
            """.format(root_subject=root_subject, server_subject=server_subject, san=san_display)
        return """
        <div class="warning" style="border-color:#3B2323;background:#fffbea;">
            <h4>Escalate to Managed Certificate Authority</h4>
            <p>If Firefox refuses to honor certificate exceptions, install a MediLink-managed root once and skip future prompts.</p>
            <div class="step"><span class="step-num">Option:</span> Click the button below to prepare the managed CA workflow. You will then import the root in Firefox and restart the browser.</div>
            <button id="enable-managed-ca" class="btn" style="padding:8px 16px;">Prepare Managed CA</button>
            <a href="/ca/root.crt" class="btn secondary" style="padding:8px 16px;">Download Root</a>
            <div id="managed-ca-enable-status" style="margin-top:12px;font-size:0.9em;color:#3B2323;"></div>
        </div>
        <script>
        (function() {{
            var btn = document.getElementById('enable-managed-ca');
            var statusNode = document.getElementById('managed-ca-enable-status');
            if (!btn) return;
            btn.addEventListener('click', function() {{
                btn.disabled = true;
                statusNode.textContent = 'Preparing managed CA...';
                fetch('/ca/enable', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{mode: 'managed_ca'}})
                }}).then(function(res) {{ return res.json(); }}).then(function(payload) {{
                    if (payload.success) {{
                        statusNode.textContent = 'Managed CA prepared. Download the root, import it under Authorities, then restart Firefox.';
                    }} else {{
                        statusNode.textContent = 'Unable to enable managed CA: ' + (payload.error || 'Unknown error');
                        btn.disabled = false;
                    }}
                }}).catch(function(err) {{
                    statusNode.textContent = 'Request failed: ' + err;
                    btn.disabled = false;
                }});
            }});
        }})();
        </script>
        """.format()
    except Exception:
        return ''


def build_diagnostics_html(diag_report, server_port=8000, certificate_auto_fixed=False, restart_required=False):
    """Build a comprehensive diagnostics HTML page.
    
    Args:
        diag_report: Dictionary from ConnectionDiagnostics.run_full_diagnostics()
        server_port: Server port number
        certificate_auto_fixed: Whether certificate was auto-fixed (from diag_payload)
        restart_required: Whether server restart is required (from diag_payload)
    
    Returns:
        str: HTML content for diagnostics page
    """
    # Defensive check for None or non-dict diag_report
    if not diag_report or not isinstance(diag_report, dict):
        diag_report = {}
    
    env = diag_report.get('environment', {})
    issues = diag_report.get('issues', [])
    warnings = diag_report.get('warnings', [])
    summary = diag_report.get('summary', {})
    fixes_attempted = diag_report.get('fixes_attempted', [])
    fixes_successful = diag_report.get('fixes_successful', [])
    
    # Check user_action_required from diag_report if flags not provided
    user_action = diag_report.get('user_action_required', {})
    if not certificate_auto_fixed and user_action.get('requires_restart'):
        certificate_auto_fixed = True
        restart_required = True
    
    # Build environment section
    env_rows = ""
    env_items = [
        ('Operating System', env.get('os_full', 'Unknown')),
        ('Python Version', '.'.join(str(x) for x in env.get('python_version_info', []))),
        ('OpenSSL Version', env.get('ssl_version', 'Unknown')),
        ('TLS Support', ', '.join(env.get('tls_versions', []))),
        ('Windows XP', 'Yes' if env.get('is_windows_xp') else 'No'),
    ]
    for label, value in env_items:
        env_rows += "<tr><td class='label'>{}</td><td>{}</td></tr>".format(label, value)
    
    # Build issues section
    issues_html = ""
    if issues:
        issues_html = "<h3>Critical Issues</h3><ul class='issues'>"
        for issue in issues:
            issues_html += "<li class='critical'><strong>{}</strong>".format(issue.get('message', ''))
            if issue.get('detail'):
                issues_html += "<br><small>{}</small>".format(issue.get('detail'))
            if issue.get('suggestion'):
                issues_html += "<br><em>Suggestion: {}</em>".format(issue.get('suggestion'))
            issues_html += "</li>"
        issues_html += "</ul>"
    else:
        issues_html = "<p class='success'>No critical issues detected.</p>"
    
    # Build warnings section
    warnings_html = ""
    if warnings:
        warnings_html = "<h3>Warnings &amp; Notes</h3><ul class='warnings'>"
        for warning in warnings:
            warnings_html += "<li><strong>{}</strong>".format(warning.get('message', ''))
            if warning.get('suggestion'):
                warnings_html += "<br><small>{}</small>".format(warning.get('suggestion'))
            warnings_html += "</li>"
        warnings_html += "</ul>"
    
    # Build fixes section
    fixes_html = ""
    if fixes_attempted:
        fixes_html = "<h3>Auto-Fix Attempts</h3><ul class='fixes'>"
        for fix in fixes_attempted:
            status = "SUCCESS" if fix in fixes_successful else "FAILED"
            status_class = "success" if fix in fixes_successful else "failed"
            fixes_html += "<li class='{}'>{}: {}</li>".format(status_class, fix, status)
        fixes_html += "</ul>"
    
    # Build certificate auto-fix notification
    cert_fix_html = ""
    if certificate_auto_fixed or restart_required:
        cert_fix_html = """
        <div class="info-section" style="background: #e8f7ee; border: 2px solid #30a46c; margin: 20px 0; padding: 16px;">
            <h3 style="color: #1f5132; margin-top: 0;">[i] Certificate Auto-Fixed</h3>
            <p><strong>Status:</strong> Certificate issues have been automatically resolved.</p>
            <p><strong>Action Required:</strong> Server restart needed for changes to take effect.</p>
            <ol style="margin: 12px 0; padding-left: 20px;">
                <li>Close the current MediLink server (if running)</li>
                <li>Restart the MediLink application</li>
                <li>Update Firefox certificate exception if needed (navigate to <a href="https://127.0.0.1:{port}/_cert">https://127.0.0.1:{port}/_cert</a>)</li>
            </ol>
        </div>
        """.format(port=server_port)
    
    # Status indicator
    can_start = summary.get('can_start_server', False)
    status_class = 'status-ok' if can_start else 'status-error'
    status_text = 'Server Ready' if can_start else 'Issues Detected'
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MediLink Diagnostics</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f3e8; color: #2b2b2b; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border: 1px solid #ccc; padding: 24px; }}
        h1 {{ color: #3B2323; margin-top: 0; }}
        h2 {{ color: #3B2323; border-bottom: 2px solid #3B2323; padding-bottom: 8px; }}
        h3 {{ color: #4E3B3B; margin-top: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        td {{ padding: 8px; border-bottom: 1px solid #e0e0e0; }}
        td.label {{ font-weight: bold; width: 40%; color: #666; }}
        ul {{ padding-left: 20px; }}
        ul.issues li {{ margin: 12px 0; padding: 12px; background: #fdecea; border-left: 4px solid #dc2626; }}
        ul.issues li.critical {{ background: #fdecea; }}
        ul.warnings li {{ margin: 8px 0; padding: 8px; background: #fff4e6; border-left: 4px solid #f0ad4e; }}
        ul.fixes li {{ margin: 4px 0; }}
        ul.fixes li.success {{ color: #1f5132; }}
        ul.fixes li.failed {{ color: #dc2626; }}
        .status-badge {{ display: inline-block; padding: 12px 24px; font-weight: bold; font-size: 1.1em; margin: 16px 0; }}
        .status-ok {{ background: #e8f7ee; color: #1f5132; border: 2px solid #30a46c; }}
        .status-error {{ background: #fdecea; color: #dc2626; border: 2px solid #dc2626; }}
        .success {{ color: #1f5132; }}
        .actions {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e0e0e0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #3B2323; color: white; text-decoration: none; margin-right: 8px; }}
        .btn:hover {{ background: #4E3B3B; }}
        .btn.secondary {{ background: #6b5b5b; }}
        .firefox-help {{ margin-top: 24px; padding: 16px; background: #f8f7f5; border: 1px solid #d9cbbd; }}
        .firefox-help h4 {{ margin-top: 0; color: #3B2323; }}
        .firefox-help ol {{ margin: 0; padding-left: 20px; }}
        .firefox-help li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MediLink Connection Diagnostics</h1>
        
        <div class="status-badge {status_class}">{status_text}</div>
        
        <h2>Environment</h2>
        <table>{env_rows}</table>
        
        <h2>Diagnostic Results</h2>
        {cert_fix_html}
        {issues_html}
        {warnings_html}
        {fixes_html}
        
        <div class="firefox-help">
            <h4>Firefox Troubleshooting (Windows XP)</h4>
            <p>If you're having trouble connecting from Firefox:</p>
            <ol>
                <li><strong>Certificate Trust:</strong> Open <a href="https://127.0.0.1:{port}" target="_blank">https://127.0.0.1:{port}</a> directly, click "Advanced", then "Add Exception".</li>
                <li><strong>Clear Certificate Cache:</strong> In Firefox, go to Options &gt; Privacy &amp; Security &gt; Certificates &gt; View Certificates &gt; Servers tab, remove any 127.0.0.1 entries.</li>
                <li><strong>Check Firewall:</strong> Ensure Windows Firewall allows Python on port {port}.</li>
                <li><strong>TLS Settings:</strong> In <code>about:config</code>, check <code>security.tls.version.min</code> is set to 1 (TLS 1.0).</li>
            </ol>
        </div>
        
        <div class="actions">
            <a href="/" class="btn">Back to Status</a>
            <a href="/_cert" class="btn secondary">View Certificate</a>
            <a href="/_diag?refresh=1" class="btn secondary">Refresh Diagnostics</a>
        </div>
    </div>
</body>
</html>    """.format(
        status_class=status_class,
        status_text=status_text,
        env_rows=env_rows,
        cert_fix_html=cert_fix_html,
        issues_html=issues_html,
        warnings_html=warnings_html,
        fixes_html=fixes_html,
        port=server_port
    )
    return html


def build_connection_error_html(error_type, error_message, suggestions=None, server_port=8000):
    """Build an error page for connection/SSL issues.
    
    Args:
        error_type: Type of error (e.g., 'ssl_error', 'connection_refused')
        error_message: Human-readable error message
        suggestions: List of suggestion strings
        server_port: Server port number
    
    Returns:
        str: HTML content for error page
    """
    suggestions = suggestions or []
    
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<h3>Suggested Actions</h3><ol>"
        for suggestion in suggestions:
            suggestions_html += "<li>{}</li>".format(suggestion)
        suggestions_html += "</ol>"
    
    # Common troubleshooting steps
    common_steps = """
        <h3>Common Troubleshooting Steps</h3>
        <ol>
            <li><strong>Trust the certificate:</strong> Navigate to <a href="https://127.0.0.1:{port}">https://127.0.0.1:{port}</a> directly and accept the security warning.</li>
            <li><strong>Check if server is running:</strong> Look for the Python console window.</li>
            <li><strong>Restart the server:</strong> Close and reopen the MediLink application.</li>
            <li><strong>Check firewall:</strong> Ensure Python is allowed through Windows Firewall.</li>
        </ol>
    """.format(port=server_port)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Connection Error - MediLink</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f3e8; color: #2b2b2b; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border: 1px solid #ccc; padding: 24px; }}
        h1 {{ color: #dc2626; margin-top: 0; }}
        .error-box {{ background: #fdecea; border: 1px solid #dc2626; padding: 16px; margin: 16px 0; }}
        .error-type {{ font-weight: bold; color: #dc2626; }}
        .error-message {{ margin-top: 8px; }}
        h3 {{ color: #3B2323; margin-top: 24px; }}
        ol {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
        .actions {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e0e0e0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #3B2323; color: white; text-decoration: none; margin-right: 8px; }}
        .btn:hover {{ background: #4E3B3B; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Connection Error</h1>
        
        <div class="error-box">
            <div class="error-type">{error_type}</div>
            <div class="error-message">{error_message}</div>
        </div>
        
        {suggestions_html}
        {common_steps}
        
        <div class="actions">
            <a href="/" class="btn">Try Again</a>
            <a href="/_diag" class="btn">Run Diagnostics</a>
        </div>
    </div>
</body>
</html>""".format(
        error_type=error_type,
        error_message=error_message,
        suggestions_html=suggestions_html,
        common_steps=common_steps
    )
    return html


def build_troubleshoot_html(diag_report=None, firefox_notes=None, browser_hints=None, server_port=8000, certificate_provider=None, firefox_diagnosis=None, cert_info=None):
    """Build comprehensive troubleshooting HTML page.
    
    Args:
        diag_report: Optional diagnostics report dict
        firefox_notes: Optional Firefox compatibility notes dict
        browser_hints: Optional browser error hints dict
        server_port: Server port number
        certificate_provider: Optional certificate provider config dict
        firefox_diagnosis: Optional Firefox certificate diagnosis results
        cert_info: Optional current certificate information
    
    Returns:
        str: HTML content for troubleshooting page
    """
    # Build environment info section
    env_info = ""
    if diag_report and 'environment' in diag_report:
        env = diag_report['environment']
        env_info = """
        <table>
            <tr><td><strong>Operating System:</strong></td><td>{os}</td></tr>
            <tr><td><strong>Python Version:</strong></td><td>{python}</td></tr>
            <tr><td><strong>OpenSSL Version:</strong></td><td>{ssl}</td></tr>
            <tr><td><strong>TLS Support:</strong></td><td>{tls}</td></tr>
            <tr><td><strong>Windows XP:</strong></td><td>{xp}</td></tr>
        </table>
        """.format(
            os=env.get('os_full', 'Unknown'),
            python='.'.join(str(x) for x in env.get('python_version_info', [])),
            ssl=env.get('ssl_version', 'Unknown'),
            tls=', '.join(env.get('tls_versions', [])),
            xp='Yes' if env.get('is_windows_xp') else 'No'
        )
    
    # Build issues section
    issues_html = ""
    if diag_report and diag_report.get('issues'):
        issues_html = "<h3>Detected Issues</h3><ul>"
        for issue in diag_report['issues']:
            issues_html += "<li><strong>{}</strong>: {}</li>".format(
                issue.get('category', 'Unknown'),
                issue.get('message', '')
            )
        issues_html += "</ul>"
    
    # Build browser hints section
    hints_html = ""
    if browser_hints:
        hints_html = "<h3>Common Browser Error Messages</h3><ul>"
        for error_code, hint in browser_hints.items():
            hints_html += "<li><strong>{}</strong>: {}<br><em>Solution: {}</em></li>".format(
                error_code.upper().replace('_', ' '),
                hint.get('meaning', ''),
                hint.get('solution', '')
            )
        hints_html += "</ul>"
    
    # Build Firefox notes section
    firefox_html = ""
    if firefox_notes and firefox_notes.get('notes'):
        firefox_html = "<h3>Firefox on Windows XP Notes</h3><ul>"
        for note in firefox_notes['notes']:
            if note and note.strip():
                firefox_html += "<li>{}</li>".format(note)
        firefox_html += "</ul>"
    
    # Build certificate auto-fix notification if applicable
    cert_fix_html = ""
    if diag_report and diag_report.get('user_action_required'):
        user_action = diag_report['user_action_required']
        if user_action.get('requires_restart'):
            cert_fix_html = """
            <div class="quick-fix" style="background: #e8f7ee; border: 2px solid #30a46c;">
                <h4 style="color: #1f5132;">[i] Certificate Auto-Fixed</h4>
                <p><strong>Status:</strong> Certificate issues have been automatically resolved.</p>
                <p><strong>Action Required:</strong> Server restart needed for changes to take effect.</p>
                <ol style="margin: 12px 0; padding-left: 20px;">
                    <li>Close the current MediLink server (if running)</li>
                    <li>Restart the MediLink application</li>
                    <li>Update Firefox certificate exception if needed (navigate to <a href="https://127.0.0.1:{port}/_cert">https://127.0.0.1:{port}/_cert</a>)</li>
                </ol>
            </div>
            """.format(port=server_port)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MediLink Troubleshooting Guide</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f3e8; color: #2b2b2b; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border: 1px solid #ccc; padding: 24px; }}
        h1 {{ color: #3B2323; margin-top: 0; border-bottom: 3px solid #3B2323; padding-bottom: 12px; }}
        h2 {{ color: #4E3B3B; border-bottom: 1px solid #d9cbbd; padding-bottom: 8px; margin-top: 32px; }}
        h3 {{ color: #5E4B4B; margin-top: 24px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }}
        ul {{ padding-left: 24px; }}
        li {{ margin: 8px 0; }}
        .quick-fix {{ background: #e8f7ee; border: 1px solid #30a46c; padding: 16px; margin: 16px 0; border-radius: 4px; }}
        .quick-fix h4 {{ margin-top: 0; color: #1f5132; }}
        .warning {{ background: #fff4e6; border: 1px solid #f0ad4e; padding: 16px; margin: 16px 0; border-radius: 4px; }}
        .warning h4 {{ margin-top: 0; color: #8b4513; }}
        .step {{ background: #f8f7f5; padding: 12px; margin: 8px 0; border-left: 4px solid #3B2323; }}
        .step-num {{ font-weight: bold; color: #3B2323; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #3B2323; color: white; text-decoration: none; margin: 8px 8px 8px 0; border-radius: 4px; }}
        .btn:hover {{ background: #4E3B3B; }}
        .btn.secondary {{ background: #6b5b5b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MediLink Connection Troubleshooting</h1>
        
        <div class="quick-fix">
            <h4>Quick Fix: Trust the Certificate</h4>
            <p>Most connection issues are caused by the browser not trusting the local server's self-signed certificate.</p>
            <div class="step">
                <span class="step-num">Step 1:</span> Open <a href="https://127.0.0.1:{port}" target="_blank">https://127.0.0.1:{port}</a> directly in your browser
            </div>
            <div class="step">
                <span class="step-num">Step 2:</span> Click "Advanced" or "More Information" on the warning page
            </div>
            <div class="step">
                <span class="step-num">Step 3:</span> Click "Add Exception" or "Accept the Risk and Continue"
            </div>
            <div class="step">
                <span class="step-num">Step 4:</span> Return to the MediLink app and try again
            </div>
        </div>

        {managed_ca_section}
        
        {cert_fix_html}
        
        <h2>System Environment</h2>
        {env_info}
        
        {issues_html}
        
        <h2>Troubleshooting Steps</h2>
        
        <h3>1. Certificate Trust Issues</h3>
        <p>If you see "Your connection is not private" or "SEC_ERROR_UNKNOWN_ISSUER":</p>
        <ul>
            <li>This is <strong>normal</strong> for the local development server</li>
            <li>The server uses a self-signed certificate that browsers don't trust by default</li>
            <li>You need to add a security exception to proceed</li>
        </ul>
        
        <h3>2. Connection Refused / Unable to Connect</h3>
        <p>If the browser can't connect at all:</p>
        <ul>
            <li>Check that the Python server window is still open and running</li>
            <li>Look for error messages in the Python console</li>
            <li>Try restarting the MediLink application</li>
            <li>Check if Windows Firewall is blocking Python</li>
        </ul>
        
        <h3>3. Firefox-Specific Issues (Windows XP)</h3>
        {firefox_html}
        
        <div class="warning">
            <h4>Firefox Certificate Cache</h4>
            <p>Firefox remembers certificate exceptions. If the certificate was regenerated, you may need to:</p>
            <ol>
                <li>Open Firefox Options/Preferences</li>
                <li>Go to Privacy &amp; Security &gt; Certificates &gt; View Certificates</li>
                <li>In the "Servers" tab, find and remove any entries for <code>127.0.0.1</code></li>
                <li>Try connecting again and accept the new certificate</li>
            </ol>
        </div>
        
        <h3>4. Firewall Configuration</h3>
        <p>If Windows Firewall is blocking the connection:</p>
        <ul>
            <li>Go to Control Panel &gt; Windows Firewall</li>
            <li>Click "Allow a program through Windows Firewall"</li>
            <li>Find Python in the list and enable it for private networks</li>
            <li>If Python isn't listed, click "Allow another program" and browse to python.exe</li>
        </ul>
        
        {hints_html}
        
        <h2>Diagnostic Tools</h2>
        <p>Use these tools to get more information about the server status:</p>
        <a href="/_diag?html=1" class="btn">Full Diagnostics</a>
        <a href="/_cert" class="btn secondary">View Certificate</a>
        <a href="/_health" class="btn secondary">Health Check</a>
        <a href="/" class="btn secondary">Server Status</a>
        
        <h2>Still Having Issues?</h2>
        <p>If none of the above solutions work:</p>
        <ol>
            <li>Check the Python console for error messages</li>
            <li>Try a different browser (Chrome, Edge, or Internet Explorer)</li>
            <li>Restart your computer and try again</li>
            <li>Contact support with the diagnostics information from the link above</li>
        </ol>
    </div>
</body>
    </html>""".format(
        port=server_port,
        cert_fix_html=cert_fix_html,
        env_info=env_info if env_info else "<p>Environment information not available.</p>",
        issues_html=issues_html if issues_html else "<p>No issues detected.</p>",
        firefox_html=firefox_html if firefox_html else "",
        hints_html=hints_html if hints_html else "",
        managed_ca_section=_build_managed_ca_section_for_troubleshoot(certificate_provider, diag_report, firefox_diagnosis, cert_info, server_port)
    )
    return html


def build_simple_error_html(title, message, server_port=8000):
    """Build a simple error HTML page for fallback cases.
    
    Args:
        title: Page title
        message: Error message to display
        server_port: Server port for links
    
    Returns:
        str: HTML content
    """
    # Escape HTML in message
    safe_message = str(message).replace('<', '&lt;').replace('>', '&gt;')
    
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f3e8; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 24px; border: 1px solid #ccc; }}
        h1 {{ color: #3B2323; }}
        .error {{ background: #fdecea; padding: 12px; border-left: 4px solid #dc2626; margin: 16px 0; }}
        a {{ color: #3B2323; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="error">{message}</div>
        <p><a href="/_diag">Run diagnostics</a> | <a href="/_cert">View certificate</a> | <a href="/">Back to status</a></p>
    </div>
</body>
</html>""".format(title=title, message=safe_message, port=server_port)


def build_fallback_status_html(server_port=8000):
    """Build a minimal fallback status page when main build fails.
    
    Args:
        server_port: Server port number
    
    Returns:
        str: HTML content
    """
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MediLink Local Server</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f3e8; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 24px; border: 1px solid #ccc; }}
        h1 {{ color: #3B2323; }}
        a {{ color: #3B2323; margin-right: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MediLink Local Server</h1>
        <p>HTTPS server is running on port {port}</p>
        <p>
            <a href="/_diag">Run diagnostics</a>
            <a href="/_cert">View certificate</a>
            <a href="/_troubleshoot">Troubleshooting</a>
        </p>
    </div>
</body>
</html>""".format(port=server_port)


def build_fallback_cert_html(error_message, server_port=8000):
    """Build a fallback certificate page when parsing fails.
    
    Args:
        error_message: Error that occurred
        server_port: Server port number
    
    Returns:
        str: HTML content
    """
    safe_error = str(error_message).replace('<', '&lt;').replace('>', '&gt;')
    
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Certificate Info - MediLink</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f3e8; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 24px; border: 1px solid #ccc; }}
        h1 {{ color: #3B2323; }}
        .error {{ background: #fff4e6; padding: 12px; border-left: 4px solid #f0ad4e; margin: 16px 0; }}
        ol {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Certificate Information</h1>
        <div class="error">
            <strong>Note:</strong> Unable to decode certificate details.<br>
            <small>{error}</small>
        </div>
        <h3>How to trust this certificate</h3>
        <ol>
            <li>Click the "Advanced" button in your browser's warning page.</li>
            <li>Select "Accept the risk" to trust https://127.0.0.1:{port}.</li>
            <li>Return to the MediLink web app and try again.</li>
        </ol>
        <p><a href="/_diag">Run diagnostics</a> | <a href="/">Back to status</a></p>
    </div>
</body>
</html>""".format(error=safe_error, port=server_port)


