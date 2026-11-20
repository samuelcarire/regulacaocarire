"""
Transformador de Imagens com IA (img2img)

Envie uma foto e a IA cria uma nova versão dela num estilo escolhido
(anime, aquarela, pintura a óleo, 3D, lápis etc.).

Usa o modelo SDXL-Turbo (Stability AI) via biblioteca diffusers.
Roda de graça no seu computador (ideal com placa NVIDIA) ou no Google Colab.

Inclui filtro de segurança: imagens de entrada ou saída com nudez/conteúdo
sexual são bloqueadas, e prompts com termos desse tipo são recusados.

Uso:
    python app.py            # abre em http://127.0.0.1:7860
    python app.py --share    # gera também um link público temporário (*.gradio.live)
"""

import argparse
import os
import random
import re
import unicodedata
from functools import lru_cache

from PIL import Image

MODEL_ID = os.getenv("MODEL_ID", "stabilityai/sdxl-turbo")
SAFETY_MODEL_ID = "CompVis/stable-diffusion-safety-checker"
CLIP_PROCESSOR_ID = "openai/clip-vit-base-patch32"

MAX_LADO = 768  # maior lado da imagem processada (px)

ESTILOS = {
    "Anime": "anime style illustration, vibrant colors, clean line art, studio quality",
    "Aquarela": "delicate watercolor painting, soft washes, paper texture, artistic",
    "Pintura a óleo": "classical oil painting, thick brush strokes, rich colors, museum quality",
    "Animação 3D": "3d animated movie character style, soft lighting, cute, highly detailed render",
    "Desenho a lápis": "detailed graphite pencil sketch, black and white, cross hatching",
    "Cyberpunk": "cyberpunk style, neon lights, futuristic city, cinematic lighting",
    "Quadrinhos": "comic book style, bold ink outlines, halftone shading, pop art colors",
    "Pixel art": "pixel art, 16-bit retro video game style",
    "Apenas o meu texto": "",
}

# Termos que fazem o pedido ser recusado (português e inglês).
TERMOS_BLOQUEADOS = [
    r"nu", r"nua", r"nus", r"nuas", r"nud[aoe]s?", r"nudez", r"nudity", r"naked", r"pelad[ao]s?", r"sem roupas?",
    r"despid[ao]s?", r"tirar (a )?roupa", r"undress\w*", r"nsfw", r"topless",
    r"seios?", r"peitos?", r"mamilos?", r"nipples?", r"breasts?", r"boobs?",
    r"genita\w*", r"penis", r"vagina", r"bunda", r"butt", r"sexy", r"sexo", r"sexua\w*", r"porn\w*",
    r"erotic\w*", r"erotic[ao]s?", r"lingerie", r"calcinha", r"sutia", r"bikini",
    r"biquini", r"hentai", r"fetish\w*", r"fetiche\w*",
]
_REGEX_BLOQUEIO = re.compile(r"\b(" + "|".join(TERMOS_BLOQUEADOS) + r")\b", re.IGNORECASE)


def _sem_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def prompt_bloqueado(texto: str) -> bool:
    """True se o texto pedir conteúdo adulto."""
    return bool(_REGEX_BLOQUEIO.search(_sem_acentos(texto or "")))


def preparar_imagem(img: Image.Image) -> Image.Image:
    """Converte para RGB e redimensiona mantendo proporção, com lados múltiplos de 64."""
    img = img.convert("RGB")
    largura, altura = img.size
    escala = MAX_LADO / max(largura, altura)
    nova_l = max(64, int(round(largura * escala / 64)) * 64)
    nova_a = max(64, int(round(altura * escala / 64)) * 64)
    return img.resize((nova_l, nova_a), Image.LANCZOS)


def montar_prompt(estilo: str, texto: str) -> str:
    partes = [ESTILOS.get(estilo, ""), (texto or "").strip()]
    partes = [p for p in partes if p]
    return ", ".join(partes) + ", fully clothed, safe for work" if partes else ""


@lru_cache(maxsize=1)
def carregar_modelos():
    """Carrega os modelos uma única vez (o primeiro uso baixa ~7 GB)."""
    import torch
    from diffusers import AutoPipelineForImage2Image
    from diffusers.pipelines.stable_diffusion.safety_checker import (
        StableDiffusionSafetyChecker,
    )
    from transformers import CLIPImageProcessor

    if torch.cuda.is_available():
        device, dtype, variant = "cuda", torch.float16, "fp16"
    elif torch.backends.mps.is_available():
        device, dtype, variant = "mps", torch.float16, "fp16"
    else:
        device, dtype, variant = "cpu", torch.float32, None
        print("AVISO: sem GPU detectada. Vai funcionar, mas cada imagem pode levar minutos.")

    pipe = AutoPipelineForImage2Image.from_pretrained(
        MODEL_ID, torch_dtype=dtype, variant=variant
    ).to(device)
    pipe.set_progress_bar_config(disable=True)

    checker = StableDiffusionSafetyChecker.from_pretrained(SAFETY_MODEL_ID).to(device)
    processador = CLIPImageProcessor.from_pretrained(CLIP_PROCESSOR_ID)
    return torch, pipe, checker, processador, device


def contem_nudez(img: Image.Image) -> bool:
    """Usa o safety checker do Stable Diffusion para detectar conteúdo adulto."""
    import numpy as np

    torch, _, checker, processador, device = carregar_modelos()
    entrada = processador(images=img, return_tensors="pt").pixel_values.to(device)
    arr = np.array(img, dtype=np.float32)[None] / 255.0
    with torch.no_grad():
        _, flags = checker(images=arr, clip_input=entrada)
    return bool(flags[0])


def transformar(imagem, estilo, texto, intensidade, semente):
    if imagem is None:
        raise ValueError("Envie uma imagem primeiro.")
    if prompt_bloqueado(texto):
        return None, "⛔ Pedido recusado: este app não gera nudez nem conteúdo sexual."

    prompt = montar_prompt(estilo, texto)
    if not prompt:
        return None, "Escolha um estilo ou escreva uma descrição."

    torch, pipe, _, _, device = carregar_modelos()
    img = preparar_imagem(imagem)

    if contem_nudez(img):
        return None, "⛔ A imagem enviada foi bloqueada pelo filtro de conteúdo adulto."

    semente = int(semente) if semente and int(semente) >= 0 else random.randint(0, 2**31 - 1)
    gerador = torch.Generator(device="cpu").manual_seed(semente)

    # SDXL-Turbo: poucos passos e sem guidance. passos * intensidade precisa ser >= 1.
    resultado = pipe(
        prompt=prompt,
        image=img,
        strength=float(intensidade),
        num_inference_steps=4,
        guidance_scale=0.0,
        generator=gerador,
    ).images[0]

    if contem_nudez(resultado):
        return None, "⛔ O resultado foi bloqueado pelo filtro de conteúdo adulto. Tente outro estilo."

    return resultado, f"✅ Pronto! Semente usada: {semente} (use a mesma para repetir o resultado)."


def criar_interface():
    import gradio as gr

    with gr.Blocks(title="Transformador de Imagens") as demo:
        gr.Markdown(
            "# 🎨 Transformador de Imagens com IA\n"
            "Envie uma foto, escolha um estilo e a IA cria uma nova versão dela. "
            "Conteúdo adulto é bloqueado."
        )
        with gr.Row():
            with gr.Column():
                entrada = gr.Image(type="pil", label="Sua imagem")
                estilo = gr.Dropdown(list(ESTILOS), value="Anime", label="Estilo")
                texto = gr.Textbox(
                    label="Descrição extra (opcional, em inglês funciona melhor)",
                    placeholder="ex.: wearing a red jacket, sunset background",
                )
                intensidade = gr.Slider(
                    0.3, 0.9, value=0.55, step=0.05,
                    label="Intensidade (baixo = parecido com a original, alto = mais criativo)",
                )
                semente = gr.Number(value=-1, precision=0, label="Semente (-1 = aleatória)")
                botao = gr.Button("Transformar", variant="primary")
            with gr.Column():
                saida = gr.Image(label="Resultado", format="png")
                status = gr.Markdown()

        botao.click(
            transformar,
            inputs=[entrada, estilo, texto, intensidade, semente],
            outputs=[saida, status],
        )
    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="gera link público temporário")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    print("Carregando modelos (na primeira vez baixa ~7 GB, pode demorar)...")
    carregar_modelos()
    criar_interface().queue().launch(share=args.share, server_port=args.port)
