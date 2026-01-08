from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import fitz
import json
import base64
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Serviço Ativo", "dica": "Use POST em /crop"}

@app.post("/crop")
async def crop_pdf(file: UploadFile = File(...), crops: str = Form(...)):
    try:
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        # --- LÓGICA ANTI-ERRO PARA O JSON ---
        crops_data = json.loads(crops)
        # Se o n8n mandou como string dentro de string, carregamos de novo
        if isinstance(crops_data, str):
            crops_data = json.loads(crops_data)
        # Se mandou apenas um objeto fora de uma lista, transformamos em lista
        if isinstance(crops_data, dict):
            crops_data = [crops_data]
        # -------------------------------------

        results = []
        for crop in crops_data:
            # Proteção: Verifica se crop é realmente um dicionário
            if not isinstance(crop, dict):
                continue
                
            page_idx = int(crop.get('page', 1)) - 1
            if page_idx >= len(doc): continue
            
            page = doc[page_idx]
            p_w, p_h = page.rect.width, page.rect.height
            
            x0 = float(crop['x']) * p_w
            y0 = float(crop['y']) * p_h
            x1 = (float(crop['x']) + float(crop['width'])) * p_w
            y1 = (float(crop['y']) + float(crop['height'])) * p_h
            
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(x0, y0, x1, y1))
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            
            results.append({
                "type": crop.get('type', 'unknown'),
                "page": page_idx + 1,
                "image_data": img_b64
            })
            
        doc.close()
        return results
    except Exception as e:
        return {"error": str(e), "tipo_recebido": str(type(crops))}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)