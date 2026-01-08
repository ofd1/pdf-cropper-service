from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import fitz
import json
import base64
import os # Importante para ler a porta do Railway

app = FastAPI()

# Rota de teste (Health Check)
# Se você acessar a URL pura no navegador e aparecer isso, o site está vivo!
@app.get("/")
async def root():
    return {"status": "Serviço de Recorte Ativo", "rota_de_post": "/crop"}

@app.post("/crop")
async def crop_pdf(file: UploadFile = File(...), crops: str = Form(...)):
    try:
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        crops_list = json.loads(crops)
        
        results = []
        for crop in crops_list:
            page_idx = int(crop['page']) - 1
            if page_idx >= len(doc): continue
            
            page = doc[page_idx]
            p_w, p_h = page.rect.width, page.rect.height
            
            x0, y0 = float(crop['x']) * p_w, float(crop['y']) * p_h
            x1 = (float(crop['x']) + float(crop['width'])) * p_w
            y1 = (float(crop['y']) + float(crop['height'])) * p_h
            
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(x0, y0, x1, y1))
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            
            results.append({
                "type": crop.get('type', 'unknown'),
                "page": crop['page'],
                "image_data": img_b64
            })
            
        doc.close()
        return results
    except Exception as e:
        return {"error": str(e)}

# CONFIGURAÇÃO DE PORTA PARA O RAILWAY
if __name__ == "__main__":
    import uvicorn
    # O Railway passa a porta na variável de ambiente PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)