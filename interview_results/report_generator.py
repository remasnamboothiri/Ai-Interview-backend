from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from interview_screenshots.models import InterviewScreenshot
from django.conf import settings
import os

class InterviewReportGenerator:
    """Generates PDF reports with flagged screenshots"""
    
    def generate_report(self, interview_result):
        """
        Generate PDF report for interview result
        
        Args:
            interview_result: InterviewResult object
            
        Returns:
            str: Path to generated PDF file
        """
        # Get flagged screenshots (max 10)
        flagged_screenshots = InterviewScreenshot.objects.filter(
            interview=interview_result.interview,
            multiple_people_detected=True
        ).order_by('-confidence_score')[:settings.MAX_SCREENSHOTS_IN_REPORT]
        
        # Update red_flags in result
        red_flags = []
        for screenshot in flagged_screenshots:
            red_flags.append({
                'type': screenshot.issue_type,
                'timestamp': screenshot.timestamp.isoformat(),
                'screenshot_number': screenshot.screenshot_number,
                'confidence': float(screenshot.confidence_score) if screenshot.confidence_score else 0.0
            })
        
        interview_result.red_flags = red_flags
        interview_result.save()
        
        # Generate PDF
        pdf_path = self._create_pdf(interview_result, flagged_screenshots)
        
        return pdf_path
    
    def _create_pdf(self, interview_result, flagged_screenshots):
        """Create PDF file with report"""
        # Create reports directory
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # PDF filename
        filename = f"interview_report_{interview_result.interview.id}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        # Create PDF
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(1*inch, height - 1*inch, "Interview Proctoring Report")
        
        # Candidate info
        c.setFont("Helvetica", 12)
        y_position = height - 1.5*inch
        c.drawString(1*inch, y_position, f"Candidate: {interview_result.interview.candidate.user.full_name}")
        y_position -= 0.3*inch
        c.drawString(1*inch, y_position, f"Job: {interview_result.interview.job.title}")
        y_position -= 0.3*inch
        c.drawString(1*inch, y_position, f"Overall Score: {interview_result.overall_score}/10")
        y_position -= 0.3*inch
        c.drawString(1*inch, y_position, f"Recommendation: {interview_result.recommendation.upper()}")
        
        # Flagged screenshots section
        y_position -= 0.5*inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, y_position, f"Proctoring Violations ({len(flagged_screenshots)} detected)")
        
        y_position -= 0.4*inch
        
        # Add each flagged screenshot
        for i, screenshot in enumerate(flagged_screenshots):
            if y_position < 2*inch:  # Start new page if needed
                c.showPage()
                y_position = height - 1*inch
            
            c.setFont("Helvetica", 10)
            c.drawString(1*inch, y_position, 
                        f"#{i+1} - {screenshot.issue_type} - Confidence: {screenshot.confidence_score:.2f}")
            y_position -= 0.2*inch
            
            # Add screenshot image
            try:
                image_path = os.path.join(settings.BASE_DIR, screenshot.screenshot_url.lstrip('/'))
                if os.path.exists(image_path):
                    img = ImageReader(image_path)
                    c.drawImage(img, 1*inch, y_position - 2*inch, 
                               width=3*inch, height=2*inch, preserveAspectRatio=True)
                    y_position -= 2.3*inch
            except Exception as e:
                c.drawString(1*inch, y_position, f"[Image not available: {str(e)}]")
                y_position -= 0.3*inch
        
        # Save PDF
        c.save()
        
        return filepath
