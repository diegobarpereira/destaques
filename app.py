import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, url_for
from pyppeteer import launch
import asyncio
import time
import cartolafc
import cartolafc.models
from cartolafc import Api
from cartolafc.util import strip_accents

root_dir = os.path.dirname(os.path.abspath(__file__))

api = cartolafc.Api(
    glb_id='1b62a06f6d67add624e2360012d974b304a5044624c486a50716e5a374a666539744c3738702d386b79516e466c36466f546546585070585f4c414b74666a6f4273597363697258754b374a6d7257487a724b716c7a36653531556f555a6f6f2d503665574e673d3d3a303a646965676f2e323031312e382e35')

rod = api.mercado().rodada_atual

app = Flask(__name__)
app.url_map.strict_slashes = False


@app.route('/')
def dest_page():
    start_time = time.time()
    capitaes, reservas = retornar_capitaes()

    print("--- %s seconds ---" % (time.time() - start_time))

    return render_template('destaques.html', get_list=retornar_destaques(), get_capitaes=capitaes,
                           get_reservas=reservas)


def get_partidas(rodada):
    partidas = api.partidas(rodada)
    parc_part = partidas
    return parc_part


def retornar_jogos():
    threads = []
    partidas = []
    with ThreadPoolExecutor(max_workers=60) as executor:
        threads.append(executor.submit(get_partidas, rod))

        for task in as_completed(threads):
            partidas.append(task.result())

    return partidas


def retornar_destaques():
    destaques = api.destaques()
    list_destaques = []
    for destaque in destaques:
        list_destaques.append(destaque)

        for partidas in retornar_jogos():
            for partida in partidas:
                if partida.valida:
                    if destaque.clube_nome == partida.clube_casa.nome:
                        destaque.adv = f' x {partida.clube_visitante.nome}'
                    if destaque.clube_nome == partida.clube_visitante.nome:
                        destaque.adv = f' {partida.clube_casa.nome} x '

    return list_destaques


async def scrap():
    browser = await launch(args=['--no-sandbox'], handleSIGINT=False,
                           handleSIGTERM=False,
                           handleSIGHUP=False)
    page = await browser.newPage()
    await page.goto('https://gatomestre.globoesporte.globo.com/mais-escalados-do-cartola-fc/')
    await page.waitFor(2000)
    content = await page.content()

    await browser.close()
    return content


def retornar_capitaes():
    with open('static/partidas.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    dict_time = json.loads(data)

    with open('static/clubes.json', encoding='utf-8', mode='r') as currentFile:
        clubes_data = currentFile.read().replace('\n', '')

    dict_clubes = json.loads(clubes_data)

    pagina = asyncio.new_event_loop().run_until_complete(scrap())

    soup = BeautifulSoup(pagina, features="html.parser")

    capitaes = soup.find("div", {"id": "gmListaCapitaes"})

    nomes = capitaes.find_all("h4", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__nome"})
    escalacoes_ = capitaes.find_all("span", {
        "class": "GM-FICHA-JOGADOR-box__header-dados-jogador__numeros__detalhes__valor"})

    posicoes = capitaes.find_all("span", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__posicao"})
    clubes = capitaes.find_all("span", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__time"})
    imagens = capitaes.find_all("div", {"class": "GM-FICHA-JOGADOR-box__header-foto-jogador", "style": True})

    reservas = soup.find("div", {"id": "gmListaReservas"})
    nomes_res = reservas.find_all("h4", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__nome"})
    escalacoes_res = reservas.find_all("span", {
        "class": "GM-FICHA-JOGADOR-box__header-dados-jogador__numeros__detalhes__valor"})
    posicoes_res = reservas.find_all("span", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__posicao"})
    clubes_res = reservas.find_all("span", {"class": "GM-FICHA-JOGADOR-box__header-dados-jogador__time"})
    imagens_res = reservas.find_all("div", {"class": "GM-FICHA-JOGADOR-box__header-foto-jogador", "style": True})

    imgs = []
    for img in imagens:
        image = img['style'].split('url(')[1].split(')')[0]
        imgs.append(image.replace("'", ""))

    imgs_res = []
    for img_res in imagens_res:
        image_res = img_res['style'].split('url(')[1].split(')')[0]
        imgs_res.append(image_res.replace("'", ""))

    escalacoes = []
    escs = [1, 3, 5, 7, 9]
    for e in escs:
        escalacoes.append(escalacoes_[e].text.replace(",", "."))

    res_escalacoes = []
    escs_res = [1, 3, 5, 7, 9]
    for e_res in escs_res:
        res_escalacoes.append(escalacoes_res[e_res].text.replace(",", "."))

    club_list = []
    adv_list = []
    club_list_res = []
    adv_res_list = []

    for cl, cl_res in zip(clubes, clubes_res):
        for k, v in dict_clubes.items():
            if cl.text == v['abreviacao']:
                club_list.append(v['nome'])
                # break
            if cl_res.text == v['abreviacao']:
                club_list_res.append(v['nome'])
                # break
        for partida in dict_time:

            if partida['valida']:

                if cl.text == partida['clube_casa']['abreviacao']:
                    adv_list.append(f' x {partida["clube_visitante"]["nome"]}')

                if cl.text == partida['clube_visitante']['abreviacao']:
                    adv_list.append(f' {partida["clube_casa"]["nome"]} x ')

                if cl_res.text == partida['clube_casa']['abreviacao']:
                    adv_res_list.append(f' x {partida["clube_visitante"]["nome"]}')

                if cl_res.text == partida['clube_visitante']['abreviacao']:
                    adv_res_list.append(f' {partida["clube_casa"]["nome"]} x ')

    cap_dict = {nome.text: [clube, posicao.text.upper(), escalacao, foto, adv]
                for nome, clube, posicao, escalacao, foto, adv
                in
                zip(nomes, club_list, posicoes, escalacoes, imgs, adv_list)}

    res_dict = {nome_res.text: [clube_res, posicao_res.text.upper(), escalacao_res, foto_res, adv_res]
                for nome_res, clube_res, posicao_res, escalacao_res, foto_res, adv_res
                in
                zip(nomes_res, club_list_res, posicoes_res, res_escalacoes, imgs_res, adv_res_list)}

    return cap_dict, res_dict


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)