from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import json
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

logger = logging.getLogger("PDFGenerator")

class EcoProfilerPDFReport:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for the PDF report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2E86AB')
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#565656')
        ))
        
        # Risk style
        self.styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=self.styles['Normal'],
            textColor=colors.red,
            backColor=colors.whitesmoke,
            borderPadding=5,
            borderColor=colors.red,
            borderWidth=1
        ))
        
        # Normal style with better spacing
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        ))

    def generate_report(self, data: Dict[str, Any], region_name: str, output_path: str = None) -> str:
        """Generate comprehensive PDF report"""
        try:
            logger.info(f"Starting PDF report generation for {region_name}")
            
            if output_path is None:
                output_dir = Path("data/reports")
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"{region_name}_report_{timestamp}.pdf"
            
            # Create PDF document with conservative margins
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            
            # Build story (content)
            story = []
            
            # Cover page
            story.extend(self.create_cover_page(region_name))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self.create_executive_summary(data, region_name))
            story.append(Spacer(1, 0.1*inch))
            
            # Forest loss analysis
            story.extend(self.create_forest_analysis(data))
            story.append(Spacer(1, 0.1*inch))
            
            # Corporate risk analysis
            story.extend(self.create_corporate_analysis(data))
            story.append(Spacer(1, 0.1*inch))
            
            # Social intelligence
            story.extend(self.create_social_analysis(data))
            story.append(Spacer(1, 0.1*inch))
            
            # Recommendations
            story.extend(self.create_recommendations(data))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF_REPORT_GENERATED: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF_REPORT_ERROR: {str(e)}")
            raise

    def create_cover_page(self, region_name: str) -> List:
        """Create cover page for the report - FIXED SPACING"""
        elements = []
        
        # Title
        title = Paragraph(f"EcoProfiler Intelligence Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Region
        region_text = Paragraph(f"Region: {region_name}", self.styles['CustomHeading'])
        elements.append(region_text)
        elements.append(Spacer(1, 0.1*inch))
        
        # Date
        date_text = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                            self.styles['CustomSubheading'])
        elements.append(date_text)
        elements.append(Spacer(1, 0.2*inch))
        
        # Confidential notice
        confidential = Paragraph(
            "CONFIDENTIAL - For Official Use Only<br/>"
            "Environmental Crime Intelligence - Open Source Data",
            ParagraphStyle(
                name='Confidential',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        )
        elements.append(confidential)
        elements.append(Spacer(1, 0.5*inch))
        
        # Data sources
        sources = Paragraph(
            "<b>Data Sources:</b><br/>"
            "• Global Forest Watch (GLAD Alerts)<br/>"
            "• Sentinel Hub Satellite Imagery<br/>"
            "• Wikidata Corporate Registry<br/>"
            "• GLEIF LEI Database<br/>"
            "• OpenSanctions Screening<br/>"
            "• OpenStreetMap Business Data<br/>"
            "• Reddit Social Media Analysis",
            ParagraphStyle(
                name='Sources',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.darkgray,
                alignment=TA_LEFT
            )
        )
        elements.append(sources)
        
        return elements

    def create_executive_summary(self, data: Dict[str, Any], region_name: str) -> List:
        """Create executive summary section"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Calculate risk metrics
        risk_score = self.calculate_risk_score(data)
        alert_count = len(data['glad_alerts']) if not data['glad_alerts'].empty else 0
        company_count = len(data.get('companies', []))
        sanctioned_count = len([c for c in data.get('companies', []) if c.get('sanctioned', False)])
        reddit_count = len(data.get('reddit_posts', []))
        
        # Risk level determination
        if risk_score > 70:
            risk_level = "CRITICAL"
            risk_color = colors.red
        elif risk_score > 40:
            risk_level = "HIGH"
            risk_color = colors.orange
        elif risk_score > 20:
            risk_level = "MEDIUM"
            risk_color = colors.yellow
        else:
            risk_level = "LOW"
            risk_color = colors.green
        
        # Summary table
        summary_data = [
            ['Risk Assessment', f'{risk_level} ({risk_score:.1f}/100)'],
            ['Forest Loss Alerts', str(alert_count)],
            ['Corporate Entities', str(company_count)],
            ['Sanctioned Entities', str(sanctioned_count)],
            ['Social Media Posts', str(reddit_count)],
            ['Analysis Period', f"Last 30 days"],
            ['Geographic Coverage', f"{region_name} (+20km radius)"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Key findings
        findings_text = self.generate_key_findings_text(data, risk_level)
        elements.append(Paragraph(findings_text, self.styles['CustomNormal']))
        
        return elements

    def create_forest_analysis(self, data: Dict[str, Any]) -> List:
        """Create forest loss analysis section"""
        elements = []
        
        elements.append(Paragraph("Forest Loss Analysis", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
            # Alert statistics
            recent_alerts = data['glad_alerts'][
                pd.to_datetime(data['glad_alerts']['date']) > 
                (datetime.now() - pd.Timedelta(days=30))
            ]
            
            stats_data = [
                ['Metric', 'Value'],
                ['Total Alerts', str(len(data['glad_alerts']))],
                ['Recent Alerts (30d)', str(len(recent_alerts))],
                ['Average Confidence', f"{data['glad_alerts'].get('confidence', 0.5).mean():.2f}"],
                ['Peak Alert Date', str(data['glad_alerts']['date'].max() if 'date' in data['glad_alerts'].columns else 'N/A')]
            ]
            
            stats_table = Table(stats_data, colWidths=[2.5*inch, 2.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 0.1*inch))
            
            # Alert trends
            trend_text = self.generate_forest_trends_text(data)
            elements.append(Paragraph(trend_text, self.styles['CustomNormal']))
            
        else:
            elements.append(Paragraph("No forest loss alert data available for this region.", 
                                    self.styles['CustomNormal']))
        
        return elements

    def create_corporate_analysis(self, data: Dict[str, Any]) -> List:
        """Create corporate risk analysis section"""
        elements = []
        
        elements.append(Paragraph("Corporate Risk Analysis", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        companies = data.get('companies', [])
        osm_businesses = data.get('osm_businesses', [])
        
        if companies:
            # High-risk companies
            high_risk_companies = [
                c for c in companies 
                if c.get('sanctioned') or c.get('shell_company')
            ]
            
            if high_risk_companies:
                elements.append(Paragraph(f"<b>High-Risk Entities Identified: {len(high_risk_companies)}</b>", 
                                        self.styles['CustomSubheading']))
                
                for company in high_risk_companies[:3]:  # Show top 3
                    risk_factors = []
                    if company.get('sanctioned'):
                        risk_factors.append("SANCTIONED")
                    if company.get('shell_company'):
                        risk_factors.append("SHELL COMPANY")
                    
                    company_text = f"• <b>{company.get('name', 'Unknown')}</b> - {', '.join(risk_factors)}"
                    if company.get('industry'):
                        company_text += f" - Industry: {company.get('industry')}"
                    
                    elements.append(Paragraph(company_text, self.styles['CustomNormal']))
                
                elements.append(Spacer(1, 0.05*inch))
            else:
                elements.append(Paragraph("No high-risk corporate entities identified.", 
                                        self.styles['CustomNormal']))
        
        # OSM businesses
        if osm_businesses:
            industrial_businesses = [
                b for b in osm_businesses 
                if any(tag in str(b.get('tags', {})).lower() 
                      for tag in ['industrial', 'mining', 'logging', 'quarry', 'factory'])
            ]
            
            if industrial_businesses:
                elements.append(Paragraph(
                    f"<b>Local Industrial Facilities: {len(industrial_businesses)}</b>",
                    self.styles['CustomSubheading']
                ))
                
                for business in industrial_businesses[:3]:
                    tags = business.get('tags', {})
                    name = tags.get('name', 'Unknown')
                    business_type = tags.get('industrial', tags.get('shop', 'Unknown'))
                    
                    elements.append(Paragraph(
                        f"• {name} - {business_type}",
                        self.styles['CustomNormal']
                    ))
            else:
                elements.append(Paragraph("No industrial facilities identified in the area.", 
                                        self.styles['CustomNormal']))
        
        if not companies and not osm_businesses:
            elements.append(Paragraph(
                "No corporate or business data available for this region.",
                self.styles['CustomNormal']
            ))
        
        return elements

    def create_social_analysis(self, data: Dict[str, Any]) -> List:
        """Create social media analysis section"""
        elements = []
        
        elements.append(Paragraph("Social Media Intelligence", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        reddit_posts = data.get('reddit_posts', [])
        
        if reddit_posts:
            # Sentiment analysis
            negative_posts = [p for p in reddit_posts if p.get('sentiment', 0) < -0.1]
            positive_posts = [p for p in reddit_posts if p.get('sentiment', 0) > 0.1]
            neutral_posts = [p for p in reddit_posts if -0.1 <= p.get('sentiment', 0) <= 0.1]
            
            sentiment_data = [
                ['Sentiment', 'Count', 'Percentage'],
                ['Negative', str(len(negative_posts)), f"{(len(negative_posts)/len(reddit_posts))*100:.1f}%"],
                ['Neutral', str(len(neutral_posts)), f"{(len(neutral_posts)/len(reddit_posts))*100:.1f}%"],
                ['Positive', str(len(positive_posts)), f"{(len(positive_posts)/len(reddit_posts))*100:.1f}%"],
                ['Total', str(len(reddit_posts)), '100%']
            ]
            
            sentiment_table = Table(sentiment_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
            sentiment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (0, 1), colors.lightcoral),
                ('BACKGROUND', (0, 2), (0, 2), colors.lightgrey),
                ('BACKGROUND', (0, 3), (0, 3), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(sentiment_table)
            elements.append(Spacer(1, 0.1*inch))
            
            # Key discussions
            top_posts = sorted(reddit_posts, key=lambda x: x.get('score', 0), reverse=True)[:2]  # Show top 2
            
            elements.append(Paragraph("<b>Key Discussions:</b>", self.styles['CustomSubheading']))
            
            for i, post in enumerate(top_posts, 1):
                sentiment = post.get('sentiment', 0)
                sentiment_emoji = "🔴" if sentiment < -0.1 else "🟢" if sentiment > 0.1 else "⚪"
                
                post_text = (
                    f"{i}. {sentiment_emoji} <b>Score: {post.get('score', 0)}</b><br/>"
                    f"\"{post.get('title', 'No title')[:80]}...\"<br/>"
                    f"Subreddit: r/{post.get('subreddit', 'unknown')} | "
                    f"Comments: {post.get('num_comments', 0)}"
                )
                
                elements.append(Paragraph(post_text, self.styles['CustomNormal']))
                elements.append(Spacer(1, 0.05*inch))
        
        else:
            elements.append(Paragraph(
                "No social media data available for this region.",
                self.styles['CustomNormal']
            ))
        
        return elements

    def create_recommendations(self, data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recommendations & Next Steps", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        risk_score = self.calculate_risk_score(data)
        
        if risk_score > 70:
            recommendations = [
                "🚨 <b>IMMEDIATE ACTION REQUIRED</b>",
                "• Launch formal environmental crime investigation",
                "• Coordinate with local law enforcement agencies",
                "• Deploy real-time satellite monitoring",
                "• Conduct field verification of high-risk sites",
                "• Freeze assets of sanctioned entities if applicable",
                "• Engage with social media platforms for content monitoring"
            ]
        elif risk_score > 40:
            recommendations = [
                "⚠️ <b>ENHANCED MONITORING RECOMMENDED</b>",
                "• Increase satellite monitoring frequency to weekly",
                "• Conduct deeper corporate due diligence",
                "• Monitor social channels for escalation signals",
                "• Prepare contingency investigation plans",
                "• Engage with local environmental NGOs",
                "• Schedule follow-up assessment in 30 days"
            ]
        else:
            recommendations = [
                "✅ <b>STANDARD MONITORING SUFFICIENT</b>",
                "• Maintain regular satellite monitoring schedule",
                "• Continue periodic corporate registry checks",
                "• Monitor social media for emerging trends",
                "• Document baseline metrics for future comparison",
                "• Review regulatory compliance of local businesses",
                "• Conduct routine follow-up in 90 days"
            ]
        
        for rec in recommendations:
            if "🚨" in rec or "⚠️" in rec or "✅" in rec:
                # This is a header line
                elements.append(Paragraph(rec, self.styles['CustomSubheading']))
            else:
                elements.append(Paragraph(rec, self.styles['CustomNormal']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Follow-up timeline
        timeline_text = (
            "<b>Recommended Follow-up Timeline:</b><br/>"
            f"• Next assessment: {self.get_next_assessment_date(risk_score)}<br/>"
            "• Data refresh: 7 days<br/>"
            "• Report update: 30 days"
        )
        
        elements.append(Paragraph(timeline_text, self.styles['CustomNormal']))
        
        return elements

    def calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall environmental risk score"""
        score = 0
        
        # GLAD alerts contribute 40%
        if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
            alert_count = len(data['glad_alerts'])
            score += min(40, alert_count * 2)  # 2 points per alert
            
        # Company sanctions contribute 30%
        sanctioned_companies = [c for c in data.get('companies', []) if c.get('sanctioned', False)]
        score += min(30, len(sanctioned_companies) * 15)
        
        # Reddit sentiment contributes 20%
        reddit_posts = data.get('reddit_posts', [])
        if reddit_posts:
            negative_posts = [p for p in reddit_posts if p.get('sentiment', 0) < -0.1]
            if negative_posts:
                score += min(20, (len(negative_posts) / len(reddit_posts)) * 20)
            
        # OSM industrial sites contribute 10%
        industrial_osm = [b for b in data.get('osm_businesses', []) 
                         if any(tag in str(b.get('tags', {})).lower() 
                               for tag in ['industrial', 'mining', 'logging', 'quarry'])]
        score += min(10, len(industrial_osm) * 2)
        
        return min(100, score)

    def generate_key_findings_text(self, data: Dict[str, Any], risk_level: str) -> str:
        """Generate key findings text for executive summary"""
        findings = []
        
        if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
            recent_alerts = data['glad_alerts'][
                pd.to_datetime(data['glad_alerts']['date']) > 
                (datetime.now() - pd.Timedelta(days=30))
            ]
            findings.append(f"• <b>{len(recent_alerts)} recent forest loss alerts</b> detected in past 30 days")
        
        companies = data.get('companies', [])
        if companies:
            sanctioned = len([c for c in companies if c.get('sanctioned', False)])
            if sanctioned > 0:
                findings.append(f"• <b>{sanctioned} sanctioned corporate entities</b> operating in region")
        
        reddit_posts = data.get('reddit_posts', [])
        if reddit_posts:
            negative_posts = len([p for p in reddit_posts if p.get('sentiment', 0) < -0.1])
            if negative_posts > 0:
                findings.append(f"• <b>{negative_posts} negative social media discussions</b> about environmental issues")
        
        if not findings:
            findings.append("• Limited data available for comprehensive risk assessment")
            findings.append("• Consider expanding search parameters for more comprehensive analysis")
        
        findings_text = "<b>Key Findings:</b><br/>" + "<br/>".join(findings)
        return findings_text

    def generate_forest_trends_text(self, data: Dict[str, Any]) -> str:
        """Generate forest trends analysis text"""
        if data['glad_alerts'].empty:
            return "No forest alert data available for trend analysis."
        
        # Calculate basic trends
        daily_alerts = data['glad_alerts'].groupby(
            pd.to_datetime(data['glad_alerts']['date']).dt.date
        ).size()
        
        if len(daily_alerts) > 1:
            trend = "increasing" if daily_alerts.iloc[-1] > daily_alerts.iloc[0] else "decreasing"
            peak_day = daily_alerts.idxmax()
            peak_count = daily_alerts.max()
            
            return (
                f"Alert frequency shows a <b>{trend} trend</b> over the analysis period. "
                f"Peak activity occurred on {peak_day} with {peak_count} alerts. "
                "Continued monitoring recommended to track deforestation patterns."
            )
        else:
            return "Insufficient data for trend analysis. Additional monitoring required."

    def get_next_assessment_date(self, risk_score: float) -> str:
        """Calculate next assessment date based on risk"""
        from datetime import datetime, timedelta
        
        if risk_score > 70:
            days = 7
        elif risk_score > 40:
            days = 14
        else:
            days = 30
        
        next_date = datetime.now() + timedelta(days=days)
        return next_date.strftime("%Y-%m-%d")

# Make sure this function is defined at the module level
def generate_pdf_report(data: Dict[str, Any], region_name: str, output_path: str = None) -> str:
    """Convenience function to generate PDF report"""
    generator = EcoProfilerPDFReport()
    return generator.generate_report(data, region_name, output_path)