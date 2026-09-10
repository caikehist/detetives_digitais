from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import glob
import os
import re
import unicodedata

app = FastAPI(
    title="Mostra de Ciências - Detetives Digitais",
    description="Portfólio dos resultados da turma do 3º ano",
    version="1.0"
)

os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.globals["file_exists"] = lambda p: os.path.isfile(os.path.join("static", p))

RESULTADOS = [
    {
        "slug": "historias",
        "emoji": "📖",
        "titulo": "Histórias Digitais Ilustradas",
        "resumo": "Narrativas criadas coletivamente pelos alunos, combinando imaginação, escrita criativa e ferramentas digitais de ilustração.",
        "destaques": [
            "Histórias escritas em coletivo pela turma",
            "Ilustrações criadas com ferramentas digitais",
            "Leitura das histórias para os colegas com sonorização"
        ],
        "atividades": [
            "Criação de personagens e enredos em grupo",
            "Escrita e revisão coletiva dos textos",
            "Ilustração digital e apresentação final"
        ],
        "imagem": "img/historias.jpg"
    }
]


def slugify(nome):
    """Converte um nome de arquivo em um slug seguro para URL."""
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r"[^a-zA-Z0-9]+", "-", nome).strip("-").lower()
    return nome or "jogo"


def formatar_titulo(slug):
    """Transforma um slug de pasta em um título bonito: limpeza-da-represa -> Limpeza da Represa."""
    curtos = {"a", "e", "de", "da", "do", "das", "dos", "em", "na", "no", "o", "um", "uma", "com"}
    palavras = slug.split("-")
    partes = []
    for i, palavra in enumerate(palavras):
        if i == 0 or palavra.lower() not in curtos:
            partes.append(palavra.capitalize())
        else:
            partes.append(palavra.lower())
    return " ".join(partes)


def listar_jogos():
    """Descobre os jogos salvos em static/jogos/<nome>/index.html automaticamente."""
    jogos = []
    for caminho in sorted(glob.glob(os.path.join("static", "jogos", "*", "index.html"))):
        slug = os.path.basename(os.path.dirname(caminho))
        jogos.append({
            "slug": slug,
            "titulo": formatar_titulo(slug),
            "emoji": "🎮",
            "descricao": f"Jogo criado pela turma.",
            "arquivo": f"jogos/{slug}/index.html"
        })
    return jogos


def get_resultado(slug):
    for i, r in enumerate(RESULTADOS):
        if r["slug"] == slug:
            anterior = RESULTADOS[i - 1]
            proximo = RESULTADOS[(i + 1) % len(RESULTADOS)]
            return r, anterior, proximo
    return None


@app.get("/")
def read_index():
    return FileResponse("static/index.html")


def _renderizar_resultado(request: Request, slug: str):
    dados = get_resultado(slug)
    resultado, anterior, proximo = dados
    return templates.TemplateResponse(request, "resultado.html", {
        "request": request,
        "resultado": resultado,
        "anterior": anterior,
        "proximo": proximo,
        "mostrar_navegacao": len(RESULTADOS) > 1
    })


@app.get("/historias")
def historias(request: Request):
    return _renderizar_resultado(request, "historias")


@app.get("/jogos")
def galeria_jogos(request: Request):
    return templates.TemplateResponse(request, "galeria_jogos.html", {
        "request": request,
        "jogos": listar_jogos()
    })


@app.get("/jogos/{slug}")
def jogo(request: Request, slug: str):
    for j in listar_jogos():
        if j["slug"] == slug:
            return templates.TemplateResponse(request, "jogo.html", {
                "request": request,
                "jogo": j
            })
    return templates.TemplateResponse(
        request, "404.html", {"request": request}, status_code=404
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request, "404.html", {"request": request}, status_code=404
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)