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
        
        crops_data = json.loads(crops)
        if isinstance(crops_data, str):
            crops_data = json.loads(crops_data)
        if isinstance(crops_data, dict):
            crops_data = [crops_data]

        results = []
        for crop in crops_data:
            if not isinstance(crop, dict):
                continue
                
            page_idx = int(crop.get('page', 1)) - 1
            if page_idx >= len(doc): continue
            
            page = doc[page_idx]
            p_w, p_h = page.rect.width, page.rect.height
            
            # --- CORREÇÃO DOS NOMES DAS CHAVES ---
            # O Lovable envia xRel, yRel, wRel, hRel
            x0 = float(crop['xRel']) * p_w
            y0 = float(crop['yRel']) * p_h
            x1 = (float(crop['xRel']) + float(crop['wRel'])) * p_w
            y1 = (float(crop['yRel']) + float(crop['hRel'])) * p_h
            # -------------------------------------
            
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
        # Retorna o erro detalhado para facilitar o debug no n8n
        return {"error": str(e), "tipo_recebido": str(type(crops)), "payload_recebido": str(crops)[:200]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)