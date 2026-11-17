"""Crea 50 casos guía UNSA en PostgreSQL de forma idempotente."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]


CASES = [
    ("Acceso", "Datos en aula virtual", "Un estudiante solicita los datos que conserva el aula virtual sobre su actividad.", "Identificar al titular, el sistema responsable, categorías de datos, finalidad y evidencia entregable.", "acceso estudiante aula virtual plataforma actividad historial"),
    ("Acceso", "Registros de inicio de sesión", "Un estudiante pide conocer sus accesos y dispositivos registrados en una plataforma UNSA.", "Distinguir datos del titular de registros que puedan revelar información de terceros o seguridad.", "acceso logs inicio sesion dispositivos seguridad plataforma"),
    ("Acceso", "Expediente de admisión", "Un postulante solicita copia de sus datos y documentos del proceso de admisión.", "Ubicar el expediente, verificar identidad y separar datos de evaluadores o terceros.", "acceso postulante admision expediente documentos identidad"),
    ("Acceso", "Historial de biblioteca", "Un estudiante solicita su historial de préstamos y sanciones de biblioteca.", "Determinar qué registros son personales, su origen, finalidad y plazo de conservación.", "acceso biblioteca prestamos sanciones historial estudiante"),
    ("Acceso", "Ficha de bienestar universitario", "Un estudiante pide acceso a información personal registrada por bienestar universitario.", "Considerar sensibilidad, canal seguro, identidad y alcance exacto de la solicitud.", "acceso bienestar salud sensible ficha estudiante"),
    ("Rectificación", "Nombre incorrecto", "El nombre de un estudiante aparece mal escrito en varios sistemas de la UNSA.", "Identificar fuente maestra, documentos de sustento y sistemas derivados que requieren sincronización.", "rectificacion nombre estudiante sistemas correccion identidad"),
    ("Rectificación", "Calificación controvertida", "Un estudiante pide cambiar una nota alegando que es un dato personal inexacto.", "Distinguir rectificación de datos objetivos del procedimiento académico para impugnar una evaluación.", "rectificacion nota calificacion reclamo academico estudiante"),
    ("Rectificación", "Correo desactualizado", "Un egresado solicita actualizar su correo y teléfono de contacto.", "Verificar identidad, localizar réplicas y registrar la actualización sin alterar evidencia histórica necesaria.", "rectificacion egresado correo telefono actualizacion"),
    ("Rectificación", "Datos de grado", "Un egresado detecta un error en la información usada para emitir una constancia.", "Revisar fuente oficial, trazabilidad del cambio e impacto en documentos ya emitidos.", "rectificacion grado constancia egresado error registro"),
    ("Rectificación", "Contacto de emergencia", "Un estudiante informa que su contacto de emergencia ya no es válido.", "Actualizar el dato con un flujo autenticado y considerar que también contiene datos de un tercero.", "rectificacion contacto emergencia tercero estudiante"),
    ("Supresión", "Cuenta de egresado", "Un egresado solicita eliminar su cuenta y todos sus datos de servicios universitarios.", "Separar datos eliminables de expedientes sujetos a conservación y explicar el alcance posible.", "supresion egresado cuenta eliminacion conservacion"),
    ("Supresión", "Postulante no admitido", "Un postulante no admitido solicita borrar los documentos que presentó.", "Revisar finalidad agotada, plazos aplicables, respaldos y obligaciones de conservación.", "supresion postulante no admitido documentos retencion"),
    ("Supresión", "Antecedente disciplinario", "Un estudiante solicita eliminar un registro disciplinario antiguo.", "Comprobar vigencia, archivo institucional y restricciones antes de concluir que procede la eliminación.", "supresion disciplinario estudiante archivo conservacion"),
    ("Supresión", "Participante de investigación", "Una persona retira su participación y pide eliminar sus datos de un estudio UNSA.", "Revisar consentimiento, anonimización, etapa del estudio y compromisos éticos documentados.", "supresion investigacion participante consentimiento anonimización"),
    ("Supresión", "Cierre de plataforma", "Un alumno pide eliminar su perfil de una aplicación usada en un curso.", "Precisar quién controla la plataforma, qué copia conserva el proveedor y qué registros académicos subsisten.", "supresion plataforma curso proveedor perfil estudiante"),
    ("Consentimiento", "Fotografías institucionales", "La UNSA quiere publicar fotografías identificables de estudiantes en una campaña.", "Examinar finalidad, información previa, base aplicable, revocación y canales de publicación.", "consentimiento fotos estudiantes campaña imagen publicacion"),
    ("Consentimiento", "Control biométrico", "Una dependencia propone usar reconocimiento facial para controlar asistencia.", "Evaluar necesidad, proporcionalidad, alternativas menos invasivas y protección de datos biométricos.", "consentimiento biometria reconocimiento facial asistencia"),
    ("Consentimiento", "Encuesta de investigación", "Un equipo investigador recopilará salud y opiniones de estudiantes.", "Revisar información al participante, minimización, finalidad, acceso y medidas para datos sensibles.", "consentimiento investigacion encuesta salud sensibles"),
    ("Consentimiento", "Mensajes promocionales", "Una oficina desea enviar publicidad de cursos a correos de egresados.", "Comprobar finalidad original, opción de oposición o baja y registro de preferencias.", "consentimiento marketing correos egresados cursos oposicion"),
    ("Consentimiento", "Actividad con menores", "Un programa de extensión recopila imágenes y datos de escolares menores de edad.", "Identificar representación, autorización, información adecuada y protección reforzada.", "consentimiento menores escolares extension imagen"),
    ("Incidentes", "Filtración de calificaciones", "Una hoja con nombres, correos y notas quedó accesible públicamente.", "Contener el acceso, preservar evidencia, evaluar alcance, responsables y comunicaciones necesarias.", "incidente filtracion notas calificaciones correos publico"),
    ("Incidentes", "Laptop institucional robada", "Se roba una laptop que almacenaba expedientes de estudiantes.", "Determinar cifrado, acceso remoto, categorías afectadas, copias y respuesta documentada.", "incidente laptop robo expedientes cifrado estudiantes"),
    ("Incidentes", "Cuenta docente comprometida", "Una campaña de phishing compromete el correo de un docente.", "Revocar sesiones, proteger credenciales, revisar accesos y determinar exposición de datos personales.", "incidente phishing docente correo credenciales acceso"),
    ("Incidentes", "Correo al destinatario equivocado", "Una oficina envía un expediente estudiantil a una persona incorrecta.", "Intentar recuperación segura, evaluar sensibilidad, documentar el incidente y evitar reenvíos.", "incidente correo equivocado expediente estudiante"),
    ("Incidentes", "Archivo compartido sin restricción", "Un enlace permite descargar datos de estudiantes sin autenticación.", "Deshabilitar el enlace, conservar registros de acceso y evaluar cantidad y naturaleza de afectados.", "incidente enlace archivo compartido acceso estudiantes"),
    ("Conservación", "Expedientes de admisión", "La oficina conserva indefinidamente expedientes de todos los postulantes.", "Relacionar cada categoría con finalidad, plazo documentado, archivo y eliminación segura.", "retencion conservacion admision postulantes expedientes"),
    ("Conservación", "Datos de egresados", "Se mantienen teléfonos y direcciones de egresados sin uso definido.", "Separar registros académicos permanentes de datos de contacto cuya finalidad pudo terminar.", "retencion egresados contacto archivo finalidad"),
    ("Conservación", "Grabaciones de videovigilancia", "La universidad conserva grabaciones de cámaras durante varios años.", "Revisar finalidad de seguridad, acceso, incidentes asociados y plazo proporcional.", "retencion videovigilancia camaras grabaciones seguridad"),
    ("Conservación", "Base de investigación", "Una investigación terminó, pero conserva identificadores directos de participantes.", "Evaluar anonimización, compromisos informados y necesidad de conservar datos identificables.", "retencion investigacion anonimización participantes"),
    ("Conservación", "Copias de respaldo", "Datos eliminados siguen presentes en respaldos institucionales.", "Distinguir uso operativo de respaldo, ciclos de sobrescritura y controles contra restauración indebida.", "retencion backups respaldo eliminacion restauracion"),
    ("Proveedores", "Aula virtual en la nube", "La UNSA contrata una plataforma que procesa actividad y evaluaciones.", "Precisar roles, instrucciones, seguridad, subcontratación, devolución y eliminación de datos.", "proveedor nube aula virtual contrato evaluaciones"),
    ("Proveedores", "Sistema de biblioteca", "Un proveedor externo administra préstamos y perfiles de usuarios.", "Revisar acceso del proveedor, finalidad contractual, incidentes y terminación del servicio.", "proveedor biblioteca prestamos contrato acceso"),
    ("Proveedores", "Investigación internacional", "Datos de participantes serán compartidos con una universidad extranjera.", "Identificar destinatario, país, finalidad, garantías, minimización e información al titular.", "transferencia internacional investigacion universidad extranjera"),
    ("Proveedores", "Servicio de correo", "Un servicio externo filtra automáticamente mensajes institucionales.", "Revisar metadatos y contenido tratado, ubicación, retención y medidas contractuales.", "proveedor correo nube transferencia metadatos"),
    ("Proveedores", "Subcontratista no informado", "El proveedor de una aplicación incorpora otro procesador de datos.", "Comprobar autorización, transparencia, garantías equivalentes y actualización del registro.", "proveedor subcontratista encargado datos contrato"),
    ("Publicación", "Transparencia y datos personales", "Una solicitud de transparencia pide documentos con datos de estudiantes.", "Separar información pública, datos personales y posibles técnicas de disociación.", "transparencia acceso informacion publica estudiantes datos"),
    ("Publicación", "Tesis con datos identificables", "Una tesis publicada contiene nombres de participantes entrevistados.", "Revisar consentimiento, necesidad de identificación, anonimización y corrección del repositorio.", "tesis repositorio nombres participantes anonimización"),
    ("Publicación", "Lista pública de notas", "Una escuela publica calificaciones junto con nombres completos.", "Evaluar finalidad, minimización, canal, audiencia y alternativas con identificadores menos expuestos.", "publicacion notas nombres estudiantes minimizacion"),
    ("Publicación", "Grabación de clases", "Una clase grabada con intervenciones de estudiantes se publica en internet.", "Distinguir uso docente interno de publicación abierta y revisar información y controles de acceso.", "grabacion clases estudiantes publicacion internet"),
    ("Publicación", "Directorio estudiantil", "Se propone publicar correos y teléfonos de delegados estudiantiles.", "Limitar campos, audiencia, vigencia, propósito y mecanismo de actualización u oposición.", "directorio estudiantes correos telefonos publicacion"),
    ("Derechos", "Oposición a campañas", "Un egresado pide dejar de recibir invitaciones y publicidad institucional.", "Registrar la preferencia y diferenciar comunicaciones promocionales de avisos necesarios.", "oposicion marketing egresado comunicaciones"),
    ("Derechos", "Revocación de uso de imagen", "Una estudiante revoca el permiso para usar su fotografía.", "Localizar publicaciones controladas por la UNSA, evaluar alcance futuro y documentar las acciones.", "revocacion consentimiento imagen fotografia estudiante"),
    ("Derechos", "Supervisión automatizada", "Un sistema de evaluación remota toma decisiones o alertas automáticas.", "Explicar funcionamiento relevante, intervención humana, exactitud y vías de revisión.", "automatizada proctoring evaluacion decisiones estudiante"),
    ("Derechos", "Portabilidad académica", "Un estudiante solicita sus datos académicos en formato reutilizable.", "Definir datos aportados u observados, formato seguro y límites frente a documentos de terceros.", "portabilidad datos academicos formato estudiante"),
    ("Derechos", "Solicitud por representante", "Un familiar solicita datos de un estudiante alegando representarlo.", "Verificar identidad, representación, alcance del poder y canal de entrega antes de revelar información.", "representante acceso familiar identidad poder estudiante"),
    ("Operación", "Verificación de identidad", "Una oficina recibe por correo una solicitud de acceso con pocos datos.", "Aplicar verificación proporcional sin recopilar información excesiva y usar un canal seguro.", "identidad solicitud acceso verificacion correo"),
    ("Operación", "Solicitud accesible", "Una persona con discapacidad no puede usar el formulario digital de derechos.", "Ofrecer un canal alternativo equivalente y conservar trazabilidad de la atención.", "accesibilidad derechos formulario canal alternativo"),
    ("Operación", "Datos del personal", "Un trabajador solicita conocer evaluaciones y registros sobre su desempeño.", "Identificar datos propios, información de terceros, finalidad laboral y canal autenticado.", "trabajador personal acceso evaluacion desempeño"),
    ("Operación", "Denuncia de privacidad", "Un estudiante denuncia uso indebido de sus datos por una dependencia.", "Registrar hechos, preservar evidencia, evitar represalias y derivar al responsable competente.", "denuncia privacidad estudiante evidencia responsable"),
    ("Operación", "Supresión con bloqueo de conservación", "Una solicitud de eliminación afecta información vinculada a un procedimiento pendiente.", "Explicar qué datos no pueden eliminarse aún, aislar su uso y documentar la condición de conservación.", "supresion bloqueo legal procedimiento pendiente conservacion"),
]


def seed():
    from dsar_api import create_app
    from dsar_api.extensions import db
    from dsar_api.models import InstitutionalCaseGuide

    app = create_app()
    with app.app_context():
        db.create_all()
        for index, (area, title, scenario, focus, keywords) in enumerate(CASES, 1):
            code = f"UNSA-CG-{index:03d}"
            row = InstitutionalCaseGuide.query.filter_by(code=code).first()
            if row is None:
                row = InstitutionalCaseGuide(code=code)
                db.session.add(row)
            row.title, row.area, row.scenario = title, area, scenario
            row.reasoning_focus, row.keywords, row.active = focus, keywords, True
        db.session.commit()
        return InstitutionalCaseGuide.query.filter_by(active=True).count()


def main():
    count = seed()
    print(f"Casos guía UNSA activos: {count}")
    return 0 if count >= 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
