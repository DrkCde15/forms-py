from flask import Flask, request, render_template, send_file
from docx import Document
from docx2pdf import convert
import google.generativeai as genai
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

# Configurar API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Configure a variável de ambiente GEMINI_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)

# Caminho do currículo base (Stephanie)
BASE_CURRICULO = r"C:\Users\Júlio César\Documents\Currículo\Currículo Stephanie Amarante - Área TI (1).docx"

def carregar_curriculo_base():
    """Lê o currículo base e retorna o texto"""
    doc = Document(BASE_CURRICULO)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def gerar_curriculo_arquivo(nome, resumo, objetivo, experiencias="", educacao="", habilidades=""):
    doc_texto = carregar_curriculo_base()

    prompt = f"""
Você é um assistente especialista em currículos.
Use o seguinte documento como referência de estrutura, estilo e organização:

DOCUMENTO BASE:
{doc_texto}

Agora crie um NOVO currículo com os dados abaixo, mantendo o mesmo estilo do documento base:

Nome: {nome}
Resumo Profissional: {resumo}
Objetivo Profissional: {objetivo}
Experiências: {experiencias if experiencias else "A definir"}
Formação: {educacao if educacao else "A informar"}
Habilidades: {habilidades if habilidades else "Versatilidade e capacidade de aprendizado"}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    texto_final = response.text

    novo_doc = Document()
    for linha in texto_final.split("\n"):
        linha = linha.strip()
        if linha:
            if any(x in linha.upper() for x in ["RESUMO", "OBJETIVO", "EXPERIÊNCIA", "FORMAÇÃO", "HABILIDADES"]) and len(linha) < 50:
                p = novo_doc.add_paragraph()
                run = p.add_run(linha)
                run.bold = True
            elif linha.isupper() and len(linha) < 80:
                p = novo_doc.add_paragraph()
                run = p.add_run(linha)
                run.bold = True
            else:
                novo_doc.add_paragraph(linha)

    tmp_dir = tempfile.mkdtemp()
    output_docx = os.path.join(tmp_dir, f"{nome.replace(' ', '_')}_Curriculo.docx")
    output_pdf = os.path.join(tmp_dir, f"{nome.replace(' ', '_')}_Curriculo.pdf")

    novo_doc.save(output_docx)
    try:
        convert(output_docx, output_pdf)
    except Exception:
        output_pdf = None

    return output_docx, output_pdf

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/gerar_curriculo", methods=["POST"])
def gerar_curriculo_route():
    nome = request.form.get("nome", "").strip()
    resumo = request.form.get("resumo", "").strip()
    objetivo = request.form.get("objetivo", "").strip()
    experiencias = request.form.get("experiencias", "").strip()
    educacao = request.form.get("educacao", "").strip()
    habilidades = request.form.get("habilidades", "").strip()

    if not nome or not resumo or not objetivo:
        return "Preencha todos os campos obrigatórios!", 400

    try:
        docx_path, pdf_path = gerar_curriculo_arquivo(nome, resumo, objetivo, experiencias, educacao, habilidades)
        return send_file(docx_path, as_attachment=True)
    except Exception as e:
        return f"Erro ao gerar currículo: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
