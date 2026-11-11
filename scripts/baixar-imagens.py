#!/usr/bin/env python3
"""Baixa renders transparentes já existentes em websites de imagens.

Execute na raiz do projeto com internet: python3 scripts/baixar-imagens.py
Imagens de terceiros: uso pessoal/não comercial e sujeito aos direitos dos titulares.
Em caso de bloqueio automático no host de origem, faça o download manualmente.
"""
import argparse
import struct
import urllib.error
import urllib.request
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent / 'frontend' / 'public' / 'characters'
ASSETS={
    'kitty':'https://www.citypng.com/public/uploads/preview/sweet-portrait-of-hello-kitty-waving-hd-transparent-png-735811696611595jr36apxzjp.png?v=2025103105',
    'pony':'https://www.clipartmax.com/png/middle/199-1990134_fluttershy-happy-by-the3javi-fluttershy-face-happy-mlp-fluttershy-standing.png',
    'snoopy':'https://pnggallery.com/wp-content/uploads/snoopy-01.png',
    'amelie':'https://w7.pngwing.com/pngs/627/860/png-transparent-amelie-poulain-computer-icons-others-child-face-black-hair.png',
    'coraline':'https://pnggallery.com/wp-content/uploads/coraline-01.png',
}

def validate_png(content:bytes)->tuple[int,int]:
    if len(content)<33 or content[:8]!=b'\x89PNG\r\n\x1a\n' or content[12:16]!=b'IHDR':
        raise ValueError('A resposta não é um arquivo PNG válido')
    width,height,depth,color=struct.unpack('>IIBB',content[16:26])
    if not 30<=width<=10000 or not 30<=height<=10000:
        raise ValueError('Dimensões inesperadas para a imagem')
    # Truecolor alpha (6), grayscale alpha (4), or indexed transparency (3 + tRNS)
    if color not in (4,6) and not (color==3 and b'tRNS' in content):
        raise ValueError('O arquivo não informa um canal alfa/transparência')
    return width,height

def main():
    parser=argparse.ArgumentParser(description='Baixar PNGs transparentes para uso pessoal no Alice Finanças')
    parser.add_argument('--verify',action='store_true',help='Apenas verificar os arquivos locais')
    args=parser.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    failures=[]
    for name,url in ASSETS.items():
        filename=BASE / f'{name}.png'
        try:
            if filename.exists():
                dimensions=validate_png(filename.read_bytes())
                print(f'✓ {name}: salvo localmente, {dimensions[0]}x{dimensions[1]}')
                continue
            if args.verify:
                raise FileNotFoundError('arquivo local ainda não existe')
            req=urllib.request.Request(url,headers={
                'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36',
                'Accept':'image/png,image/*;q=0.8,*/*;q=0.5',
            })
            with urllib.request.urlopen(req,timeout=22) as res:
                content=res.read(6_000_000)
            dimensions=validate_png(content)
            filename.write_bytes(content)
            print(f'✓ {name}: download concluído ({dimensions[0]}x{dimensions[1]})')
        except (ValueError,OSError,urllib.error.URLError) as exc:
            print(f'! {name}: {str(exc)[:200]}')
            failures.append(name)
    if failures:
        print('\nNão foi possível obter:',', '.join(failures))
        print('Baixe manualmente os PNGs pelas páginas indicadas em docs/IMAGENS.md')
        print('e salve como frontend/public/characters/<tema>.png.')
        raise SystemExit(1)
    print('\nTodas as imagens estão no projeto. Agora execute: docker compose up --build -d')

if __name__=='__main__': main()
