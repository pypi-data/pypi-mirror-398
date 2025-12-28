"""
PDF Generator Module
Generates beautiful, production-quality PDF documentation
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem, HRFlowable,
        KeepTogether, Flowable
    )
    from reportlab.graphics.shapes import Drawing, Rect, Line
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from .parser import AppAPIInfo, EndpointInfo, FieldInfo


class ColoredRect(Flowable):
    """A colored rectangle flowable for section headers"""
    
    def __init__(self, width, height, color, radius=3):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        self.radius = radius
    
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)


class MethodBadge(Flowable):
    """A badge-style method indicator"""
    
    METHOD_COLORS = {
        'GET': colors.HexColor('#22c55e'),      # Green
        'POST': colors.HexColor('#3b82f6'),     # Blue  
        'PUT': colors.HexColor('#f59e0b'),      # Orange
        'PATCH': colors.HexColor('#8b5cf6'),    # Purple
        'DELETE': colors.HexColor('#ef4444'),   # Red
        'HEAD': colors.HexColor('#6b7280'),     # Gray
        'OPTIONS': colors.HexColor('#06b6d4'),  # Cyan
    }
    
    def __init__(self, method: str, width=50, height=18):
        Flowable.__init__(self)
        self.method = method.upper()
        self.width = width
        self.height = height
        self.color = self.METHOD_COLORS.get(self.method, colors.HexColor('#6b7280'))
    
    def draw(self):
        # Draw rounded rectangle background
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        
        # Draw method text
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 8)
        text_width = self.canv.stringWidth(self.method, 'Helvetica-Bold', 8)
        x = (self.width - text_width) / 2
        y = (self.height - 8) / 2 + 2
        self.canv.drawString(x, y, self.method)


class PDFGenerator:
    """
    Generates production-quality PDF documentation for APIs
    """
    
    # Theme colors
    PRIMARY_COLOR = colors.HexColor('#2563eb')
    SECONDARY_COLOR = colors.HexColor('#1e40af')
    ACCENT_COLOR = colors.HexColor('#3b82f6')
    SUCCESS_COLOR = colors.HexColor('#22c55e')
    WARNING_COLOR = colors.HexColor('#f59e0b')
    DANGER_COLOR = colors.HexColor('#ef4444')
    TEXT_COLOR = colors.HexColor('#1f2937')
    MUTED_COLOR = colors.HexColor('#6b7280')
    LIGHT_BG = colors.HexColor('#f8fafc')
    BORDER_COLOR = colors.HexColor('#e2e8f0')
    CODE_BG = colors.HexColor('#1e293b')
    
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
        
        theme_color = self.config.get('THEME_COLOR', '#2563eb')
        if theme_color:
            self.PRIMARY_COLOR = colors.HexColor(theme_color)
        
        self.styles = self._create_styles()
        self.toc_entries = []
        
    def _create_styles(self):
        """Create custom paragraph styles for the PDF"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='DocTitle',
            parent=styles['Title'],
            fontSize=36,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            name='DocSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=self.MUTED_COLOR,
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold',
            borderPadding=10,
        ))
        
        # Subsection header style
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=self.SECONDARY_COLOR,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold',
        ))
        
        # Endpoint title style
        styles.add(ParagraphStyle(
            name='EndpointTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=self.TEXT_COLOR,
            spaceBefore=8,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            leftIndent=65,
        ))
        
        # URL style
        styles.add(ParagraphStyle(
            name='URLStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.TEXT_COLOR,
            fontName='Courier',
            backColor=self.LIGHT_BG,
            borderPadding=8,
            spaceBefore=5,
            spaceAfter=5,
        ))
        
        # Description style
        styles.add(ParagraphStyle(
            name='Description',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            spaceAfter=8,
            leading=14,
            alignment=TA_JUSTIFY,
        ))
        
        # Label style
        styles.add(ParagraphStyle(
            name='Label',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.MUTED_COLOR,
            fontName='Helvetica-Bold',
            spaceBefore=8,
            spaceAfter=4,
        ))
        
        # Code style
        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Courier',
            textColor=colors.white,
            backColor=self.CODE_BG,
            borderPadding=10,
            leading=12,
        ))
        
        # Small text style
        styles.add(ParagraphStyle(
            name='Small',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.MUTED_COLOR,
        ))
        
        # Badge style
        styles.add(ParagraphStyle(
            name='Badge',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
        ))
        
        # TOC entry style
        styles.add(ParagraphStyle(
            name='TOCEntry',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.TEXT_COLOR,
            spaceBefore=4,
            spaceAfter=4,
            leftIndent=20,
        ))
        
        # TOC app header style
        styles.add(ParagraphStyle(
            name='TOCAppHeader',
            parent=styles['Normal'],
            fontSize=13,
            textColor=self.PRIMARY_COLOR,
            fontName='Helvetica-Bold',
            spaceBefore=15,
            spaceAfter=8,
        ))
        
        return styles
    
    def generate(self, apps: List[AppAPIInfo], output_path: str) -> str:
        """
        Generate PDF documentation
        
        Args:
            apps: List of AppAPIInfo objects with parsed API data
            output_path: Path to save the PDF file
            
        Returns:
            Path to the generated PDF file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=60,
            bottomMargin=60,
            title=self.title,
            author='API Documentation Generator',
        )
        
        # Build content
        story = []
        
        # Add cover page
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # Add table of contents
        story.extend(self._create_toc(apps))
        story.append(PageBreak())
        
        # Add API documentation for each app
        for app in apps:
            story.extend(self._create_app_section(app))
            story.append(PageBreak())
        
        # Build the PDF
        doc.build(story, onFirstPage=self._add_page_header_footer, 
                  onLaterPages=self._add_page_header_footer)
        
        return os.path.abspath(output_path)
    
    def _add_page_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Footer
        footer_text = f"Generated by API Documentation Generator | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(self.MUTED_COLOR)
        canvas_obj.drawString(doc.leftMargin, 30, footer_text)
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawRightString(doc.width + doc.leftMargin, 30, f"Page {page_num}")
        
        # Header line
        canvas_obj.setStrokeColor(self.BORDER_COLOR)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(doc.leftMargin, doc.height + doc.topMargin - 10,
                       doc.width + doc.leftMargin, doc.height + doc.topMargin - 10)
        
        canvas_obj.restoreState()
    
    def _create_cover_page(self) -> List:
        """Create the cover page"""
        story = []
        
        # Add spacing from top
        story.append(Spacer(1, 2*inch))
        
        # Logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=1.5*inch, height=1.5*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.3*inch))
            except:
                pass
        
        # Title
        story.append(Paragraph(self.title, self.styles['DocTitle']))
        
        # Subtitle
        story.append(Paragraph(self.description, self.styles['DocSubtitle']))
        
        # Version badge
        version_text = f"<b>Version {self.version}</b>"
        story.append(Paragraph(version_text, self.styles['DocSubtitle']))
        
        story.append(Spacer(1, 1*inch))
        
        # Info table
        info_data = [
            ['Generated On', datetime.now().strftime('%B %d, %Y at %H:%M')],
        ]
        
        if self.contact_email:
            info_data.append(['Contact', self.contact_email])
        
        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.MUTED_COLOR),
            ('TEXTCOLOR', (1, 0), (1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        
        return story
    
    def _create_toc(self, apps: List[AppAPIInfo]) -> List:
        """Create table of contents"""
        story = []
        
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        
        for app in apps:
            # App header
            story.append(Paragraph(f"📦 {app.app_label}", self.styles['TOCAppHeader']))
            
            # Endpoint entries
            for endpoint in app.endpoints:
                methods_str = ' | '.join(endpoint.methods)
                toc_text = f"<b>{methods_str}</b>  {endpoint.url}"
                story.append(Paragraph(toc_text, self.styles['TOCEntry']))
        
        return story
    
    def _create_app_section(self, app: AppAPIInfo) -> List:
        """Create documentation section for an app"""
        story = []
        
        # App header
        header_text = f"📦 {app.app_label}"
        story.append(Paragraph(header_text, self.styles['SectionHeader']))
        
        # App description
        if app.description:
            story.append(Paragraph(app.description, self.styles['Description']))
        
        # Divider
        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.BORDER_COLOR,
            spaceBefore=10,
            spaceAfter=20,
        ))
        
        # Endpoints
        for i, endpoint in enumerate(app.endpoints):
            endpoint_content = self._create_endpoint_section(endpoint)
            story.extend(endpoint_content)
            
            # Add spacing between endpoints
            if i < len(app.endpoints) - 1:
                story.append(Spacer(1, 15))
                story.append(HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=self.BORDER_COLOR,
                    spaceBefore=5,
                    spaceAfter=15,
                ))
        
        return story
    
    def _create_endpoint_section(self, endpoint: EndpointInfo) -> List:
        """Create documentation for a single endpoint"""
        story = []
        
        # Methods and URL header
        methods_badges = []
        for method in endpoint.methods:
            badge_color = MethodBadge.METHOD_COLORS.get(method.upper(), self.MUTED_COLOR)
            badge_text = f'<font color="white" backColor="{badge_color.hexval()}">&nbsp;{method}&nbsp;</font>'
            methods_badges.append(badge_text)
        
        # Create method badges row
        methods_str = '  '.join(endpoint.methods)
        url_display = endpoint.url
        
        # Create a table for method + URL
        method_data = []
        for method in endpoint.methods:
            method_data.append([method])
        
        header_table_data = [[
            ' | '.join([f'<b>{m}</b>' for m in endpoint.methods]),
            endpoint.url
        ]]
        
        # Method and URL on same line
        method_badges_html = ' '.join([
            f'<font name="Helvetica-Bold" size="9" color="#{self._get_method_color(m)[1:]}">[{m}]</font>'
            for m in endpoint.methods
        ])
        
        story.append(Paragraph(
            f'{method_badges_html}  <font name="Courier" size="11">{endpoint.url}</font>',
            self.styles['Description']
        ))
        
        # Endpoint name and description
        if endpoint.description:
            story.append(Paragraph(endpoint.description, self.styles['Description']))
        
        story.append(Spacer(1, 8))
        
        # Create info sections
        sections = []
        
        # Authentication section
        if endpoint.authentication:
            sections.append(('🔐 Authentication', ', '.join(endpoint.authentication)))
        
        # Permissions section  
        if endpoint.permissions:
            sections.append(('🛡️ Permissions', ', '.join(endpoint.permissions)))
        
        # Path parameters section
        if endpoint.path_params:
            params_text = ', '.join([f'{{{p}}}' for p in endpoint.path_params])
            sections.append(('📍 Path Parameters', params_text))
        
        # Create sections table
        if sections:
            for label, value in sections:
                story.append(Paragraph(f"<b>{label}:</b> {value}", self.styles['Description']))
        
        # Query Parameters section
        if endpoint.query_params:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>📋 Query Parameters</b>", self.styles['Label']))
            story.append(self._create_fields_table(endpoint.query_params))
        
        # Request Body section
        if endpoint.request_fields:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>📤 Request Body</b>", self.styles['Label']))
            story.append(self._create_fields_table(endpoint.request_fields))
            
            # JSON Example
            story.append(Spacer(1, 5))
            story.append(Paragraph("<b>Example Request:</b>", self.styles['Small']))
            json_example = self._create_json_example(endpoint.request_fields, is_request=True)
            story.append(Paragraph(
                f'<font name="Courier" size="9">{self._escape_html(json_example)}</font>',
                self.styles['Description']
            ))
        
        # Response section
        if endpoint.response_fields:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>📥 Response (200 OK)</b>", self.styles['Label']))
            story.append(self._create_fields_table(endpoint.response_fields))
            
            # JSON Example
            story.append(Spacer(1, 5))
            story.append(Paragraph("<b>Example Response:</b>", self.styles['Small']))
            json_example = self._create_json_example(endpoint.response_fields, is_request=False)
            story.append(Paragraph(
                f'<font name="Courier" size="9">{self._escape_html(json_example)}</font>',
                self.styles['Description']
            ))
        
        return story
    
    def _get_method_color(self, method: str) -> str:
        """Get hex color for HTTP method"""
        colors_map = {
            'GET': '#22c55e',
            'POST': '#3b82f6', 
            'PUT': '#f59e0b',
            'PATCH': '#8b5cf6',
            'DELETE': '#ef4444',
            'HEAD': '#6b7280',
            'OPTIONS': '#06b6d4',
        }
        return colors_map.get(method.upper(), '#6b7280')
    
    def _create_fields_table(self, fields: List[FieldInfo]) -> Table:
        """Create a table displaying field information"""
        # Table header
        data = [['Field', 'Type', 'Required', 'Description']]
        
        for field in fields:
            req_symbol = '✓' if field.required else '—'
            
            # Build description with constraints
            desc_parts = []
            if field.help_text:
                desc_parts.append(field.help_text)
            if field.choices:
                choices_str = ', '.join([str(c) for c in field.choices[:5]])
                if len(field.choices) > 5:
                    choices_str += '...'
                desc_parts.append(f'Choices: {choices_str}')
            if field.max_length:
                desc_parts.append(f'Max length: {field.max_length}')
            if field.default is not None:
                desc_parts.append(f'Default: {field.default}')
            
            description = ' | '.join(desc_parts) if desc_parts else '—'
            
            data.append([
                field.name,
                field.field_type,
                req_symbol,
                description[:50] + '...' if len(description) > 50 else description
            ])
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 1*inch, 0.7*inch, 2.5*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_COLOR),
            ('FONTNAME', (0, 1), (0, -1), 'Courier'),  # Field names in monospace
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            
            # Required column centering
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternate row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.white) for i in range(2, len(data), 2)],
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
        """Get example value for a field based on its type"""
        if field.default is not None and str(field.default) != 'empty':
            # Only use default if it's JSON serializable
            try:
                default_val = field.default
                if isinstance(default_val, (str, int, float, bool, list, dict, type(None))):
                    return default_val
            except:
                pass
        
        if field.choices:
            return field.choices[0] if field.choices else None
        
        type_examples = {
            'string': '"example_string"',
            'email': '"user@example.com"',
            'url': '"https://example.com"',
            'integer': 1,
            'float': 1.0,
            'decimal': '1.00',
            'boolean': True,
            'date': '"2024-01-15"',
            'datetime': '"2024-01-15T10:30:00Z"',
            'time': '"10:30:00"',
            'uuid': '"123e4567-e89b-12d3-a456-426614174000"',
            'file': '"file.pdf"',
            'image': '"image.jpg"',
            'array': [],
            'object': {},
            'json': {},
            'integer (pk)': 1,
            'string (slug)': '"example-slug"',
        }
        
        base_type = field.field_type.lower()
        
        if base_type in type_examples:
            return type_examples[base_type]
        
        if 'integer' in base_type or 'pk' in base_type:
            return 1
        if 'string' in base_type:
            return f'"example_{field.name}"'
        
        return 'null'
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
