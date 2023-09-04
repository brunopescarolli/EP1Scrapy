import scrapy
from unidecode import unidecode
import time

# Exercício:
# Buscar:
# Nome, ID, Tamanho e Peso
# Alguns dados estão dentro da página do Pokemon
# Página do Pokémon deve usar o parser "parser_pokemon"

# Dica: Principais CSS Selectors:
# https://www.w3schools.com/cssref/css_selectors.php

class PokeSpider(scrapy.Spider):
  name = 'pokespider'
  start_urls = ['https://pokemondb.net/pokedex/all']
  base_url = 'https://pokemondb.net'

  def parse(self, response):
    ### tabela de seletores de CSS
    start = time.time()

    tabela_pokedex = "table#pokedex > tbody > tr"
    linhas = response.css(tabela_pokedex)
    for linha in linhas:
      coluna_href = linha.css("td:nth-child(2) > a::attr(href)")
      yield response.follow(coluna_href.get(), self.parser_pokemon)
      break
    
    print(f"{time.time() - start}s")

  def parser_pokemon(self, response):
    id = response.css(".vitals-table > tbody > tr:nth-child(1) > td > strong::text")
    name = response.css("#main > h1::text")
    weight = response.css(".vitals-table > tbody > tr:nth-child(5) > td::text")
    height = response.css(".vitals-table > tbody > tr:nth-child(4) > td::text")
    types = response.css(".grid-row > div:nth-child(2) > table > tbody > tr:nth-child(2) > td > a:nth-child(1)::text")
    types2 = response.css(".grid-row > div:nth-child(2) > table > tbody > tr:nth-child(2) > td > a:nth-child(2)::text")
    url = response.request.url
    nextevoid = response.css(".infocard-list-evo > div.infocard > span > small::text")
    nextevoname = response.css(".infocard-list-evo > div.infocard > span:nth-child(2) > a::text")
    nextevourl = response.css(".infocard-list-evo > div.infocard > span:nth-child(2) > a::attr(href)")
    css_result = response.css(".grid-row > div:nth-child(2) > table > tbody > tr:nth-child(6) > td > .text-muted > a::attr(href)").getall()
    

    # Checando se tem evolução
    evo_formatado = [e for e in nextevoid.getall() if e.__contains__('#')]
    idx_next_evo = None
    for i in range(len(evo_formatado)):
      if (evo_formatado[i].__contains__(id.get())):
        if(i + 1 < len(evo_formatado)):
          idx_next_evo = i + 1
          break
          
    #Formatando peso e altura
    weight_arr = weight.get().split(".")
    height_arr = height.get().split(".")

    #Separando tipos
    types_arr = []
    types_arr.append(types.get())
    if(types2.get() != None):
      types_arr.append(types2.get())


    linha = {
      'id': int(id.get()),
      'name': unidecode(name.get().strip()),
      'weight': float(f"{weight_arr[0]}.{weight_arr[1][0]}"),
      'height': float(f"{height_arr[0]}.{height_arr[1][0]}"),
      'types': types_arr,
      'url': url,
      'abilities': []
    }

    if(idx_next_evo != None):
      linha['evolution'] = {'id': int(evo_formatado[idx_next_evo].replace("#","")) if len(evo_formatado) > 0 and idx_next_evo != None else None,
      'name': nextevoname.getall()[idx_next_evo] if len(nextevoname.getall()) > 0 and idx_next_evo != None else None,
      'url': f"https://pokemondb.net{nextevourl.getall()[idx_next_evo]}" if len(nextevourl.getall()) > 0 and idx_next_evo != None else None} 
    else:
      linha['evolution'] = 'N/A'
    
    for href_ability in css_result:
      # https://stackoverflow.com/questions/9334522/scrapy-follow-link-to-get-additional-item-data
      request = response.follow(f"{self.base_url}{href_ability}", callback=self.parser_ability)
      request.meta['linha'] = linha
      request.meta['num_abilities'] = len(css_result)
      yield request


  def parser_ability (self, response):
  
    name_ability = "#main > h1::text"
    text_ability = "#main > div > div > p"
  
    name = response.css(name_ability)
    text = response.css(text_ability)

    linha = response.meta['linha']

    # https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
    text_string = unidecode(''.join(text.css('*::text').getall())).replace('\n','')

    linha['abilities'].append({'name': name.get().strip(),'text': text_string, 'url': response.request.url})
    if(len(linha['abilities']) == response.meta['num_abilities']):
      yield linha
