#!/usr/bin/env python3
"""
Script para executar a API FastAPI
Uso: python run.py
"""

if __name__ == "__main__":
    from api.main import app
    import uvicorn
    from api.config import HOST, PORT, DEBUG

    print(f"""
    ╔════════════════════════════════════════════╗
    ║  🚀 ComparaEstoque API - FastAPI Server   ║
    ╠════════════════════════════════════════════╣
    ║  📍 Host: {HOST:30} ║
    ║  📍 Port: {PORT:30} ║
    ║  🔧 Debug: {str(DEBUG):29} ║
    ║  📚 Docs: http://{HOST}:{PORT}/docs{' ' * 17} ║
    ╚════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
