import base64
import os
import asyncio  # Importar asyncio para manejar el timeout
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import resend

from app.db.database import get_db
from app.models.models import Usuario

RESEND_KEY = os.getenv('RESEND_KEY')
resend.api_key = RESEND_KEY
router = APIRouter()

# Definir el tiempo máximo permitido para el envío de correos (en segundos)
TIMEOUT_SECONDS = 50

@router.post("/report/send")
async def send_report(destino: List[int], pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Leer el contenido del PDF
        pdf_content = await pdf.read()
        
        # Convertir el contenido a Base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Obtener los correos de los usuarios según los IDs de destino
        users = db.execute(
            Usuario.__table__.select().where(Usuario.__table__.c.id.in_(destino))
        ).mappings().all()

        emails = [user['email'] for user in users]  # Extraer los emails
        if not emails:
            raise HTTPException(status_code=404, detail="No users found for the provided IDs")

        # Preparar los parámetros del correo
        attachment = {
            "content": pdf_base64,  # Usar el contenido en Base64
            "filename": pdf.filename  # Agregar el nombre del archivo
        }

        params: resend.Emails.SendParams = {
           "from": "Panel A.C.I.B Registros <onboarding@resend.dev>",
           "to": emails,  # Lista de correos electrónicos
           "subject": "Reporte Enviado - Acción Requerida",
           "html": """
           <html>
             <head>
               <style>
                 body {
                   font-family: Arial, sans-serif;
                   margin: 0;
                   padding: 20px;
                   background-color: #f4f4f4;
                 }
                 .container {
                   max-width: 600px;
                   margin: auto;
                   background: white;
                   border-radius: 8px;
                   box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                   padding: 20px;
                 }
                 h1 {
                   color: #333;
                 }
                 p {
                   color: #666;
                   line-height: 1.5;
                 }
                 .cta-button {
                   display: inline-block;
                   margin-top: 20px;
                   padding: 10px 15px;
                   background-color: #007bff;
                   color: white;
                   text-decoration: none;
                   border-radius: 5px;
                 }
                 .footer {
                   margin-top: 30px;
                   font-size: 0.8em;
                   color: #999;
                 }
               </style>
             </head>
             <body>
               <div class="container">
                 <h1>Estimado Gerente,</h1>
                 <p>Se ha generado un reporte solicitado y se encuentra adjunto a este correo.</p>
                 <p>Atentamente,</p>
                 <p>El equipo de A.C.I.B Registros</p>
                 <div class="footer">
                   <p>Si no reconoce este correo, por favor, ignórelo.</p>
                   <p>Panel A.C.I.B - URL</p>
                 </div>
               </div>
             </body>
           </html>
           """,
           "attachments": [attachment],
        }

        # Enviar el correo con un timeout de 50 segundos
        try:
            email = await asyncio.wait_for(resend.Emails.send(params), timeout=TIMEOUT_SECONDS)
            return {"message": "Reporte enviado con éxito!", "email": email}
        except asyncio.TimeoutError:
            return {"message": "El envío del reporte tomó demasiado tiempo. Continúa con el proceso normal."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
