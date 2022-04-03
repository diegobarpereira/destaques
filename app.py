import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, url_for
from matplotlib import pyplot as plt
from pyppeteer import launch
import asyncio
import time

from werkzeug.utils import redirect

import cartolafc
import cartolafc.models
from cartolafc import Api
from cartolafc.util import strip_accents

root_dir = os.path.dirname(os.path.abspath(__file__))

api = cartolafc.Api(
    glb_id='1b62a06f6d67add624e2360012d974b304a5044624c486a50716e5a374a666539744c3738702d386b79516e466c36466f546546585070585f4c414b74666a6f4273597363697258754b374a6d7257487a724b716c7a36653531556f555a6f6f2d503665574e673d3d3a303a646965676f2e323031312e382e35')

rod = api.mercado().rodada_atual
rodadas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
           30, 31, 32, 33, 34, 35, 36]

rar = ['Fandangos Santista', 'Christimao', 'Luanday FC', 'oSantista', 'Diego Pereira FC', 'Camisa21FC', 'RLR Santos FC',
       'Obina Mais Dez', 'JevyGoal', 'Real Beach Soccer', 'AvantiHulkFc', 'Eae Malandro FC', '0VINTE1 FC',
       'Golden Lions FC', 'Gabitreta F C', 'Denoris F.C.', 'ThiagoRolo FC', 'DraVascular', 'RIVA 77 ', 'VS Ponte Preta',
       'Lanterna Football Club', 'Markito Team']
grupo_1 = [3646412, 1241021, 48733, 7630223, 1011904]
grupo_2 = [219929, 1893918, 13957925, 71375, 977136]
grupo_3 = [19190102, 54685, 18796615, 28919430]
grupo_4 = [315637, 15452244, 279314, 1061000]
grupo_5 = [1245808, 937747, 14439636, 25582672]
grupo_6 = [1235701, 8912058, 19883717, 579336]
grupo = [3646412, 1241021, 48733, 7630223, 1011904, 219929, 1893918, 13957925, 71375, 977136, 19190102, 54685, 18796615,
         28919430, 315637, 15452244, 279314, 1061000, 1245808, 937747, 14439636, 25582672,
         1235701, 8912058, 19883717, 579336]
todos_ids = [3646412, 1235701, 219929, 1245808, 315637, 19190102, 13957925, 48733,
             15452244, 937747, 579336, 71375, 8912058, 977136, 54685, 1011904, 1893918, 18796615,
             14439636, 1889674, 279314, 1241021, 25582672, 1061000, 28919430, 19883717, 7630223]
ids_matamata = [937747, 15452244, 1241021, 3646412, 579336, 1061000, 1235701, 18796615, 13957925, 219929,
                977136, 1245808, 1011904, 19190102, 14439636, 54685]
ids_quartas = [937747, 219929, 1241021, 1245808, 15452244, 13957925, 3646412, 1061000]
ids_semis = [937747, 1245808, 13957925, 1061000]
ids_finais = [1245808, 13957925]

grupo_nomes = ['Gabitreta F C', 'Fandangos Santista', 'Raça Timão!!!', 'DraVascular', 'VS Ponte Preta',
               'Camisa21FC', 'Christimao', 'oSantista', 'Denoris F.C.', 'RIVA 77 ',
               'ThiagoRolo FC', 'Sóhh Tapa F.C.', 'Golden Lions FC', 'Gonella Verde ',
               'Real Beach Soccer', 'FC Caiçara BR', 'AvantiHulkFc', 'SAMPAIO13 FUTEBOL CL',
               'Diego Pereira FC', 'RLR Santos FC', 'Obina Mais Dez', 'JevyGoal',
               'Eae Malandro FC', 'Markito Team', 'Lanterna Football Club', 'Luanday FC']

times_ids = []
if api.mercado().status.nome != 'Mercado em manutenção':
    ligas = api.liga('liga-heineken-2022')

    for lig in ligas.times:
        times_ids.append(lig.ids)


app = Flask(__name__)
app.url_map.strict_slashes = False


@app.route('/')
def index_page():
    if api.mercado().status.nome == 'Mercado em manutenção':
        return render_template('manutencao.html')
    else:
        liga = api.liga('liga-heineken-2022')
        nome = liga.nome
        escudo = liga.escudo
        return render_template('index.html', get_nome=nome, get_escudo=escudo)


@app.route('/participantes')
def participantes_page():
    liga = api.liga('liga-heineken-2022')
    nome = liga.nome
    escudo = liga.escudo
    return render_template('participantes.html', get_list=retornar_part(), get_escudo=escudo)


@app.route('/class')
async def class_page():
    start_time = time.time()
    liga_total, liga_turno = retornar_liga_class()
    print("--- %s seconds ---" % (time.time() - start_time))

    return render_template('class_2.html',
                           get_total=sorted(liga_total.items(), key=lambda kv: kv[1][2], reverse=True),
                           get_turno=sorted(liga_turno.items(), key=lambda kv: kv[1][2], reverse=True),
                           get_semcapitao=sem_capitao())


@app.route('/scouts')
def parciais_page():
    if api.mercado().status.nome == 'Mercado fechado':
        return render_template('scouts.html', get_list=parciais())
    else:
        return render_template('error.html')


@app.route('/matamata')
def matamata_page():
    # oit_a, oit_b, qua_a, qua_b = retornar_matamata()
    # oit_a, oit_b, qua_a, qua_b, semi_a, semi_b = retornar_matamata()
    oit_a, oit_b, qua_a, qua_b, semi_a, semi_b, final_a, final_b = retornar_matamata()
    campeao = []
    vice = []

    for f_a, f_b in zip(final_a, final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao = [[f_a[1], f_a[2]]]
            vice = [[f_b[1], f_b[2]]]
        else:
            campeao = [[f_b[1], f_b[2]]]
            vice = [[f_a[1], f_a[2]]]

    return render_template('matamata.html', get_list1=oit_a, get_list2=oit_b, get_list3=qua_a,
                           get_list4=qua_b, get_list5=semi_a, get_list6=semi_b, get_list7=final_a,
                           get_list8=final_b, campeao=campeao, vice=vice)


@app.route('/premiacao')
def premiacao_page():
    lider_prim_turno, lider_seg_turno, prem, campeao_geral, vice_campeao, terc_colocado, quarto_colocado, campeao, vice = premiacao()
    return render_template('premiacao.html', lider_prim_turno=lider_prim_turno, lider_seg_turno=lider_seg_turno,
                           get_list=prem, get_lider=campeao_geral, vice_campeao=vice_campeao,
                           terc_colocado=terc_colocado, quarto_colocado=quarto_colocado, campeao=campeao, vice=vice)


@app.route('/partidas')
def partidas_page():
    return render_template('partidas.html', get_list=retornar_partidas())


@app.route('/destaques')
def dest_page():

    capitaes, reservas = retornar_capitaes()

    return render_template('destaques.html', get_list=retornar_destaques(), get_capitaes=capitaes,
                           get_reservas=reservas)


@app.route('/times')
def times_page():
    get_list = sorted(get_atletas().items(), key=lambda kv: kv[1], reverse=True)
    return render_template('times.html', get_list=get_list)


@app.route('/stats')
def stats_page():
    return render_template('stats.html', get_list=retornar_estats_liga_3())


@app.route('/pontuacoes')
async def pontuacoes_page():
    start_time = time.time()
    pont_liga, list_max = pontos()
    print("--- %s seconds ---" % (time.time() - start_time))
    return render_template('pontuacoes.html', get_list=pont_liga, get_max=list_max)


@app.route('/comp', methods=["GET", "POST"])
def gfg():
    if request.method == "POST":
        jogador = request.form.get("jogador")

        time = request.form.get("time")

        retornar_estats_jogador(jogador, time)
        return redirect(url_for("/comparacao_result.html"))

    return render_template("comparacao.html")


@app.route("/comp_jogs")
def comp_jogs():
    return render_template('teste.html')


@app.route("/form", methods=["GET"])
def get_form():
    dropdown_times = []
    clubes = api.partidas(rod)
    for clube in clubes:
        dropdown_times.append(clube.clube_casa.nome)
        dropdown_times.append(clube.clube_visitante.nome)

    dropdown_times.sort()

    return render_template('teste.html', dropdown_times=dropdown_times)


@app.route("/post_field", methods=["POST"])
def need_input():
    jogador = request.form.get("jogador")
    time = request.form.get("time")
    gd = {}

    get_data = retornar_estats_jogador(jogador, time)
    for gdata in get_data:
        for k, v in gdata.items():
            gd[k] = v

    return render_template('comparacao_result.html', get_data=gd, get_jogador=jogador, get_time=time)


@app.route("/media", methods=['GET', 'POST'])
def get_media_form():
    dropdown_times = []

    for lig in ligas.times:
        dropdown_times.append(lig.nome)

    dropdown_times.sort()

    return render_template('media_form.html', dropdown_times=dropdown_times)


@app.route("/media_result", methods=['GET', 'POST'])
def return_media_form():
    team = request.form.get("time")
    gd = {}

    get_data = retornar_medias_time(team)
    for k, v in get_data.items():
        gd[k] = v

    root_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(root_dir, 'static/media.jpg')
    get_img = img_path

    return render_template('media_result.html', get_data=gd, get_time=team, get_img=get_img)


@app.route("/liberta")
def liberta():
    rod_21, rod_22, rod_23, rod_24, rod_25, rod_26, rod_27, rod_28, rod_29, rod_30, g1, g2, g3, g4, g5, g6 = liberta_seg_turno_3()
    return render_template('liberta2.html', get_list=rod_21, get_list2=rod_22, get_list3=rod_23, get_list4=rod_24,
                           get_list5=rod_25, get_list6=rod_26, get_list7=rod_27, get_list8=rod_28,
                           get_list9=rod_29, get_list10=rod_30,
                           data1=sorted(g1, key=lambda y: (y[4], y[5], y[7]), reverse=True),
                           data2=sorted(g2, key=lambda y: (y[4], y[5], y[7]), reverse=True),
                           data3=sorted(g3, key=lambda y: (y[4], y[5], y[7]), reverse=True),
                           data4=sorted(g4, key=lambda y: (y[4], y[5], y[7]), reverse=True),
                           data5=sorted(g5, key=lambda y: (y[4], y[5], y[7]), reverse=True),
                           data6=sorted(g6, key=lambda y: (y[4], y[5], y[7]), reverse=True))


def get_times_campeonato():
    liga_class = api.liga('liga-heineken-2022', order_by=cartolafc.CAMPEONATO)
    return liga_class


def retornar_liga_campeonato():
    threads = []
    teams = []
    team_dict = {}

    with ThreadPoolExecutor() as executor:
        threads.append(executor.submit(get_times_campeonato))

        for task in as_completed(threads):
            teams.append(task.result())

        for t in teams:
            for team in t.times:
                team_dict[team.nome] = team.foto

    return team_dict


def retornar_part():
    participantes = {}

    for k, v in retornar_liga_campeonato().items():
        participantes[k] = v

    return participantes


def parciais():
    parciais = api.parciais()
    parciais_sorted = sorted(parciais.values(), key=lambda pts: pts.pontos, reverse=True)
    list_parciais = []
    for chave in parciais_sorted:
        list_parciais.append([chave.posicao.abreviacao, chave.apelido, chave.clube.nome,
                              ', '.join('%s%s' % (chave.scout[k], k) for k in chave.scout),
                              "{:.2f}".format(chave.pontos)])
    return list_parciais


def retornar_partidas():
    rodada = api.mercado().rodada_atual
    partidas = api.partidas(rodada)
    list_partidas = []
    for partida in partidas:
        if partida.valida:
            list_partidas.append(f'{partida.data} - {partida.local}')
            list_partidas.append(
                f' {partida.clube_casa.nome} {partida.placar_casa if partida.placar_casa else 0} x {partida.placar_visitante if partida.placar_visitante else 0} {partida.clube_visitante.nome}')
        else:
            list_partidas.append('Partida não é valida para a rodada')
            list_partidas.append(
                f' {partida.clube_casa.nome} {partida.placar_casa if partida.placar_casa else 0} x {partida.placar_visitante if partida.placar_visitante else 0} {partida.clube_visitante.nome}')
    return list_partidas


def get_times(id_):
    time_ = api.time(id_) if api.mercado().status.nome == 'Mercado aberto' else api.time_parcial(id_)
    return time_


def get_times_total(id_):
    time_ = api.time(id_)
    return time_


def get_times_parcial(id_):
    time_ = api.time_parcial(id_) if api.mercado().status.nome == 'Mercado fechado' else None
    return time_


def get_times_rodada(id_, rodada):
    if rodada < rod:
        time_ = api.time(id_, rodada=rodada)
    else:
        time_ = api.time_parcial(id_)
    return time_


def get_atletas():
    dict_time_pontos = {}

    with ThreadPoolExecutor(max_workers=40) as executor:
        threads = executor.map(get_times, times_ids)

        for times in threads:
            list_atletas = []
            list_reservas = []
            for atleta in times.atletas:
                list_atletas.append(
                    [atleta.posicao.abreviacao, '(C) ' + atleta.apelido if atleta.is_capitao else atleta.apelido,
                     atleta.clube.nome if atleta.clube else None, atleta.scout,
                     "{:.2f}".format(atleta.pontos * 2) if atleta.is_capitao and api.mercado().status.nome == 'Mercado '
                                                                                                              'aberto'
                     else "{:.2f}".format(atleta.pontos)])

            if times.reservas:
                for reserva in times.reservas:
                    list_reservas.append(
                        [reserva.posicao.abreviacao, reserva.apelido, reserva.clube.nome if reserva.clube else None,
                         reserva.scout,
                         "{:.2f}".format(reserva.pontos)])

            dict_time_pontos[times.info.nome] = [times.pontos, list_atletas, list_reservas]

    return dict_time_pontos


def retornar_media_time_rodada(id_):
    threads = []
    teams = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        for x in range(1, rod):
            threads.append(executor.submit(get_times_rodada, id_, rodada=x))

        for task in as_completed(threads):
            teams.append(task.result())

    return teams


def sem_capitao():
    dict_time = {}
    dict_time_ = {}
    dict_pts = {}
    with open('static/sem_capitao.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    for chave, valor in json.loads(escudos).items():
        for c, v in dict_time.items():
            if chave == c:
                dict_time_[c] = [valor, v]

    for k in sorted(list(dict_time_.items()), key=lambda t: t[1][1], reverse=True):
        dict_pts[k[0]] = [k[1][0], k[1][1]]

    return dict_pts


def retornar_matamata():
    dict_time = {}
    dict_time_q = {}
    dict_time_s = {}
    dict_time_f = {}
    oitavas = []
    quartas = []
    semis = []
    finais = []

    with open('static/times_matamata.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, ids_matamata)
        #
        #     for teams in threads:
        #         dict_time[teams.info.nome].append(teams.pontos)

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    for chave, valor in json.loads(escudos).items():
        for c, v in dict_time.items():
            if chave == c:
                dict_time[c] = [valor, v]

    for key, value in dict_time.items():
        # oitavas.append([key, value[0], value[1][0], value[1][1]])  # value[1]
        if not value[1]:
            oitavas.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                oitavas.append([key, value[0], value[1][0], 0.00])
            else:
                oitavas.append([key, value[0], value[1][0], value[1][1]])

    jogos_oitavas_a = []
    jogos_oitavas_a.append(
        [oitavas[0][2], oitavas[0][1], oitavas[0][0], oitavas[0][3], oitavas[15][2], oitavas[15][1], oitavas[15][0],
         oitavas[15][3]])
    jogos_oitavas_a.append(
        [oitavas[6][2], oitavas[6][1], oitavas[6][0], oitavas[6][3], oitavas[9][2], oitavas[9][1], oitavas[9][0],
         oitavas[9][3]])
    jogos_oitavas_a.append(
        [oitavas[2][2], oitavas[2][1], oitavas[2][0], oitavas[2][3], oitavas[13][2], oitavas[13][1], oitavas[13][0],
         oitavas[13][3]])
    jogos_oitavas_a.append(
        [oitavas[4][2], oitavas[4][1], oitavas[4][0], oitavas[4][3], oitavas[11][2], oitavas[11][1], oitavas[11][0],
         oitavas[11][3]])

    jogos_oitavas_b = []
    jogos_oitavas_b.append(
        [oitavas[1][3], oitavas[1][1], oitavas[1][0], oitavas[1][2], oitavas[14][3], oitavas[14][1], oitavas[14][0],
         oitavas[14][2]])
    jogos_oitavas_b.append(
        [oitavas[7][3], oitavas[7][1], oitavas[7][0], oitavas[7][2], oitavas[8][3], oitavas[8][1], oitavas[8][0],
         oitavas[8][2]])
    jogos_oitavas_b.append(
        [oitavas[3][3], oitavas[3][1], oitavas[3][0], oitavas[3][2], oitavas[12][3], oitavas[12][1], oitavas[12][0],
         oitavas[12][2]])
    jogos_oitavas_b.append(
        [oitavas[5][3], oitavas[5][1], oitavas[5][0], oitavas[5][2], oitavas[10][3], oitavas[10][1], oitavas[10][0],
         oitavas[10][2]])

    with open('static/times_quartas.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_q[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, ids_quartas)
        #
        #     for teams in threads:
        #         dict_time_q[teams.info.nome].append(teams.pontos)

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    for chave, valor in json.loads(escudos).items():
        for c, v in dict_time_q.items():
            if chave == c:
                dict_time_q[c] = [valor, v]

    for key, value in dict_time_q.items():
        # quartas.append([key, value[0], value[1][0], value[1][1]])  # value[0]
        if not value[1]:
            quartas.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                quartas.append([key, value[0], value[1][0], 0.00])
            else:
                quartas.append([key, value[0], value[1][0], value[1][1]])

    jogos_quartas_a = []
    jogos_quartas_a.append(
        [quartas[0][2], quartas[0][1], quartas[0][0], quartas[0][3], quartas[1][2], quartas[1][1], quartas[1][0],
         quartas[1][3]])
    jogos_quartas_a.append(
        [quartas[2][2], quartas[2][1], quartas[2][0], quartas[2][3], quartas[3][2], quartas[3][1], quartas[3][0],
         quartas[3][3]])

    jogos_quartas_b = []
    jogos_quartas_b.append(
        [quartas[4][3], quartas[4][1], quartas[4][0], quartas[4][2], quartas[5][3], quartas[5][1], quartas[5][0],
         quartas[5][2]])
    jogos_quartas_b.append(
        [quartas[6][3], quartas[6][1], quartas[6][0], quartas[6][2], quartas[7][3], quartas[7][1], quartas[7][0],
         quartas[7][2]])

    with open('static/times_semis.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_s[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, ids_semis)
        #
        #     for teams in threads:
        #         dict_time_s[teams.info.nome].append(teams.pontos)

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    for chave, valor in json.loads(escudos).items():
        for c, v in dict_time_s.items():
            if chave == c:
                dict_time_s[c] = [valor, v]

    for key, value in dict_time_s.items():
        if not value[1]:
            semis.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                semis.append([key, value[0], value[1][0], 0.00])
            else:
                semis.append([key, value[0], value[1][0], value[1][1]])

    jogos_semis_a = []
    jogos_semis_a.append(
        [semis[0][2], semis[0][1], semis[0][0], semis[0][3], semis[1][2], semis[1][1], semis[1][0],
         semis[1][3]])

    jogos_semis_b = []
    jogos_semis_b.append(
        [semis[2][3], semis[2][1], semis[2][0], semis[2][2], semis[3][3], semis[3][1], semis[3][0],
         semis[3][2]])

    with open('static/times_finais.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_f[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, ids_finais)
        #
        #     for teams in threads:
        #         dict_time_f[teams.info.nome].append(teams.pontos)

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    for chave, valor in json.loads(escudos).items():
        for c, v in dict_time_f.items():
            if chave == c:
                dict_time_f[c] = [valor, v]

    for key, value in dict_time_f.items():
        if not value[1]:
            finais.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                finais.append([key, value[0], value[1][0], 0.00])
            else:
                finais.append([key, value[0], value[1][0], value[1][1]])

    jogos_final_a = []
    jogos_final_a.append(
        [finais[0][2], finais[0][1], finais[0][0], finais[0][3]])

    jogos_final_b = []
    jogos_final_b.append(
        [finais[1][3], finais[1][1], finais[1][0], finais[1][2]])

    return jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, \
           jogos_final_a, jogos_final_b


def get_time_rodada_2(id_):
    time_ = []
    for rod_ in rodadas:
        time_.append(api.time(id_, rodada=rod_))
    return time_


def retornar_estats_liga_3():
    dict_time_stats = {}

    with open('static/times_stats.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_stats[k] = v

    return dict_time_stats


def pontos():
    dict_time_pts = {}
    dict_time_pts_ = {}
    max_val = []

    dict_time = {}

    with open('static/times.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, times_ids)
        #
        #     for teams in threads:
        #         dict_time[teams.info.nome].append(teams.pontos)

    for time, pontos in dict_time.items():
        for ponto in pontos:
            if time in dict_time_pts:
                dict_time_pts[time].append(ponto)
            else:
                dict_time_pts[time] = [ponto]

    ordenar_dict = sorted(dict_time_pts.items(), key=lambda t: sum(t[1]), reverse=True)
    for k in ordenar_dict:
        dict_time_pts_[k[0]] = k[1]

    if api.mercado().status.nome == 'Mercado aberto':
        dict_time_pts.pop('Raça Timão!!!')
        dict_time_pts.pop('Sóhh Tapa F.C.')
        dict_time_pts.pop('SAMPAIO13 FUTEBOL CL')
        dict_time_pts.pop('Gonella Verde ')
        dict_time_pts.pop('FC Caiçara BR')

        for x in range(0, api.mercado().rodada_atual - 1):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_time_pts.items()}.items(), key=lambda y: y[1],
                                     reverse=True)
            max_val.append(max_cada_rodada[0] if max_cada_rodada[0][0] in rar else max_cada_rodada[1])

    if api.mercado().status.nome == 'Mercado fechado':
        dict_time_pts.pop('Raça Timão!!!')
        dict_time_pts.pop('Sóhh Tapa F.C.')
        dict_time_pts.pop('SAMPAIO13 FUTEBOL CL')
        dict_time_pts.pop('Gonella Verde ')
        dict_time_pts.pop('FC Caiçara BR')

        for x in range(0, api.mercado().rodada_atual):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_time_pts.items()}.items(), key=lambda y: y[1],
                                     reverse=True)
            max_val.append(max_cada_rodada[0] if max_cada_rodada[0][0] in rar else max_cada_rodada[1])

    if api.mercado().status.nome == 'Final de temporada':
        dict_time_pts.pop('Raça Timão!!!')
        dict_time_pts.pop('Sóhh Tapa F.C.')
        dict_time_pts.pop('SAMPAIO13 FUTEBOL CL')
        dict_time_pts.pop('Gonella Verde ')
        dict_time_pts.pop('FC Caiçara BR')

        for x in range(0, api.mercado().rodada_atual):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_time_pts.items()}.items(), key=lambda y: y[1],
                                     reverse=True)
            max_val.append(max_cada_rodada[0] if max_cada_rodada[0][0] in rar else max_cada_rodada[1])

    return dict_time_pts_, max_val


def pontos_turnos():
    dict_time_pts_prim_turno = {}
    dict_time_pts_prim_turno_ = {}
    dict_time_pts_seg_turno = {}
    dict_time_pts_seg_turno_ = {}
    dict_time_prim_turno = {}
    dict_time_seg_turno = {}

    with open('static/times_prim_turno.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_prim_turno[k] = v

        # if api.mercado().status.nome == 'Mercado fechado':
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, times_ids)
        #
        #     for teams in threads:
        #         dict_time_prim_turno[teams.info.nome].append(teams.pontos)

    for time, pontos in dict_time_prim_turno.items():
        for ponto in pontos:
            if time in dict_time_pts_prim_turno:
                dict_time_pts_prim_turno[time].append(ponto)
            else:
                dict_time_pts_prim_turno[time] = [ponto]

    with open('static/times_seg_turno.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_seg_turno[k] = v

        if api.mercado().status.nome == 'Mercado fechado':
            with ThreadPoolExecutor(max_workers=40) as executor:
                threads = executor.map(api.time_parcial, times_ids)

            for teams in threads:
                dict_time_seg_turno[teams.info.nome].append(teams.pontos)

    for time, pontos in dict_time_seg_turno.items():
        for ponto in pontos:
            if time in dict_time_pts_seg_turno:
                dict_time_pts_seg_turno[time].append(ponto)
            else:
                dict_time_pts_seg_turno[time] = [ponto]

    ordenar_dict = sorted(dict_time_pts_prim_turno.items(), key=lambda t: sum(t[1]), reverse=True)
    for k in ordenar_dict:
        dict_time_pts_prim_turno_[k[0]] = k[1]

    ordenar_dict_2 = sorted(dict_time_pts_seg_turno.items(), key=lambda t: sum(t[1]), reverse=True)
    for k in ordenar_dict_2:
        dict_time_pts_seg_turno_[k[0]] = k[1]

    return dict_time_pts_prim_turno_, dict_time_pts_seg_turno_


def get_parciais_partidas(rodada):
    parc_part = {}
    parciais = api.parciais(rodada)
    partidas = api.partidas(rodada)
    parc_part[rodada] = [parciais, partidas]
    return parc_part


def retornar_parciais_partidas():
    threads = []
    parciais_partidas = []
    with ThreadPoolExecutor(max_workers=60) as executor:
        for x in range(1, rod):
            threads.append(executor.submit(get_parciais_partidas, x))

        for task in as_completed(threads):
            parciais_partidas.append(task.result())

    return parciais_partidas


def retornar_estats_jogador(player: str, player_clube: str):
    jogador_media_total = {}
    jogador_media_fora = {}
    jogador_media_casa = {}
    casa = {}
    fora = {}
    soma_pontos_casa = 0
    soma_pontos_fora = 0
    num_jogos_casa = 0
    num_jogos_fora = 0
    player_id = ''
    player = strip_accents(player)

    for atleta in api.mercado_atletas():
        if player.lower() in strip_accents(atleta.apelido.lower()) and player_clube in atleta.clube.nome:
            player_id = ''.join([str(atleta.id)])
            jogador_media_total[f'{atleta.jogos_num} jogos'] = [atleta.media_num, atleta.scout]
            break

    for parc_part in retornar_parciais_partidas():
        for k, v in parc_part.items():
            for v1 in v[0].values():
                if player_id == str(v1.id):
                    for v2 in v[1]:
                        if player_clube == v2.clube_casa.nome:
                            num_jogos_casa = num_jogos_casa + 1

                            if v1.posicao.nome != 'Técnico' and v1.scout:

                                for i in [v1.scout]:
                                    for k, v in i.items():
                                        if k in casa.keys():
                                            casa[k] = casa[k] + v
                                        else:
                                            casa[k] = v

                            soma_pontos_casa += v1.pontos

                        elif player_clube == v2.clube_visitante.nome:
                            num_jogos_fora = num_jogos_fora + 1

                            if v1.posicao.nome != 'Técnico' and v1.scout:

                                for j in [v1.scout]:
                                    for k, v in j.items():
                                        if k in fora.keys():
                                            fora[k] = fora[k] + v
                                        else:
                                            fora[k] = v

                            soma_pontos_fora += v1.pontos

    jogador_media_casa[f'{num_jogos_casa} jogos Casa'] = ["{:.2f}".format(soma_pontos_casa / num_jogos_casa),
                                                          casa] if num_jogos_casa != 0 else ['Sem partidas em casa']

    jogador_media_fora[f'{num_jogos_fora} jogos Fora'] = ["{:.2f}".format(soma_pontos_fora / num_jogos_fora),
                                                          fora] if num_jogos_fora != 0 else ['Sem partidas fora']

    return jogador_media_total, jogador_media_casa, jogador_media_fora


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
    # await page.waitFor(2000)
    await page.waitForXPath('//i[@class="GM-ICONES-icon GM-ICONES-icon--arrow-round-down"]')
    content = await page.content()

    await browser.close()
    return content


def retornar_capitaes():
    start_time = time.time()

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

    print("--- %s seconds ---" % (time.time() - start_time))

    return cap_dict, res_dict


def retornar_medias_time(cartola_time: str):
    dict_medias = {}
    gol = 0
    somagol = 0
    lat = 0
    somalat = 0
    zag = 0
    somazag = 0
    meia = 0
    somameia = 0
    ata = 0
    somaata = 0
    tec = 0
    somatec = 0
    time_id = 0

    for part in ligas.times:
        if cartola_time in part.nome:
            time_id = part.id
            break

    media_total = api.time(time_id)
    mt = "{:.2f}".format(media_total.pontos / (rod - 1))

    for t in retornar_media_time_rodada(time_id):
        for value in t.atletas:

            if value.posicao.nome == 'Goleiro':
                gol = gol + 1
                somagol = somagol + value.pontos
            elif value.posicao.nome == 'Lateral':
                lat = lat + 1
                somalat = somalat + value.pontos
            elif value.posicao.nome == 'Zagueiro':
                zag = zag + 1
                somazag = somazag + value.pontos
            elif value.posicao.nome == 'Meia':
                meia = meia + 1
                somameia = somameia + value.pontos
            elif value.posicao.nome == 'Atacante':
                ata = ata + 1
                somaata = somaata + value.pontos
            elif value.posicao.nome == 'Técnico':
                tec = tec + 1
                somatec = somatec + value.pontos
            else:
                pass

        dict_medias[t.info.nome, mt] = [somagol / gol, (somalat / lat) if somalat or lat else 0, somazag / zag,
                                        somameia / meia, somaata / ata, somatec / tec]

    for x_axis in dict_medias.values():
        left = [1, 2, 3, 4, 5, 6]
        x = ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA', 'TEC']
        y = [x_axis[0], x_axis[1], x_axis[2], x_axis[3], x_axis[4], x_axis[5]]
        # plt.bar(left, y, tick_label=x,
        #         width=0.8, color=['red', 'green'])

        z = np.arange(len(x))  # the label locations
        width = 0.8  # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(z, y, width, label='Média')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_xticks(z)
        ax.set_xticklabels(x)
        ax.legend()

        ax.bar_label(rects1, padding=3)

        fig.tight_layout()
        plt.savefig('static/media.jpg', dpi=400)
        # plt.show()

    return dict_medias


def liberta_seg_turno_3():
    rodada_21 = []
    rodada_22 = []
    rodada_23 = []
    rodada_24 = []
    rodada_25 = []
    rodada_26 = []
    rodada_27 = []
    rodada_28 = []
    rodada_29 = []
    rodada_30 = []

    dict_time = {}

    with open('static/times_liberta.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

        if api.mercado().status.nome == 'Mercado fechado':
            with ThreadPoolExecutor(max_workers=40) as executor:
                threads = executor.map(api.time_parcial, grupo)

            for teams in threads:
                dict_time[teams.info.nome].append(teams.pontos)

    jogos_rodada_21 = []
    jogos_rodada_22 = []
    jogos_rodada_23 = []
    jogos_rodada_24 = []
    jogos_rodada_25 = []
    jogos_rodada_26 = []
    jogos_rodada_27 = []
    jogos_rodada_28 = []
    jogos_rodada_29 = []
    jogos_rodada_30 = []

    for key, value in dict_time.items():
        rodada_21.append([key, value[0]])
        rodada_22.append([key, value[1]])
        rodada_23.append([key, value[2]])
        rodada_24.append([key, value[3]])
        rodada_25.append([key, value[4]])
        rodada_26.append([key, value[5]])
        rodada_27.append([key, value[6]])
        rodada_28.append([key, value[7]])
        rodada_29.append([key, value[8]])
        rodada_30.append([key, value[9]])

    jogos_rodada_21.append([rodada_21[0][0], rodada_21[0][1], 'x', rodada_21[1][1], rodada_21[1][0]])
    jogos_rodada_21.append([rodada_21[2][0], rodada_21[2][1], 'x', rodada_21[3][1], rodada_21[3][0]])
    jogos_rodada_21.append([rodada_21[4][0], '', 'x', '', ''])
    jogos_rodada_21.append([rodada_21[5][0], rodada_21[5][1], 'x', rodada_21[6][1], rodada_21[6][0]])
    jogos_rodada_21.append([rodada_21[7][0], rodada_21[7][1], 'x', rodada_21[8][1], rodada_21[8][0]])
    jogos_rodada_21.append([rodada_21[9][0], '', 'x', '', ''])

    for x in jogos_rodada_21:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_22.append([rodada_22[0][0], rodada_22[0][1], 'x', rodada_22[4][1], rodada_22[4][0]])
    jogos_rodada_22.append([rodada_22[1][0], rodada_22[1][1], 'x', rodada_22[2][1], rodada_22[2][0]])
    jogos_rodada_22.append([rodada_22[3][0], '', 'x', '', ''])
    jogos_rodada_22.append([rodada_22[5][0], rodada_22[5][1], 'x', rodada_22[9][1], rodada_22[9][0]])
    jogos_rodada_22.append([rodada_22[6][0], rodada_22[6][1], 'x', rodada_22[7][1], rodada_22[7][0]])
    jogos_rodada_22.append([rodada_22[8][0], '', 'x', '', ''])
    jogos_rodada_22.append([rodada_22[10][0], rodada_22[10][1], 'x', rodada_22[11][1], rodada_22[11][0]])
    jogos_rodada_22.append([rodada_22[12][0], rodada_22[12][1], 'x', rodada_22[13][1], rodada_22[13][0]])
    jogos_rodada_22.append([rodada_22[14][0], rodada_22[14][1], 'x', rodada_22[15][1], rodada_22[15][0]])
    jogos_rodada_22.append([rodada_22[16][0], rodada_22[16][1], 'x', rodada_22[17][1], rodada_22[17][0]])
    jogos_rodada_22.append([rodada_22[18][0], rodada_22[18][1], 'x', rodada_22[19][1], rodada_22[19][0]])
    jogos_rodada_22.append([rodada_22[20][0], rodada_22[20][1], 'x', rodada_22[21][1], rodada_22[21][0]])
    jogos_rodada_22.append([rodada_22[22][0], rodada_22[22][1], 'x', rodada_22[23][1], rodada_22[23][0]])
    jogos_rodada_22.append([rodada_22[24][0], rodada_22[24][1], 'x', rodada_22[25][1], rodada_22[25][0]])

    for x in jogos_rodada_22:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (x[1] and x[3]) is type(float):
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_23.append([rodada_23[0][0], rodada_23[0][1], 'x', rodada_23[3][1], rodada_23[3][0]])
    jogos_rodada_23.append([rodada_23[1][0], rodada_23[1][1], 'x', rodada_23[4][1], rodada_23[4][0]])
    jogos_rodada_23.append([rodada_23[2][0], '', 'x', '', ''])

    jogos_rodada_23.append([rodada_23[5][0], rodada_23[5][1], 'x', rodada_23[8][1], rodada_23[8][0]])
    jogos_rodada_23.append([rodada_23[6][0], rodada_23[6][1], 'x', rodada_23[9][1], rodada_23[9][0]])
    jogos_rodada_23.append([rodada_23[7][0], '', 'x', '', ''])

    jogos_rodada_23.append([rodada_23[10][0], rodada_23[10][1], 'x', rodada_23[12][1], rodada_23[12][0]])
    jogos_rodada_23.append([rodada_23[11][0], rodada_23[11][1], 'x', rodada_23[13][1], rodada_23[13][0]])

    jogos_rodada_23.append([rodada_23[14][0], rodada_23[14][1], 'x', rodada_23[16][1], rodada_23[16][0]])
    jogos_rodada_23.append([rodada_23[15][0], rodada_23[15][1], 'x', rodada_23[17][1], rodada_23[17][0]])

    jogos_rodada_23.append([rodada_23[18][0], rodada_23[18][1], 'x', rodada_23[20][1], rodada_23[20][0]])
    jogos_rodada_23.append([rodada_23[19][0], rodada_23[19][1], 'x', rodada_23[21][1], rodada_23[21][0]])

    jogos_rodada_23.append([rodada_23[22][0], rodada_23[22][1], 'x', rodada_23[24][1], rodada_23[24][0]])
    jogos_rodada_23.append([rodada_23[23][0], rodada_23[23][1], 'x', rodada_23[25][1], rodada_23[25][0]])

    for x in jogos_rodada_23:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (x[1] and x[3]) is type(float):
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_24.append([rodada_24[0][0], rodada_24[0][1], 'x', rodada_24[2][1], rodada_24[2][0]])
    jogos_rodada_24.append([rodada_24[4][0], rodada_24[4][1], 'x', rodada_24[3][1], rodada_24[3][0]])
    jogos_rodada_24.append([rodada_24[1][0], '', 'x', '', ''])

    jogos_rodada_24.append([rodada_24[5][0], rodada_24[5][1], 'x', rodada_24[7][1], rodada_24[7][0]])
    jogos_rodada_24.append([rodada_24[9][0], rodada_24[9][1], 'x', rodada_24[8][1], rodada_24[8][0]])
    jogos_rodada_24.append([rodada_24[6][0], '', 'x', '', ''])

    jogos_rodada_24.append([rodada_24[10][0], rodada_24[10][1], 'x', rodada_24[13][1], rodada_24[13][0]])
    jogos_rodada_24.append([rodada_24[11][0], rodada_24[11][1], 'x', rodada_24[12][1], rodada_24[12][0]])

    jogos_rodada_24.append([rodada_24[14][0], rodada_24[14][1], 'x', rodada_24[17][1], rodada_24[17][0]])
    jogos_rodada_24.append([rodada_24[15][0], rodada_24[15][1], 'x', rodada_24[16][1], rodada_24[16][0]])

    jogos_rodada_24.append([rodada_24[18][0], rodada_24[18][1], 'x', rodada_24[21][1], rodada_24[21][0]])
    jogos_rodada_24.append([rodada_24[19][0], rodada_24[19][1], 'x', rodada_24[20][1], rodada_24[20][0]])

    jogos_rodada_24.append([rodada_24[22][0], rodada_24[22][1], 'x', rodada_24[25][1], rodada_24[25][0]])
    jogos_rodada_24.append([rodada_24[23][0], rodada_24[23][1], 'x', rodada_24[24][1], rodada_24[24][0]])

    for x in jogos_rodada_24:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_25.append([rodada_25[1][0], rodada_25[1][1], 'x', rodada_25[3][1], rodada_25[3][0]])
    jogos_rodada_25.append([rodada_25[2][0], rodada_25[2][1], 'x', rodada_25[4][1], rodada_25[4][0]])
    jogos_rodada_25.append([rodada_25[0][0], '', 'x', '', ''])
    jogos_rodada_25.append([rodada_25[6][0], rodada_25[6][1], 'x', rodada_25[8][1], rodada_25[8][0]])
    jogos_rodada_25.append([rodada_25[7][0], rodada_25[7][1], 'x', rodada_25[9][1], rodada_25[9][0]])
    jogos_rodada_25.append([rodada_25[5][0], '', 'x', '', ''])

    for x in jogos_rodada_25:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_26.append([rodada_26[1][0], rodada_26[1][1], 'x', rodada_26[0][1], rodada_26[0][0]])
    jogos_rodada_26.append([rodada_26[3][0], rodada_26[3][1], 'x', rodada_26[2][1], rodada_26[2][0]])
    jogos_rodada_26.append(['', '', 'x', '', rodada_26[4][0]])
    jogos_rodada_26.append([rodada_26[6][0], rodada_26[6][1], 'x', rodada_26[5][1], rodada_26[5][0]])
    jogos_rodada_26.append([rodada_26[8][0], rodada_26[8][1], 'x', rodada_26[7][1], rodada_26[7][0]])
    jogos_rodada_26.append(['', '', 'x', '', rodada_26[9][0]])

    for x in jogos_rodada_26:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if x[1] == '' or x[3] == '' or x[1] == 0.00 or x[3] == 0.00:
            x.insert(0, '')
            x.insert(6, '')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')

    jogos_rodada_27.append([rodada_27[4][0], rodada_27[4][1], 'x', rodada_27[0][1], rodada_27[0][0]])
    jogos_rodada_27.append([rodada_27[2][0], rodada_27[2][1], 'x', rodada_27[1][1], rodada_27[1][0]])
    jogos_rodada_27.append(['', '', 'x', '', rodada_27[3][0]])
    jogos_rodada_27.append([rodada_27[9][0], rodada_27[9][1], 'x', rodada_27[5][1], rodada_27[5][0]])
    jogos_rodada_27.append([rodada_27[7][0], rodada_27[7][1], 'x', rodada_27[6][1], rodada_27[6][0]])
    jogos_rodada_27.append(['', '', 'x', '', rodada_27[8][0]])
    jogos_rodada_27.append([rodada_27[11][0], rodada_27[11][1], 'x', rodada_27[10][1], rodada_27[10][0]])
    jogos_rodada_27.append([rodada_27[13][0], rodada_27[13][1], 'x', rodada_27[12][1], rodada_27[12][0]])
    jogos_rodada_27.append([rodada_27[15][0], rodada_27[15][1], 'x', rodada_27[14][1], rodada_27[14][0]])
    jogos_rodada_27.append([rodada_27[17][0], rodada_27[17][1], 'x', rodada_27[16][1], rodada_27[16][0]])
    jogos_rodada_27.append([rodada_27[19][0], rodada_27[19][1], 'x', rodada_27[18][1], rodada_27[18][0]])
    jogos_rodada_27.append([rodada_27[21][0], rodada_27[21][1], 'x', rodada_27[20][1], rodada_27[20][0]])
    jogos_rodada_27.append([rodada_27[23][0], rodada_27[23][1], 'x', rodada_27[22][1], rodada_27[22][0]])
    jogos_rodada_27.append([rodada_27[25][0], rodada_27[25][1], 'x', rodada_27[24][1], rodada_27[24][0]])

    for x in jogos_rodada_27:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_28.append([rodada_28[3][0], rodada_28[3][1], 'x', rodada_28[0][1], rodada_28[0][0]])
    jogos_rodada_28.append([rodada_28[4][0], rodada_28[4][1], 'x', rodada_28[1][1], rodada_28[1][0]])
    jogos_rodada_28.append(['', '', 'x', '', rodada_28[2][0]])

    jogos_rodada_28.append([rodada_28[8][0], rodada_28[8][1], 'x', rodada_28[5][1], rodada_28[5][0]])
    jogos_rodada_28.append([rodada_28[9][0], rodada_28[9][1], 'x', rodada_28[6][1], rodada_28[6][0]])
    jogos_rodada_28.append(['', '', 'x', '', rodada_28[7][0]])

    jogos_rodada_28.append([rodada_28[12][0], rodada_28[12][1], 'x', rodada_28[10][1], rodada_28[10][0]])
    jogos_rodada_28.append([rodada_28[13][0], rodada_28[13][1], 'x', rodada_28[11][1], rodada_28[11][0]])

    jogos_rodada_28.append([rodada_28[16][0], rodada_28[16][1], 'x', rodada_28[14][1], rodada_28[14][0]])
    jogos_rodada_28.append([rodada_28[15][0], rodada_28[15][1], 'x', rodada_28[17][1], rodada_28[17][0]])

    jogos_rodada_28.append([rodada_28[20][0], rodada_28[20][1], 'x', rodada_28[18][1], rodada_28[18][0]])
    jogos_rodada_28.append([rodada_28[21][0], rodada_28[21][1], 'x', rodada_28[19][1], rodada_28[19][0]])

    jogos_rodada_28.append([rodada_28[24][0], rodada_28[24][1], 'x', rodada_28[22][1], rodada_28[22][0]])
    jogos_rodada_28.append([rodada_28[25][0], rodada_28[25][1], 'x', rodada_28[23][1], rodada_28[23][0]])

    for x in jogos_rodada_28:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_29.append([rodada_29[2][0], rodada_29[2][1], 'x', rodada_29[0][1], rodada_29[0][0]])
    jogos_rodada_29.append([rodada_29[3][0], rodada_29[3][1], 'x', rodada_29[4][1], rodada_29[4][0]])
    jogos_rodada_29.append(['', '', 'x', '', rodada_29[1][0]])

    jogos_rodada_29.append([rodada_29[7][0], rodada_29[7][1], 'x', rodada_29[5][1], rodada_29[5][0]])
    jogos_rodada_29.append([rodada_29[8][0], rodada_29[8][1], 'x', rodada_29[9][1], rodada_29[9][0]])
    jogos_rodada_29.append(['', '', 'x', '', rodada_29[6][0]])

    jogos_rodada_29.append([rodada_29[13][0], rodada_29[13][1], 'x', rodada_29[10][1], rodada_29[10][0]])
    jogos_rodada_29.append([rodada_29[12][0], rodada_29[12][1], 'x', rodada_29[11][1], rodada_29[11][0]])

    jogos_rodada_29.append([rodada_29[17][0], rodada_29[17][1], 'x', rodada_29[14][1], rodada_29[14][0]])
    jogos_rodada_29.append([rodada_29[16][0], rodada_29[16][1], 'x', rodada_29[15][1], rodada_29[15][0]])

    jogos_rodada_29.append([rodada_29[21][0], rodada_29[21][1], 'x', rodada_29[18][1], rodada_29[18][0]])
    jogos_rodada_29.append([rodada_29[20][0], rodada_29[20][1], 'x', rodada_29[19][1], rodada_29[19][0]])

    jogos_rodada_29.append([rodada_29[25][0], rodada_29[25][1], 'x', rodada_29[22][1], rodada_29[22][0]])
    jogos_rodada_29.append([rodada_29[24][0], rodada_29[24][1], 'x', rodada_29[23][1], rodada_29[23][0]])

    for x in jogos_rodada_29:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_30.append([rodada_30[3][0], rodada_30[3][1], 'x', rodada_30[1][1], rodada_30[1][0]])
    jogos_rodada_30.append([rodada_30[4][0], rodada_30[4][1], 'x', rodada_30[2][1], rodada_30[2][0]])
    jogos_rodada_30.append(['', '', 'x', '', rodada_30[0][0]])
    jogos_rodada_30.append([rodada_30[8][0], rodada_30[8][1], 'x', rodada_30[6][1], rodada_30[6][0]])
    jogos_rodada_30.append([rodada_30[9][0], rodada_30[9][1], 'x', rodada_30[7][1], rodada_30[7][0]])
    jogos_rodada_30.append(['', '', 'x', '', rodada_30[5][0]])

    for x in jogos_rodada_30:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and isinstance(x[1], float) and isinstance(x[3], float) and x[1] != 0 and x[3] != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    classi = {}
    for item in jogos_rodada_21 + jogos_rodada_22 + jogos_rodada_23 + jogos_rodada_24 + jogos_rodada_25 + \
                jogos_rodada_26 + jogos_rodada_27 + jogos_rodada_28 + jogos_rodada_29 + jogos_rodada_30:
        for nome in grupo_nomes:
            check = nome in item
            if check:
                indice = item.index(nome)

                if nome in classi:
                    if indice == 5:
                        classi[nome].append([item[indice + 1], item[indice - 1]])
                    if indice == 1:
                        classi[nome].append([item[indice - 1], item[indice + 1]])
                else:
                    if indice == 5:
                        classi[nome] = [[item[indice + 1], item[indice - 1]]]
                    if indice == 1:
                        classi[nome] = [[item[indice - 1], item[indice + 1]]]

    classificacao = []
    g1 = []
    g2 = []
    g3 = []
    g4 = []
    g5 = []
    g6 = []

    for item, value in classi.items():
        vit = 0
        der = 0
        emp = 0
        soma = 0
        aproveitamento = 0.0
        soma_pontos = 0.00
        media_pontos = 0.00

        for lista in value:
            vit += sum(lista.count(v) for v in lista if v == 'V')
            der += sum(lista.count(v) for v in lista if v == 'D')
            emp += sum(lista.count(v) for v in lista if v == 'E')
            soma = 3 * vit + 1 * emp
            soma_pontos += sum(v for v in lista if isinstance(v, float))
            soma_pontos_format = f'{"{:.2f}".format(soma_pontos)}'
        aproveitamento = (soma / ((vit + emp + der) * 3)) * 100
        apr = f'{"{:.2f}".format(aproveitamento)}%'
        media_pontos = soma_pontos / (vit + der + emp)
        media_pontos_format = f'{"{:.2f}".format(media_pontos)}'

        classificacao.append([item, vit, emp, der, soma, apr, soma_pontos_format, media_pontos_format])

    for ind in range(0, 5):
        g1.append(classificacao[ind])
    for ind in range(5, 10):
        g2.append(classificacao[ind])
    for ind in range(10, 14):
        g3.append(classificacao[ind])
    for ind in range(14, 18):
        g4.append(classificacao[ind])
    for ind in range(18, 22):
        g5.append(classificacao[ind])
    for ind in range(22, 26):
        g6.append(classificacao[ind])

    return jogos_rodada_21, jogos_rodada_22, jogos_rodada_23, jogos_rodada_24, jogos_rodada_25, jogos_rodada_26, \
           jogos_rodada_27, jogos_rodada_28, jogos_rodada_29, jogos_rodada_30, g1, g2, g3, g4, g5, g6


def premiacao():
    rod_a_rod = []
    prem_list = []
    pont_liga, list_max = pontos()
    prim_turno, seg_turno = pontos_turnos()

    for lm in list_max:
        rod_a_rod.append(lm[0])

    lista_rar = []
    for t in rar:
        if t in rod_a_rod:
            lista_rar.append([t, rod_a_rod.count(t), "{:.2f}".format(len(rar) * rod_a_rod.count(t) * 2)])
        else:
            lista_rar.append([t, 0, "{:.2f}".format(len(rar) * 0 * 2)])

    for lrar in lista_rar:
        prem_list.append(lrar)

    oit_a, oit_b, qua_a, qua_b, semi_a, semi_b, final_a, final_b = retornar_matamata()
    campeao = []
    vice = []

    rodada_atual = Api().mercado().rodada_atual
    partidas = Api().partidas(rodada_atual)

    lider_prim_turno = next(iter(prim_turno))
    # lider_seg_turno = ''
    # campeao_geral = ''
    # vice_campeao = ''
    # terc_colocado = ''
    # quarto_colocado = ''
    # campeao = ''
    # vice = ''

    # for partida in partidas:
    # if partida.clube_casa.nome == 'Santos' and partida.status_transmissao_tr == 'ENCERRADA':
    lider_seg_turno = next(iter(seg_turno))
    print(lider_seg_turno)
    campeao_geral = next(iter(pont_liga))
    vice_campeao = list(pont_liga.keys())[1]
    terc_colocado = list(pont_liga.keys())[2]
    quarto_colocado = list(pont_liga.keys())[3]

    for f_a, f_b in zip(final_a, final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao = f_a[2]
            vice = f_b[2]
        else:
            campeao = f_b[2]
            vice = f_a[2]

        # else:
        #     lider_seg_turno = ''
        #     campeao_geral = ''
        #     vice_campeao = ''
        #     terc_colocado = ''
        #     quarto_colocado = ''
        #     campeao = ''
        #     vice = ''

    return lider_prim_turno, lider_seg_turno, prem_list, campeao_geral, vice_campeao, terc_colocado, quarto_colocado, campeao, vice


def retornar_liga_class():
    dict_time_total = {}
    dict_time_pontos = {}
    dict_time_turno_pontos = {}

    with open('static/liga_class.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_total[k] = v

    if api.mercado().status.nome == 'Final de temporada':
        for chave, valor in dict_time_total.items():
            if chave in dict_time_pontos:
                dict_time_pontos[chave].append([valor[0], valor[1], valor[2]])
                dict_time_turno_pontos[chave].append([valor[0], valor[1], valor[3]])
            else:
                dict_time_pontos[chave] = [valor[0], valor[1], valor[2]]
                dict_time_turno_pontos[chave] = [valor[0], valor[1], valor[3]]

    if api.mercado().status.nome == 'Mercado aberto':
        for chave, valor in dict_time_total.items():
            if chave in dict_time_pontos:
                dict_time_pontos[chave].append([valor[0], valor[1], valor[2]])
                dict_time_turno_pontos[chave].append([valor[0], valor[1], valor[3]])
            else:
                dict_time_pontos[chave] = [valor[0], valor[1], valor[2]]
                dict_time_turno_pontos[chave] = [valor[0], valor[1], valor[3]]
        #
        # if api.mercado().status.nome == 'Mercado fechado':
        #
        #     with ThreadPoolExecutor(max_workers=40) as executor:
        #         threads = executor.map(api.time_parcial, todos_ids)
        #
        #         for team_parc in threads:
        #             if not team_parc.info.nome == 'AvantiHulkFc' and not team_parc.info.nome == '0VINTE1 FC':
        #                 dict_time_total[team_parc.info.nome].append(team_parc.pontos)

        for chave_, valor_ in dict_time_total.items():
            if chave_ in dict_time_pontos:
                dict_time_pontos[chave_].append([valor_[0], valor_[4], valor_[2] + valor_[4]])
                dict_time_turno_pontos[chave_].append([valor_[0], valor_[4], valor_[3] + valor_[4]])
            else:
                dict_time_pontos[chave_] = [valor_[0], valor_[4], valor_[2] + valor_[4]]
                dict_time_turno_pontos[chave_] = [valor_[0], valor_[4], valor_[3] + valor_[4]]

    return dict_time_pontos, dict_time_turno_pontos


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)