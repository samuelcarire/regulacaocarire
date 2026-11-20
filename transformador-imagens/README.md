# 🎨 Transformador de Imagens com IA

Site simples onde você envia uma foto e a IA cria uma nova versão dela num estilo
(anime, aquarela, pintura a óleo, animação 3D, lápis, cyberpunk, quadrinhos, pixel art)
ou seguindo uma descrição sua. **Gratuito**: roda no seu computador ou no Google Colab.

- Modelo: [SDXL-Turbo](https://huggingface.co/stabilityai/sdxl-turbo) (rápido, 4 passos)
- Interface: Gradio (abre no navegador)
- Filtro de segurança: bloqueia nudez/conteúdo sexual na foto enviada, no resultado e no texto

> Licença do SDXL-Turbo: uso pessoal/não comercial é livre. Para uso comercial é
> preciso a licença da Stability AI — ou troque o modelo pela variável `MODEL_ID`.

## Opção 1 — Google Colab (grátis, sem precisar de placa de vídeo)

1. Acesse https://colab.research.google.com e crie um notebook novo.
2. Menu **Ambiente de execução → Alterar o tipo de ambiente** → escolha **GPU T4**.
3. No painel de arquivos (ícone de pasta à esquerda), envie o `app.py`.
4. Rode numa célula:
   ```
   !pip install -q diffusers transformers accelerate gradio
   !python app.py --share
   ```
5. Aguarde o download do modelo (~7 GB, alguns minutos) e clique no link
   `https://....gradio.live` que aparecer. Esse link funciona por até 72 h
   e pode ser aberto no celular ou compartilhado.

## Opção 2 — No seu computador

Requisitos recomendados: placa NVIDIA com 8 GB+ de VRAM (ou Mac M1/M2/M3).
Sem GPU funciona, mas fica bem lento (minutos por imagem).

```bash
cd transformador-imagens
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/Mac: source .venv/bin/activate
# Instale o PyTorch conforme sua placa: https://pytorch.org/get-started/locally/
pip install -r requirements.txt
python app.py            # abre em http://127.0.0.1:7860
python app.py --share    # também cria link público temporário
```

## Dicas de uso

- **Intensidade** baixa (0.3–0.5) mantém o rosto/composição; alta (0.7–0.9) muda mais.
- A **descrição extra** funciona melhor em inglês (ex.: `wearing a red jacket, beach background`).
- Gostou de um resultado? Anote a **semente** para reproduzi-lo.
