import streamlit as st
import hashlib, json
from time import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# ------------------------ Seguridad y claves ------------------------ #
def generate_keys():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    pub_str = pub.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return priv, pub, pub_str

# ------------------------ Préstamo Educativo ------------------------ #
class CourseLoan:
    def __init__(self, user, course_name, amount, timestamp):
        self.user = user
        self.course_name = course_name
        self.amount = amount
        self.timestamp = timestamp
        self.completed = False
        self.penalized = False
        self.final_amount_due = amount

    def check_completion(self):
        elapsed = time() - self.timestamp
        return elapsed >= 30

    def apply_penalty(self, base_rate=0.005, delay_penalty=0.015, extra_per_10s=0.005):
        self.penalized = True
        elapsed = time() - self.timestamp
        overdue = max(0, elapsed - 30)
        extra_blocks = int(overdue // 10)
        total_rate = base_rate + delay_penalty + (extra_blocks * extra_per_10s)
        self.final_amount_due = round(self.amount * (1 + total_rate), 2)

# ------------------------ Streamlit UI ------------------------ #
st.set_page_config(page_title="Mantequillas voladoras finance", layout="wide")
st.title("📚 Mantequillas voladoras finance: Plataforma DeFi Educativa")
st.markdown(""" 
> 💰 **Tasa de interés base:** 0.5% mensual  
> 🔥 **Penalización por retraso:** +1.5% mensual  
> ⏳ **Interés adicional por cada 10 segundos extra:** +0.5% mensual

Completa a tiempo y el préstamo es virtualmente gratuito. Si no... bienvenido al capitalismo gamificado.
""")

if 'users' not in st.session_state:
    st.session_state.users = {}

if 'loans' not in st.session_state:
    st.session_state.loans = []

# ------------------------ Crear usuario ------------------------ #
with st.sidebar:
    st.header("👤 Crear nuevo usuario")
    username = st.text_input("Nombre del usuario")
    if st.button("Generar claves") and username:
        priv, pub, pub_str = generate_keys()
        st.session_state.users[username] = {
            'private': priv,
            'public': pub,
            'pub_str': pub_str,
            'balance': 0
        }
        st.success(f"Usuario {username} creado.")

# ------------------------ Ver usuarios ------------------------ #
st.subheader("👥 Usuarios registrados")
for user in st.session_state.users:
    st.text(f"• {user}")

# ------------------------ Solicitar curso ------------------------ #
st.subheader("📖 Solicitar curso con préstamo")
if st.session_state.users:
    user_list = list(st.session_state.users.keys())
    selected_user = st.selectbox("Seleccionar usuario", user_list)
    st.markdown("### 🎓 Selecciona un curso disponible")
    courses = [
        {"nombre": "Curso de Python", "institucion": "Capacitarte", "tokens": 52, "duracion": "4 semanas"},
        {"nombre": "Curso de Desarrollo Web: HTML5, CSS y JavaScript", "institucion": "Capacitarte", "tokens": 115, "duracion": "6 semanas"},
        {"nombre": "Curso de SQL para Análisis de Datos", "institucion": "EBAC", "tokens": 100, "duracion": "2 meses"},
        {"nombre": "Curso de Herramientas Esenciales de Excel", "institucion": "CESDE", "tokens": 336, "duracion": "5 semanas"},
        {"nombre": "Diplomado en Costos", "institucion": "Politécnico de Colombia", "tokens": 0, "duracion": "5 semanas"},
        {"nombre": "Curso de Photoshop Personalizado", "institucion": "Academia Cecap", "tokens": 490, "duracion": "12 horas"},
        {"nombre": "Curso de Illustrator", "institucion": "Academia Cecap", "tokens": 80, "duracion": "10 horas"},
        {"nombre": "Curso de Robótica Educativa para Profesores", "institucion": "Academia Cecap", "tokens": 570, "duracion": "30 horas"},
        {"nombre": "Curso de Programación en Python", "institucion": "Universidad de los Andes", "tokens": 0, "duracion": "4 semanas"},
        {"nombre": "Curso de Gestión de Contenidos y SEO", "institucion": "CESDE", "tokens": 336, "duracion": "4 semanas"},
        {"nombre": "Curso de AutoCAD 2D", "institucion": "Capacitarte", "tokens": 36, "duracion": "3 semanas"},
    ]

    course_labels = [f"{c['nombre']} ({c['institucion']} - {c['tokens']} tokens)" for c in courses]
    selected_course_index = st.selectbox("Cursos disponibles", range(len(course_labels)), format_func=lambda i: course_labels[i])
    selected_course = courses[selected_course_index]
    st.markdown(f"🕒 **Duración del curso:** {selected_course['duracion']}")


    if st.button("Solicitar curso"):
        loan = CourseLoan(selected_user, selected_course["nombre"], selected_course["tokens"], time())
        loan.institucion = selected_course["institucion"]
        loan.duracion = selected_course["duracion"]
        st.session_state.loans.append(loan) 
        st.success(f"{selected_user} ha solicitado el curso '{selected_course['nombre']}' por {selected_course['tokens']} tokens.")
        st.info("⏳ Recuerda: debes completarlo en el tiempo estipulado para evitar intereses extras.")




# ------------------------ Completar curso ------------------------ #
st.subheader("✅ Completar curso")
active_loans = [loan for loan in st.session_state.loans if not loan.completed]

if active_loans:
    for loan in active_loans:
        with st.expander(f"{loan.user} | Curso: {loan.course_name} | Monto: {loan.amount} tokens"):
            if loan.check_completion():
                if st.button(f"Marcar como completado ({loan.course_name})", key=f"complete_{loan.course_name}_{loan.user}"):
                    loan.completed = True
                    st.success("🎉 Curso completado a tiempo. Sin penalización.")
            else:
                st.warning("⏳ Debes esperar al menos 30 segundos para completarlo.")
                if st.button(f"Intentar completar anticipadamente ({loan.course_name})", key=f"fail_{loan.course_name}_{loan.user}"):
                    loan.completed = True
                    loan.apply_penalty()
                    st.error(f"😬 ¡Muy pronto! Penalización aplicada. Nueva deuda: {loan.final_amount_due} tokens.")
else:
    st.info("No hay cursos activos para completar.")

# ------------------------ Historial de préstamos ------------------------ #
st.subheader("📜 Historial de préstamos")
if st.session_state.loans:
    for loan in st.session_state.loans:
        status = "✅ Completado" if loan.completed else "🕓 En progreso"
        if loan.penalized:
            porcentaje = round(((loan.final_amount_due / loan.amount) - 1) * 100, 2)
            status += f" | 💸 Penalizado con {porcentaje}% interés"
        st.markdown(f"""
        **Usuario:** {loan.user}  
        **Curso:** {loan.course_name}  
        **Institución:** {getattr(loan, 'institucion', 'Desconocida')}  
        **Duración:** {getattr(loan, 'duracion', 'No especificada')}  
        **Monto original:** {loan.amount} tokens  
        **Monto final:** {loan.final_amount_due} tokens  
        **Estado:** {status}  
        **Tiempo transcurrido:** {round(time() - loan.timestamp)} segundos  
        ---
        """)
else:
    st.info("Todavía no hay préstamos registrados.")
