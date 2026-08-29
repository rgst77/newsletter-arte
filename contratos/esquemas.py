from datetime import datetime

from pydantic import BaseModel, Field


class SolicitudNewsletter(BaseModel):
    siglo: str = Field(..., description="Siglo o periodo a tratar, ej. 'siglo XIX'")
    disciplina: str = Field(
        default="cualquiera", description="escultura, arquitectura, pintura o 'cualquiera'"
    )


class FuenteCitada(BaseModel):
    titulo: str
    url: str


class ResultadoBusqueda(BaseModel):
    titulo: str
    url: str
    fragmento: str


class NotasAutor(BaseModel):
    nombre: str
    corriente: str = Field(..., description="Corriente o movimiento artístico, ej. 'Romanticismo'")
    periodo: str = Field(..., description="Años o rango concreto dentro del siglo")
    notas: str = Field(..., description="Biografía y contexto en bruto")
    titulos_obras_conocidas: list[str] = Field(
        default_factory=list,
        description="Títulos concretos de obras mencionadas, para que el bot de imágenes busque cada una en vez de solo el nombre del autor",
    )
    fuentes: list[FuenteCitada]


class ImagenObra(BaseModel):
    titulo_obra: str
    url_imagen: str
    url_fuente: str
    fuente: str = Field(..., description="'The Met Open Access' o 'Wikimedia Commons'")
    creditos: str = Field(default="", description="Autor/licencia para atribución en el newsletter")


class FlashcardNewsletter(BaseModel):
    nombre: str
    corriente: str
    periodo: str
    biografia: str = Field(..., description="3 a 5 frases sobre el autor")
    imagenes: list[ImagenObra]
    generado_en: datetime = Field(default_factory=datetime.now)


class NewsletterVerificado(BaseModel):
    flashcard: FlashcardNewsletter
    fiabilidad: str = Field(..., description="alta, media o baja")
    advertencias: list[str] = Field(default_factory=list)


class RegistroEnvio(BaseModel):
    nombre: str
    corriente: str
    periodo: str
    siglo: str
    archivo_html: str = Field(
        default="", description="Ruta relativa en el repo al HTML enviado, para archivo público"
    )
    fecha_envio: datetime = Field(default_factory=datetime.now)


class AutorCatalogo(BaseModel):
    nombre: str
    disciplina: str = Field(..., description="escultura, arquitectura, pintura, poesía, etc.")
    siglo: str
    corriente_orientativa: str = Field(
        default="", description="Pista inicial para el Investigador; puede refinarla con lo que encuentre"
    )
