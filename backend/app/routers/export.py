import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Episode, Prediction, Session as SessionModel, User

router = APIRouter()


@router.get("/export")
def export_data(
    user_id: int = Query(default=1),
    format: str = Query(default="pdf"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.name if user else f"User {user_id}"

    user_sessions = (
        db.query(SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .subquery()
    )
    predictions = (
        db.query(Prediction)
        .filter(Prediction.session_id.in_(user_sessions))
        .order_by(Prediction.ts.desc())
        .limit(200)
        .all()
    )
    episodes = (
        db.query(Episode)
        .filter(Episode.user_id == user_id)
        .order_by(Episode.started_at.desc())
        .all()
    )

    if format == "csv":
        return _export_csv(user_name, predictions, episodes)
    else:
        return _export_pdf(user_name, predictions, episodes)


def _export_csv(user_name, predictions, episodes):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["NeuroPulse Export", f"User: {user_name}", f"Date: {datetime.utcnow().date()}"])
    writer.writerow([])

    writer.writerow(["=== PREDICTIONS ==="])
    writer.writerow(["Timestamp", "Label", "Label Name", "Confidence", "Recommended"])
    label_names = {0: "calm", 1: "rising", 2: "critical"}
    for p in predictions:
        writer.writerow([
            p.ts.isoformat() if p.ts else "",
            p.label,
            label_names.get(p.label, "unknown"),
            f"{p.confidence:.2f}",
            p.recommended or ""
        ])

    writer.writerow([])
    writer.writerow(["=== EPISODES ==="])
    writer.writerow(["Started", "Ended", "Severity", "Trigger", "Notes"])
    for e in episodes:
        writer.writerow([
            e.started_at.isoformat() if e.started_at else "",
            e.ended_at.isoformat() if e.ended_at else "",
            e.severity,
            e.trigger_guess or "",
            e.notes or ""
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=neuropulse_{datetime.utcnow().date()}.csv"}
    )


def _export_pdf(user_name, predictions, episodes):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("NeuroPulse — Medical Report", styles["Title"]))
        story.append(Paragraph(f"Patient: {user_name}", styles["Normal"]))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("Recent Predictions", styles["Heading2"]))
        if predictions:
            label_names = {0: "Calm", 1: "Rising Stress", 2: "Critical"}
            data = [["Time", "Status", "Confidence", "Action"]]
            for p in predictions[:20]:
                data.append([
                    p.ts.strftime("%Y-%m-%d %H:%M") if p.ts else "",
                    label_names.get(p.label, "Unknown"),
                    f"{p.confidence:.0%}",
                    p.recommended or "—"
                ])
            t = Table(data, colWidths=[4 * cm, 4 * cm, 3 * cm, 4 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A8C8B8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2F3A36")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E5E2")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F4")]),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No predictions recorded yet.", styles["Normal"]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Episodes", styles["Heading2"]))
        if episodes:
            data = [["Started", "Severity", "Trigger", "Notes"]]
            for e in episodes[:20]:
                data.append([
                    e.started_at.strftime("%Y-%m-%d %H:%M") if e.started_at else "",
                    str(e.severity),
                    e.trigger_guess or "—",
                    (e.notes or "—")[:50]
                ])
            t = Table(data, colWidths=[4 * cm, 2.5 * cm, 4 * cm, 4.5 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8C58F")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E5E2")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F4")]),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No episodes recorded yet.", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=neuropulse_{datetime.utcnow().date()}.pdf"}
        )
    except ImportError:
        # Fallback to CSV if reportlab not available
        return _export_csv(user_name, predictions, episodes)
