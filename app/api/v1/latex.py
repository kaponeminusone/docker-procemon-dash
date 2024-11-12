from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import os
import subprocess
import tempfile

from requests import Session
from app.db.database import get_db
from app.models.models import ProcesosEjecutados, Registro, RegistroProcesoEjecutado, Usuario
from app.schemas.execution import EjecucionProcesoSchema
from app.schemas.log import GeneracionDocumentoSchema

router = APIRouter()
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "pdf_output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

procesos_ejecutados_table = ProcesosEjecutados.__table__
registro_table = Registro.__table__
usuario_table = Usuario.__table__
registro_procesos_ejecutados_table = RegistroProcesoEjecutado.__table__

@router.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    # Guarda el archivo LaTeX en el directorio de uploads
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Genera el PDF usando pdflatex
    pdf_filename = os.path.join(UPLOAD_DIR, file.filename.replace('.tex', '.pdf'))
    print(f"Archivo LaTeX guardado en: {file_location}")
    print(f"Archivo PDF esperado en: {pdf_filename}")

    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=batchmode', '-output-directory', UPLOAD_DIR, str(file_location)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("PDF generation completed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error generating PDF:")
        print(e.stderr.decode())
        raise HTTPException(status_code=500, detail="Error generating PDF")

    # Devuelve el archivo PDF
    return FileResponse(pdf_filename)


@router.post("/generate")
async def execute_proceso(data: GeneracionDocumentoSchema, db: Session = Depends(get_db)):
    """Ejecuta un proceso y guarda los resultados."""
    # Inicia una transacción
    with db.begin():
        # Obtener información de los procesos ejecutados y registros
        procesos_ids = data.informacion.get("procesos_ejecutados", [])
        registros_ids = data.informacion.get("registros", [])

        # Obtener el usuario de la base de datos
        usuario = db.execute(usuario_table.select().where(usuario_table.c.id == data.usuario)).first()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Obtener la información de los destinos
        destinos = db.execute(usuario_table.select().where(usuario_table.c.id.in_(data.destino))).fetchall()
        if not destinos:
            raise HTTPException(status_code=404, detail="Destinos no encontrados")

        # Crear el documento .tex
        tex_content = f"""
\\documentclass[a4paper,10pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{graphicx}}
\\usepackage{{longtable}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

% Cambiar la fuente por defecto a una más profesional
\\renewcommand{{\\rmdefault}}{{ptm}} % Cambia a fuente Times
\\renewcommand{{\\sfdefault}}{{phv}} % Cambia a fuente Helvetica

\\begin{{document}}

% Logo del software
\\begin{{center}}
    \\includegraphics[width=0.3\\textwidth]{{logo.jpeg}} % Asegúrate que el logo esté en la misma carpeta
    \\\[1em]
    {{\\LARGE \\textbf{{{data.titulo}}}}}
\\end{{center}}

\\vspace{{1em}}

\\noindent \\textbf{{Motivo:}} {data.motivo} \\\[0.5em]

\\noindent \\textbf{{Usuario:}} \\\\
Nombre: {usuario.nombre} \\\\
Correo: {usuario.email} \\\[0.5em]

\\noindent \\textbf{{Destino:}} \\\\
Nombres: {", ".join(destino.nombre for destino in destinos)} \\\\
Correos: {", ".join(destino.email for destino in destinos)} \\\[0.5em]

\\vspace{{1.5em}}

% Tabla con procesos ejecutados
\\noindent \\textbf{{Procesos Ejecutados:}} \\\\
\\begin{{longtable}}{{|p{{0.6\\textwidth}}|p{{0.2\\textwidth}}|p{{0.2\\textwidth}}|}}
    \\hline
    \\textbf{{Acción}} & \\textbf{{Hora}} & \\textbf{{Usuario}} \\\\
    \\hline
    \\endfirsthead
    \\hline
    \\textbf{{Acción}} & \\textbf{{Hora}} & \\textbf{{Usuario}} \\\\
    \\hline
    \\endhead
    \\hline
    \\endfoot
"""
        # Aquí añades la información de procesos_ejecutados
        for proceso_id in procesos_ids:
            proceso = db.execute(procesos_ejecutados_table.select().where(procesos_ejecutados_table.c.id == proceso_id)).first()
            proceso_registro_id = db.execute(registro_procesos_ejecutados_table.select().where(registro_procesos_ejecutados_table.c.id_proceso_ejecutado == proceso_id)).first()
            registro_usuario_id = db.execute(registro_table.select().where(registro_table.c.id == proceso_registro_id.id_registro)).first()
            
            if proceso:
                proceso_usuario = db.execute(usuario_table.select().where(usuario_table.c.id == registro_usuario_id.id_usuario)).first()  # Obtener el usuario asociado
                
                # Aquí organizamos los datos en las tres columnas
                tex_content += (
                    f" \\textbf{{{registro_usuario_id.descripcion}}} & "  # Acción
                    f" {registro_usuario_id.creado} & "  # Hora del proceso
                    f" {proceso_usuario.nombre} \\\\ \n"  # Usuario
                    f" \\textbf{{Tasa de exito:}} {proceso.tasa_de_exito} & & \\\\ \n"  # La tasa de éxito en una fila adicional
                    f" \\textbf{{Registro Asociado:}} {registro_usuario_id.id} & & \\\\ \n"  # Registro Asociado en otra fila
                    f" \\hline \n"
                )

        tex_content += """
\\end{longtable}

\\vspace{1.5em}

% Tabla con registros
\\noindent \\textbf{Registros:} \\\\
\\begin{longtable}{|p{0.6\\textwidth}|p{0.2\\textwidth}|p{0.2\\textwidth}|}
    \\hline
    \\textbf{Acción} & \\textbf{Hora} & \\textbf{Usuario} \\\\
    \\hline
    \\endfirsthead
    \\hline
    \\textbf{Acción} & \\textbf{Hora} & \\textbf{Usuario} \\\\
    \\hline
    \\endhead
    \\hline
    \\endfoot
"""

        # Aquí añades la información de registros
        for registro_id in registros_ids:
            registro = db.execute(registro_table.select().where(registro_table.c.id == registro_id)).first()
            if registro:
                registro_usuario = db.execute(usuario_table.select().where(usuario_table.c.id == registro.id_usuario)).first()  # Obtener el usuario asociado
                tex_content += f"\\textbf{{{registro.descripcion}}} & {registro.creado} & {registro_usuario.nombre} \\\\ \n"

        tex_content += """
\\end{longtable}

\\vspace{1.5em}

\\noindent \\textbf{Notas:} \\\\"""
        tex_content += f" - {data.notas} \\\\" + """

\\vspace{4em}

\\noindent \\textbf{Firma:} \\\\
\\rule{5cm}{0.4pt} \\\\ % Línea para firma
Nombre del Firmante \\\\

\\end{document}
"""
        # Guardar el archivo .tex en el directorio fijo
        tex_file_path = os.path.join(OUTPUT_DIR, "documento.tex")
        pdf_file_path = os.path.join(OUTPUT_DIR, "documento.pdf")

        print(f"Creando archivo LaTeX en {tex_file_path}")  # LOG
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Generar el PDF usando pdflatex
        try:
            print(f"Ejecutando pdflatex para generar el PDF en {OUTPUT_DIR}")  # LOG
            result = subprocess.run(
                ['pdflatex', '-interaction=batchmode', '-output-directory', OUTPUT_DIR, tex_file_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("PDF generado correctamente.")  # LOG
        except subprocess.CalledProcessError as e:
            print("Error generando el PDF:", e.stderr.decode())  # LOG de error
            raise HTTPException(status_code=500, detail="Error generando el PDF")

        # Comprobar si el archivo PDF fue generado
        if not os.path.exists(pdf_file_path):
            print(f"Archivo PDF no encontrado en {pdf_file_path}")  # LOG
            raise HTTPException(status_code=500, detail="PDF no fue generado")
        else:
            print(f"Archivo PDF encontrado en {pdf_file_path}.")  # LOG adicional

        print(f"Enviando archivo PDF generado desde {pdf_file_path}")  # LOG
        return FileResponse(pdf_file_path, media_type='application/pdf', filename="documento.pdf")