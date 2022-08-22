import requests
import json
from pathlib import Path
from subprocess import Popen
import os
from threading import Thread
from collections import deque


# Token do telegram obtido na criação do bot
CHAVE = os.environ['CHAVE_TEL']


class BotTelegran:
    def __init__(self, token) -> None:
        self.token = token
        self.urlbase = f'https://api.telegram.org/bot{self.token}/'
        self.tasks = deque(maxlen=3) # controla o total das rotinas
        self.__raiz = Path().absolute().parent.parent # raiz principal das pastas
    

    @property
    def raiz(self):
        return self.__raiz


    # TODO: Retornar um dict com o nome de todos os APPS
    def dict_app(self):
        return {p.stem:p for p in self.raiz.glob("*")}


    # TODO: Retornar um dict com as ROTINAS
    def rotinas(self):
        return  {
            '1': ["Planilha 2.0", f"{str(self.dict_app()['PYTHON'] / 'extrair_hyper')},python extracao.py"],
            '2': ["Divergencia", f"{str(self.dict_app()['PYTHON'] / 'ConferenciaFL')},python CriarDivergencia.py"],
            '3': ["Chamados Web", f"{str(self.dict_app()['PYTHON'] / 'chamados_web')},python abrir_site.py"],
        }

    
    # TODO: Menu formatado das rotinas
    def menu(self):
        msg = '-=' * 10
        msg += "\n{:^20}\n".format("MENU")
        msg += '-=' * 10

        for k, v in self.rotinas().items():
            msg += f'\n{k} - {v[0]}'
        msg += '\n'
        msg += '-=' * 10
        msg += '\n>>>'

        return msg


    # TODO: Menu das tarefas em andamento
    def menu_tasks(self):
        msg = "Tarefas ..\n\n"
        for t in self.tasks:
            msg += f"{t}\n"

        return msg


    # TODO: Rodar o scripting -- escolhido
    def roda_script(self, argumento: str, nometask: str, chat_id):
        # TODO: Separar o argumento
        args = argumento.split(',')
        
        # TODO: Atribuir caminho e execucao
        raiz = args[0]
        comando = args[1]
        
        # TODO: Executa a rotina
        Popen(comando, cwd=raiz, shell=True).wait()
        
        # remove a rotina da tasks
        self.tasks.remove(nometask)

        # ENIAR RESPOSTA NO CHAT
        resp = f'Tarefa: {nometask}, finalizada !'
        self.enviar_resposta(resp, chat_id)


    # TODO: Metodo para iniciar o bot
    def rodar(self):
        update_id = None # pega ultima atualizacao

        while True:
            # resposta do telegran
            altz =self.obter_msg(update_id)
            
            # dicionario result - para mensagens
            msgs = altz['result']
            
            # verifica se tem mensagem
            if msgs:
                # loop em todas as mensagens
                for ms in msgs:
                    update_id = ms['update_id']
                    chat_id = ms['message']['from']['id']
                    
                    bool_primeira_msg = ms['message']['message_id'] == 1

                    rst = self.resposta(ms, bool_primeira_msg, chat_id)

                    self.enviar_resposta(rst, chat_id)


    # TODO: Obter as mensagens
    def obter_msg(self, update_id):
        # link das atualizacoes
        link_req = f'{self.urlbase}getUpdates?timeout=100' # esperar 100 segundos para atualizar
        
        # verifica se ja tem um update id - se tiver incrementar 1, para obter o ultimo
        if update_id:
            link_req = f'{link_req}&offset={update_id + 1}'
        
        # retorno da req
        rst = requests.get(link_req)
        
        # pega a string do json e transforma em dicionario python
        return json.loads(rst.content)


    # TODO: Criar uma resposta
    def resposta(self, ms, bool_primeira_msg, chat_id):
        ms = ms['message']['text']

        if bool_primeira_msg or ms.lower() == 'menu':
            msg = self.menu()

            return msg

        if ms.lower() == 'tarefas':
            if len(self.tasks) == 0:
                return "Nenhuma tarefa em execucao !"
            else:
                return self.menu_tasks()
        

        # verifica se as opcoes esta no dicionario
        if ms.lower() in self.rotinas().keys():
            caminho = self.rotinas()[ms.lower()]
            
            # executa rotina escolhida
            if len(self.tasks) == 3:
                return "Limite de rotinas atingida favor esperar !"

            if caminho[0] in self.tasks:
                return f"Rotina {caminho[0]} ja esta em execucao !"
            
            else:
                # cria rotina paralela
                t = Thread(target=self.roda_script, args=(caminho[1], caminho[0], chat_id))
                t.name = caminho[0]
                
                # adiciona rotina as tasks
                self.tasks.appendleft(t.name)
                
                # inicia a rotina paralela
                t.start()
                
                return f"Rotina {caminho[0]}, rodando ..."
        
        else:
            return "Para o menu de tarefas ? Digite 'menu'"


    # TODO: 04 Responder
    def enviar_resposta(self, resposta, chat_id):
        link_send = f'{self.urlbase}sendMessage?chat_id={chat_id}&text={resposta}'

        requests.get(link_send)


if __name__ == '__main__':
    bot = BotTelegran(CHAVE)
    bot.rodar()