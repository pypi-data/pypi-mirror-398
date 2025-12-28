"""
PDF Generator Module
Generates beautiful, production-quality PDF documentation with clean design
Supports both REST API and WebSocket documentation
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem, HRFlowable,
        KeepTogether, Flowable, Preformatted
    )
    from reportlab.graphics.shapes import Drawing, Rect, Line
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from .parser import AppAPIInfo, EndpointInfo, FieldInfo


class CodeBox(Flowable):
    """A styled code box with language label"""
    
    def __init__(self, code: str, language: str = "json", width: float = 450):
        Flowable.__init__(self)
        self.code = code
        self.language = language
        self.width = width
        self.padding = 12
        self.line_height = 14
        self.font_size = 9
        
        # Calculate height based on content
        lines = code.split('\n')
        self.height = len(lines) * self.line_height + (self.padding * 2) + 25
    
    def draw(self):
        # Draw outer border with rounded corners
        self.canv.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 8, stroke=1, fill=0)
        
        # Draw language label background
        label_height = 22
        self.canv.setFillColor(colors.HexColor('#f9fafb'))
        self.canv.roundRect(0, self.height - label_height, self.width, label_height, 
                           8, stroke=0, fill=1)
        
        # Draw separator line
        self.canv.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.canv.line(0, self.height - label_height, self.width, self.height - label_height)
        
        # Draw language label text
        self.canv.setFillColor(colors.HexColor('#6b7280'))
        self.canv.setFont('Helvetica', 9)
        self.canv.drawString(self.padding, self.height - 16, self.language)
        
        # Draw code content
        y = self.height - label_height - self.padding - self.font_size
        lines = self.code.split('\n')
        
        for line in lines:
            # Syntax highlighting for JSON
            if self.language == 'json':
                self._draw_json_line(line, self.padding, y)
            elif self.language == 'javascript':
                self._draw_js_line(line, self.padding, y)
            else:
                self.canv.setFillColor(colors.HexColor('#374151'))
                self.canv.setFont('Courier', self.font_size)
                self.canv.drawString(self.padding, y, line)
            y -= self.line_height
    
    def _draw_json_line(self, line: str, x: float, y: float):
        """Draw a line of JSON with syntax highlighting"""
        import re
        
        self.canv.setFont('Courier', self.font_size)
        current_x = x
        
        # Simple parsing for JSON syntax highlighting
        remaining = line
        
        while remaining:
            # Check for JSON key (quoted string followed by :)
            key_match = re.match(r'^(\s*)("[^"]*")(\s*:\s*)', remaining)
            if key_match:
                # Whitespace
                ws = key_match.group(1)
                self.canv.setFillColor(colors.black)
                self.canv.drawString(current_x, y, ws)
                current_x += self.canv.stringWidth(ws, 'Courier', self.font_size)
                
                # Key (red/maroon color)
                key = key_match.group(2)
                self.canv.setFillColor(colors.HexColor('#a31515'))
                self.canv.drawString(current_x, y, key)
                current_x += self.canv.stringWidth(key, 'Courier', self.font_size)
                
                # Colon
                colon = key_match.group(3)
                self.canv.setFillColor(colors.black)
                self.canv.drawString(current_x, y, colon)
                current_x += self.canv.stringWidth(colon, 'Courier', self.font_size)
                
                remaining = remaining[key_match.end():]
                continue
            
            # Check for string value
            str_match = re.match(r'^("[^"]*")', remaining)
            if str_match:
                val = str_match.group(1)
                self.canv.setFillColor(colors.HexColor('#22863a'))
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[str_match.end():]
                continue
            
            # Check for number
            num_match = re.match(r'^(\d+\.?\d*)', remaining)
            if num_match:
                val = num_match.group(1)
                self.canv.setFillColor(colors.HexColor('#b5651d'))  # Brown/orange for numbers
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[num_match.end():]
                continue
            
            # Check for boolean/null
            bool_match = re.match(r'^(true|false|null)', remaining)
            if bool_match:
                val = bool_match.group(1)
                self.canv.setFillColor(colors.HexColor('#7c3aed'))  # Purple
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[bool_match.end():]
                continue
            
            # Default: draw single character
            char = remaining[0]
            self.canv.setFillColor(colors.black)
            self.canv.drawString(current_x, y, char)
            current_x += self.canv.stringWidth(char, 'Courier', self.font_size)
            remaining = remaining[1:]
    
    def _draw_js_line(self, line: str, x: float, y: float):
        """Draw a line of JavaScript with syntax highlighting"""
        import re
        
        self.canv.setFont('Courier', self.font_size)
        current_x = x
        remaining = line
        
        while remaining:
            # Keywords
            kw_match = re.match(r'^(const|let|var|new|function|return)\b', remaining)
            if kw_match:
                val = kw_match.group(1)
                self.canv.setFillColor(colors.HexColor('#7c3aed'))  # Purple
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[kw_match.end():]
                continue
            
            # Variable names after const/let/var
            var_match = re.match(r'^(\w+)\s*=', remaining)
            if var_match:
                val = var_match.group(1)
                self.canv.setFillColor(colors.HexColor('#0550ae'))  # Blue
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[len(val):]
                continue
            
            # Strings
            str_match = re.match(r'^([\'"][^\'"]*[\'"])', remaining)
            if str_match:
                val = str_match.group(1)
                self.canv.setFillColor(colors.HexColor('#22863a'))  # Green
                self.canv.drawString(current_x, y, val)
                current_x += self.canv.stringWidth(val, 'Courier', self.font_size)
                remaining = remaining[str_match.end():]
                continue
            
            # Default
            char = remaining[0]
            self.canv.setFillColor(colors.black)
            self.canv.drawString(current_x, y, char)
            current_x += self.canv.stringWidth(char, 'Courier', self.font_size)
            remaining = remaining[1:]


class URLBox(Flowable):
    """A styled URL display box"""
    
    def __init__(self, label: str, url: str, width: float = 450):
        Flowable.__init__(self)
        self.label = label
        self.url = url
        self.width = width
        self.height = 24
    
    def draw(self):
        # Draw label
        self.canv.setFillColor(colors.HexColor('#1f2937'))
        self.canv.setFont('Helvetica-Bold', 11)
        self.canv.drawString(0, 6, self.label)
        
        label_width = self.canv.stringWidth(self.label, 'Helvetica-Bold', 11) + 10
        
        # Draw URL box
        url_box_width = min(self.width - label_width, 
                           self.canv.stringWidth(self.url, 'Courier', 10) + 16)
        self.canv.setStrokeColor(colors.HexColor('#d1d5db'))
        self.canv.setFillColor(colors.HexColor('#f9fafb'))
        self.canv.roundRect(label_width, 0, url_box_width, self.height, 4, stroke=1, fill=1)
        
        # Draw URL text
        self.canv.setFillColor(colors.HexColor('#374151'))
        self.canv.setFont('Courier', 10)
        self.canv.drawString(label_width + 8, 7, self.url)


class PDFGenerator:
    """
    Generates production-quality PDF documentation for APIs and WebSockets
    Clean, user-friendly design with proper syntax highlighting
    """
    
    # Theme colors - clean and professional
    PRIMARY_COLOR = colors.HexColor('#1f2937')
    ACCENT_COLOR = colors.HexColor('#3b82f6')
    TEXT_COLOR = colors.HexColor('#374151')
    MUTED_COLOR = colors.HexColor('#6b7280')
    LIGHT_BG = colors.HexColor('#f9fafb')
    BORDER_COLOR = colors.HexColor('#e5e7eb')
    SUCCESS_COLOR = colors.HexColor('#22c55e')
    WARNING_COLOR = colors.HexColor('#f59e0b')
    DANGER_COLOR = colors.HexColor('#ef4444')
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize PDF generator
        
        Args:
            config: Configuration dictionary with title, version, etc.
        """
        if not HAS_REPORTLAB:
            raise ImportError(
                "ReportLab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )
        
        self.config = config or {}
        self.title = self.config.get('TITLE', 'API Documentation')
        self.version = self.config.get('VERSION', '1.0.0')
        self.description = self.config.get('DESCRIPTION', 'Complete API Reference')
        self.contact_email = self.config.get('CONTACT_EMAIL', '')
        self.logo_path = self.config.get('LOGO_PATH', None)
        
        theme_color = self.config.get('THEME_COLOR', '#1f2937')
        if theme_color:
            self.PRIMARY_COLOR = colors.HexColor(theme_color)
        
        self.styles = self._create_styles()
        self.page_width = A4[0] - 100  # Account for margins
    
    def _create_styles(self):
        """Create custom paragraph styles for the PDF"""
        styles = getSampleStyleSheet()
        
        # Main title style
        styles.add(ParagraphStyle(
            name='DocTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=10,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
        ))
        
        # Section header (like "Overview", "Connection Lifecycle")
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=25,
            spaceAfter=12,
            fontName='Helvetica-Bold',
        ))
        
        # Subsection header (like "1. Establishing Connection")
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=18,
            spaceAfter=8,
            fontName='Helvetica-Bold',
        ))
        
        # Small header (like "Client Action:", "Server Response:")
        styles.add(ParagraphStyle(
            name='SmallHeader',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='DocBodyText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.TEXT_COLOR,
            spaceAfter=8,
            leading=16,
            alignment=TA_LEFT,
        ))
        
        # Small muted text
        styles.add(ParagraphStyle(
            name='MutedText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.MUTED_COLOR,
            spaceAfter=4,
        ))
        
        # Code inline style
        styles.add(ParagraphStyle(
            name='CodeInline',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Courier',
            textColor=self.TEXT_COLOR,
            backColor=self.LIGHT_BG,
            borderPadding=4,
        ))
        
        # Endpoint URL style
        styles.add(ParagraphStyle(
            name='EndpointURL',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Courier',
            textColor=self.PRIMARY_COLOR,
            spaceBefore=5,
            spaceAfter=10,
        ))
        
        # Feature list item
        styles.add(ParagraphStyle(
            name='FeatureItem',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            leftIndent=15,
            spaceBefore=2,
            spaceAfter=2,
            bulletIndent=5,
        ))
        
        return styles
    
    def generate(self, apps: List[AppAPIInfo], output_path: str, 
                 websocket_apps: List = None) -> str:
        """
        Generate PDF documentation
        
        Args:
            apps: List of AppAPIInfo objects with parsed API data
            output_path: Path to save the PDF file
            websocket_apps: Optional list of WebSocketAppInfo objects
            
        Returns:
            Path to the generated PDF file
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
            title=self.title,
            author='API Documentation Generator',
        )
        
        story = []
        
        # Cover page
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # Table of contents
        story.extend(self._create_toc(apps, websocket_apps))
        story.append(PageBreak())
        
        # REST API documentation
        if apps:
            for app in apps:
                story.extend(self._create_app_section(app))
                story.append(PageBreak())
        
        # WebSocket documentation
        if websocket_apps:
            for ws_app in websocket_apps:
                story.extend(self._create_websocket_section(ws_app))
                story.append(PageBreak())
        
        doc.build(story, onFirstPage=self._add_page_footer, 
                  onLaterPages=self._add_page_footer)
        
        return os.path.abspath(output_path)
    
    def _add_page_footer(self, canvas_obj, doc):
        """Add footer to each page"""
        canvas_obj.saveState()
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(self.MUTED_COLOR)
        canvas_obj.drawCentredString(doc.width / 2 + doc.leftMargin, 25, f"Page {page_num}")
        
        canvas_obj.restoreState()
    
    def _create_cover_page(self) -> List:
        """Create the cover page"""
        story = []
        
        story.append(Spacer(1, 2*inch))
        
        # Logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=1.5*inch, height=1.5*inch)
                story.append(logo)
                story.append(Spacer(1, 0.5*inch))
            except:
                pass
        
        # Title
        story.append(Paragraph(self.title, self.styles['DocTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Description
        story.append(Paragraph(self.description, self.styles['DocBodyText']))
        story.append(Spacer(1, 0.5*inch))
        
        # Version and date
        story.append(Paragraph(f"<b>Version:</b> {self.version}", self.styles['DocBodyText']))
        story.append(Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            self.styles['DocBodyText']
        ))
        
        if self.contact_email:
            story.append(Paragraph(f"<b>Contact:</b> {self.contact_email}", self.styles['DocBodyText']))
        
        return story
    
    def _create_toc(self, apps: List[AppAPIInfo], websocket_apps: List = None) -> List:
        """Create table of contents"""
        story = []
        
        story.append(Paragraph("Table of Contents", self.styles['DocTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # REST APIs
        if apps:
            story.append(Paragraph("<b>REST API Endpoints</b>", self.styles['SubsectionHeader']))
            for app in apps:
                story.append(Paragraph(f"• {app.app_label}", self.styles['DocBodyText']))
                for endpoint in app.endpoints[:5]:  # Limit for TOC
                    methods = ' | '.join(endpoint.methods)
                    story.append(Paragraph(
                        f"  - [{methods}] {endpoint.url}",
                        self.styles['MutedText']
                    ))
                if len(app.endpoints) > 5:
                    story.append(Paragraph(f"  ... and {len(app.endpoints) - 5} more", 
                                          self.styles['MutedText']))
        
        # WebSocket APIs
        if websocket_apps:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>WebSocket APIs</b>", self.styles['SubsectionHeader']))
            for ws_app in websocket_apps:
                story.append(Paragraph(f"• {ws_app.app_label}", self.styles['DocBodyText']))
                for endpoint in ws_app.endpoints:
                    story.append(Paragraph(
                        f"  - {endpoint.name}: {endpoint.url}",
                        self.styles['MutedText']
                    ))
        
        return story
    
    def _create_app_section(self, app: AppAPIInfo) -> List:
        """Create documentation section for a REST API app"""
        story = []
        
        # App header
        story.append(Paragraph(f"📦 {app.app_label}", self.styles['DocTitle']))
        
        if app.description:
            story.append(Paragraph(app.description, self.styles['DocBodyText']))
        
        story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR,
                               spaceBefore=15, spaceAfter=20))
        
        # Endpoints
        for endpoint in app.endpoints:
            story.extend(self._create_endpoint_section(endpoint))
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_endpoint_section(self, endpoint: EndpointInfo) -> List:
        """Create documentation for a single REST endpoint"""
        story = []
        
        # Method badges and URL
        methods_str = ' | '.join([f"<b>{m}</b>" for m in endpoint.methods])
        story.append(Paragraph(
            f'<font color="{self._get_method_color(endpoint.methods[0])}">{methods_str}</font>  '
            f'<font name="Courier" size="11">{endpoint.url}</font>',
            self.styles['DocBodyText']
        ))
        
        # Description
        if endpoint.description:
            story.append(Paragraph(endpoint.description, self.styles['DocBodyText']))
        
        # Authentication & Permissions
        if endpoint.authentication or endpoint.permissions:
            info_parts = []
            if endpoint.authentication:
                info_parts.append(f"<b>🔐 Auth:</b> {', '.join(endpoint.authentication)}")
            if endpoint.permissions:
                info_parts.append(f"<b>🛡️ Permissions:</b> {', '.join(endpoint.permissions)}")
            story.append(Paragraph("  |  ".join(info_parts), self.styles['MutedText']))
        
        # Request Body
        if endpoint.request_fields:
            story.append(Paragraph("<b>Request Body:</b>", self.styles['SmallHeader']))
            story.append(self._create_fields_table(endpoint.request_fields))
            
            # Example
            example = self._create_json_example(endpoint.request_fields, is_request=True)
            story.append(Spacer(1, 5))
            story.append(CodeBox(example, "json", self.page_width))
        
        # Response
        if endpoint.response_fields:
            story.append(Paragraph("<b>Response:</b>", self.styles['SmallHeader']))
            story.append(self._create_fields_table(endpoint.response_fields))
            
            example = self._create_json_example(endpoint.response_fields, is_request=False)
            story.append(Spacer(1, 5))
            story.append(CodeBox(example, "json", self.page_width))
        
        story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR,
                               spaceBefore=10, spaceAfter=10))
        
        return story
    
    def _create_websocket_section(self, ws_app) -> List:
        """Create documentation section for WebSocket API"""
        story = []
        
        for endpoint in ws_app.endpoints:
            # Title
            story.append(Paragraph(
                f"🔌 {endpoint.name} WebSocket API Documentation",
                self.styles['DocTitle']
            ))
            story.append(Spacer(1, 10))
            
            # Overview section
            story.append(Paragraph("<b>Overview</b>", self.styles['SectionHeader']))
            story.append(Paragraph(endpoint.description, self.styles['DocBodyText']))
            
            # Features
            if endpoint.features:
                story.append(Paragraph("<b>Features:</b>", self.styles['SmallHeader']))
                for feature in endpoint.features:
                    story.append(Paragraph(f"• {feature}", self.styles['FeatureItem']))
            
            # WebSocket URL
            story.append(Spacer(1, 10))
            full_url = f"{ws_app.base_url}{endpoint.url}?token={{jwt_token}}"
            story.append(URLBox("WebSocket URL:", full_url, self.page_width))
            
            story.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR,
                                   spaceBefore=20, spaceAfter=20))
            
            # Connection Lifecycle
            story.append(Paragraph("<b>Connection Lifecycle</b>", self.styles['SectionHeader']))
            
            # 1. Establishing Connection
            story.append(Paragraph("<b>1. Establishing Connection</b>", self.styles['SubsectionHeader']))
            
            story.append(Paragraph("<b>Client Action:</b>", self.styles['SmallHeader']))
            js_code = f"const ws = new WebSocket('{ws_app.base_url}{endpoint.url}?token=YOUR_JWT_TOKEN');"
            story.append(CodeBox(js_code, "javascript", self.page_width))
            
            # Connection Response
            if endpoint.connection_response:
                story.append(Paragraph("<b>Server Response (on success):</b>", self.styles['SmallHeader']))
                response_json = json.dumps(endpoint.connection_response, indent=2)
                story.append(CodeBox(response_json, "json", self.page_width))
            else:
                # Default connection response
                story.append(Paragraph("<b>Server Response (on success):</b>", self.styles['SmallHeader']))
                default_response = {
                    "type": "connection_established",
                    "user_id": 123,
                    "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
                }
                story.append(CodeBox(json.dumps(default_response, indent=2), "json", self.page_width))
            
            # Connection Errors
            if endpoint.disconnect_codes:
                story.append(Paragraph("<b>Connection Errors:</b>", self.styles['SmallHeader']))
                error_data = [['Code', 'Description']]
                for code_info in endpoint.disconnect_codes:
                    error_data.append([code_info['code'], code_info['description']])
                
                error_table = Table(error_data, colWidths=[80, self.page_width - 100])
                error_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_BG),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(error_table)
            
            story.append(Spacer(1, 15))
            
            # Client Actions
            if endpoint.actions:
                story.append(Paragraph("<b>Client Actions (Client → Server)</b>", 
                                      self.styles['SectionHeader']))
                
                for i, action in enumerate(endpoint.actions, 1):
                    story.append(Paragraph(
                        f"<b>{i}. {action.name.replace('_', ' ').title()}</b>",
                        self.styles['SubsectionHeader']
                    ))
                    story.append(Paragraph(action.description, self.styles['DocBodyText']))
                    
                    # Request
                    story.append(Paragraph("<b>Client sends:</b>", self.styles['SmallHeader']))
                    if action.example_request:
                        story.append(CodeBox(
                            json.dumps(action.example_request, indent=2),
                            "json", self.page_width
                        ))
                    
                    # Response
                    if action.example_response:
                        story.append(Paragraph("<b>Server broadcasts:</b>", self.styles['SmallHeader']))
                        story.append(CodeBox(
                            json.dumps(action.example_response, indent=2),
                            "json", self.page_width
                        ))
                    
                    story.append(Spacer(1, 10))
            
            # Server Events
            if endpoint.server_events:
                story.append(Paragraph("<b>Server Events (Server → Client)</b>", 
                                      self.styles['SectionHeader']))
                
                for event in endpoint.server_events:
                    story.append(Paragraph(
                        f"<b>• {event.name.replace('_', ' ').title()}</b>",
                        self.styles['SubsectionHeader']
                    ))
                    story.append(Paragraph(event.description, self.styles['DocBodyText']))
                    
                    if event.example_response:
                        story.append(CodeBox(
                            json.dumps(event.example_response, indent=2),
                            "json", self.page_width
                        ))
                    story.append(Spacer(1, 8))
        
        return story
    
    def _create_fields_table(self, fields: List[FieldInfo]) -> Table:
        """Create a table displaying field information"""
        data = [['Field', 'Type', 'Required', 'Description']]
        
        for field in fields:
            req = '✓' if field.required else '—'
            desc = field.help_text if field.help_text else '—'
            if len(desc) > 40:
                desc = desc[:37] + '...'
            
            data.append([field.name, field.field_type, req, desc])
        
        table = Table(data, colWidths=[100, 80, 60, self.page_width - 260])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def _create_json_example(self, fields: List[FieldInfo], is_request: bool = True) -> str:
        """Generate JSON example from fields"""
        example = {}
        
        for field in fields:
            if is_request and field.read_only:
                continue
            if not is_request and field.write_only:
                continue
            
            value = self._get_example_value(field)
            example[field.name] = value
        
        return json.dumps(example, indent=2)
    
    def _get_example_value(self, field: FieldInfo) -> Any:
        """Get example value for a field"""
        if field.choices:
            return field.choices[0] if field.choices else None
        
        type_examples = {
            'string': 'example_string',
            'email': 'user@example.com',
            'url': 'https://example.com',
            'integer': 123,
            'float': 1.5,
            'decimal': '1.00',
            'boolean': True,
            'date': '2025-01-15',
            'datetime': '2025-01-15T10:30:00Z',
            'time': '10:30:00',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
            'file': 'file.pdf',
            'image': 'image.jpg',
            'array': [],
            'object': {},
            'json': {},
        }
        
        base_type = field.field_type.lower()
        return type_examples.get(base_type, f'example_{field.name}')
    
    def _get_method_color(self, method: str) -> str:
        """Get color for HTTP method"""
        colors_map = {
            'GET': '#22c55e',
            'POST': '#3b82f6',
            'PUT': '#f59e0b',
            'PATCH': '#8b5cf6',
            'DELETE': '#ef4444',
        }
        return colors_map.get(method.upper(), '#6b7280')
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
