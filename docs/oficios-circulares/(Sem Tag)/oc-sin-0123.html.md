# Ofício Circular CVM/SIN 01/23

> **Fonte:** https://conteudo.cvm.gov.br/legislacao/oficios-circulares/sin/oc-sin-0123.html  

> **Espelhado em:** 09/11/2026  


## Metadados

- **Ementa (catalogo do site):** Descontinuação do login nativo do sistema CVMWeb
- **Data (pagina de detalhe):** Wed Apr 12 14:00:00 BRT 2023
- **Epigrafe / Ementa:** Descontinuação do login nativo do sistema CVMWeb

## Documentos / Anexos (baixados localmente)

- **Ofício Circular CVM/SIN 01/23** — arquivo: `../anexos/oc-sin-0123.html/oc-sin-0123.pdf` (formato: pdf)
- **Anexo - Documentação Técnica API Recepção de Informes** — arquivo: `../anexos/oc-sin-0123.html/Documentacao_Tecnica_Plataforma_Supevisao_v11.pdf` (formato: pdf)

## Texto completo — Ofício Circular CVM/SIN 01/23

<sub>Fonte: `oc-sin-0123.pdf` — 1 paginas</sub>

Ofício-Circular nº 1/2023/CVM/SIN 
Rio de Janeiro, 12 de abril de 2023 
 
Aos 
Usuários do Sistema CVMWeb e do web service de processamento de informes (API) 
 
Assunto: Descontinuação do login nativo do sistema CVMWeb 
 
Prezados Senhores, 
 
1. A divulgação deste Ofício Circular tem como objetivo divulgar que, a partir de 15/5/2023, o 
acesso identificado ("login") ao CVMWeb e sistemas correlatos se dará exclusivamente pelo por 
meio do “Login GOV.BR”, que já disponibilizamos como segunda opção de acesso desde 2020. 
  
2. Ultrapassada a fase de estabilização de uso da plataforma GOV.BR como meio de acesso aos 
sistemas CVMWeb e correlatos, em função da maior robustez, flexibilidade e segurança por ela 
oferecida, a CVM optou por migrar para a ferramenta em caráter de exclusividade. Assim, a partir 
de 15/5/2023, não será mais possível acessar o sistema CVMWeb ou correlatos com o uso da senha 
antiga. 
 
3. Para mais informações sobre como criar sua conta GOV.BR, caso ainda não a possua, acesse o 
link https://www.gov.br/pt-br/servicos/criar-sua-conta-gov.br. 
 
4. Informamos, ainda, que a descontinuação da ferramenta também atende os objetivos 
estratégicos da CVM de consolidação no uso de serviços prestados pelo Governo Digital, 
aprofundando o processo de transformação digital e de integração dos serviços de governo para 
uma comunidade que, em relação ao GOV.BR, já conta com quase 150 milhões de usuários. 
 
5. Por fim, aos usuários do web service de processamento de informes (API), haverá uma nova 
funcionalidade no CVMWeb já a partir de 10/04/2023 que possibilitará a geração de chaves de 
acesso, que substituirão o login e senha na API (que não utiliza o login GOV.BR). Para mais 
detalhes sobre a geração e utilização das chaves, acesse a documentação técnica anexa a este ofício. 
A autenticação nativa do CVMWeb seguirá funcionando especificamente na API até o dia 
30/6/2023, quando será substituída integralmente pela autenticação baseada em chaves de acesso. 
  
6. Para esclarecimentos adicionais, solicitamos contatar o Suporte Externo da CVM, acessível por 
meio do endereço eletrônico suporteexterno@cvm.gov.br. 
Atenciosamente, 
 
Assinado digitalmente por  
DANIEL WALTER MAEDA BERNARDO 
Superintendente de Supervisão de Investidores Institucionais

## Texto completo — Anexo - Documentação Técnica API Recepção de Informes

<sub>Fonte: `Documentacao_Tecnica_Plataforma_Supevisao_v11.pdf` — 9 paginas</sub>

API de recepção e processamento de Informes 
Documentação Técnica – v1.1  
 
1) Geração de Chaves de Acesso 
Para se autenticar na API de recepção e processamento de informes, será 
necessário o uso de chave de acesso gerada no CVMWeb, em área 
identificada. 
1) Após acessar o CVMWeb e se identificar (login), acessar no menu à 
esquerda a opção ‘Chaves de Acesso’: 
 
 
 
2) Dentro da funcionalidade, é possível gerar uma nova chave de acesso, 
que ficará vinculada ao seu usuário/CPF, bem como visualizar as 
chaves geradas: 
 
2.1) Geração de chave de acesso:
2.2) Visualização das chaves de acesso, bem como opção de 
revogação: 
 
 
Com a chave de acesso gerada, será possível se autenticar na API e receber 
um access token, utilizado para enviar informes. 
2) Autenticação  
Mediante parâmetros de autenticação, retorna token de acesso para envio de 
informes ou acesso negado.  
 URL 
 
PRODUÇÃO: 
https://web.cvm.gov.br/services/auth/get/access/token 
 
AMBIENTE DE TESTES/”SANDBOX”: (instruções abaixo) 
https://web.cvm.gov.br/services/sandbox/auth/get/access/token 
 
Method: 
POST 
 Headers necessários no Request 
 
Com a chave de acesso (secret) gerada conforme item anterior – 
Geração de chaves de acesso, o “header” Authorization deve ir com o 
seguinte valor (codificado em Base64): 
 
CPF_usuário:chave_de_acesso 
 
PARA TESTES, UTILIZE 1234 COMO CHAVE DE ACESSO PARA 
QUALQUER CPF.
Ex: CPF 11111111111 e chave de acesso XXXXXX 
No header, deve constar o valor 11111111111:XXXXXX codificado em 
Base64, que equivale à String MTExMTExMTExMTE6WFhYWFhY. 
O header do exemplo acima seria: 
Nome Valor 
Authorization Basic 
MTExMTExMTExMTE6WFhYWFhY 
 Corpo da requisição (Request body) 
Corpo vazio. 
 Resposta esperada (sucesso): 
Situação Código de 
retorno HTTP 
Corpo da resposta 
Autenticação 
efetuada 
com 
sucesso 
200 (OK) { 
    "access_token": "xxxx", 
    "token_type": "bearer", 
    "expires_in": 3600 
} 
Após o login bem sucedido, o retorno volta com três dados importantes: 
 O token de acesso (access_token) 
 O tipo do token (por padrão, bearer) 
 O tempo de vida do token, em segundos 
o No exemplo acima, uma hora (padrão). 
Com esses dados, sua aplicação já poderá enviar informes para o web 
service durante o tempo de vida do token. Após sua expiração, um novo 
token deverá ser gerado. 
 Respostas com erro: 
 
Situação Código de 
retorno HTTP 
Corpo da resposta 
Autenticação 
inválida 
401 (Unauthorized) { 
"error": "invalid_client", 
"error_description": "Credenciais 
invalidas" 
} 
Erro interno 500 (Internal 
Server Error) 
{“error_description”:“descrição do 
erro”}
2) Processamento de informes 
As instruções abaixo se referem ao uso da API para o envio e processamento 
dos informes. Inicialmente, listamos as URLs por tipo de informe e na seção 
posterior, os detalhes técnicos que são comuns a todos. 
2.1) Processar Informes diários 
Padrão XML: 
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiar
ioNetV3.asp 
URL 
PRODUÇÃO:  
https://web.cvm.gov.br/services/informes/api/informe/diario 
AMBIENTE DE TESTES/”SANDBOX”: 
https://web.cvm.gov.br/services/sandbox/informes/api/informe/diario 
2.2) Processar Lâmina de Fundos 
Padrão XML: 
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina
V2.asp 
URL 
PRODUÇÃO: 
https://web.cvm.gov.br/services/informes/api/informe/lamina 
AMBIENTE DE TESTES/”SANDBOX”: 
https://web.cvm.gov.br/services/sandbox/informes/api/informe/lamina 
2.3) Processar Informe de Fundo 157 
Padrão XML: 
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.a
sp 
URL 
PRODUÇÃO:  
https://web.cvm.gov.br/services/informes/api/informe/fundo157 
AMBIENTE DE TESTES/”SANDBOX”: 
https://web.cvm.gov.br/services/sandbox/informes/api/informe/fundo157
2.4) Processar Informe de Prestadores de 
Serviço 
Padrão XML: 
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.as
p 
URL 
PRODUÇÃO:  
https://web.cvm.gov.br/services/informes/api/informe/prestservicos 
AMBIENTE DE TESTES/”SANDBOX”: 
https://web.cvm.gov.br/services/sandbox/informes/api/informe/prestservic
os 
2.5) Processar Informe Mensal de 
Investidores Não Residentes 
Padrão XML: 
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMe n
salINR.asp 
URL 
PRODUÇÃO:  
https://web.cvm.gov.br/services/informes/api/informe/mensalinr 
AMBIENTE DE TESTES/”SANDBOX”: 
https://web.cvm.gov.br/services/sandbox/informes/api/informe/mensalinr 
2.7) Orientações gerais para envio dos 
Informes 
Para enviar qualquer um dos informes acima, valem as instruções 
abaixo, variando apenas a URL e o XML enviado.  
 Method: 
POST 
 Headers necessários no Request 
Nome Valor 
Content-Type application/xml; charset=UTF-8 
ou  
text/xml; charset=UTF-8 
Authorization [Token_Type] [Access_Token]
O header Content-Type pode receber qualquer um dos valores 
especificados. Atente-se para o ‘encoding’ UTF-8, que é o esperado no 
corpo da requisição. 
 
O header Authorization receberá dois valores, separados por um 
espaço em branco, como colocado acima. O primeiro deles é o tipo do 
token (‘token type’), que é retornado pelo método de autenticação 
(padrão: bearer) e o segundo  o próprio token de acesso 
(‘access_token’), também retornado pelo serviço. 
Para o exemplo anterior, o header ficaria: 
 
Authorization: bearer xxxx 
 Corpo da requisição (Request body) 
No corpo da requisição deve ser enviado o conteúdo XML que já é 
enviado à CVM atualmente e cujo padrão pode ser encontrado em 
http://sistemas.cvm.gov.br -> Sistema CVMWeb -> Envio de 
Documentos -> Padrões de Arquivos - XML e Outros. 
Apesar de não ser obrigatório, é recomendável enviar o XML sem 
formatação, quebras de linha ou espaços antes ou após as tags. O 
retorno do processamento devolve um hash de verificação 
(“checksum”) que não leva em consideração nenhum desses 
caracteres. 
 Resposta esperada (sucesso): 
Situação Código de 
retorno 
HTTP 
Corpo da resposta 
(exemplo; maiores detalhes abaixo) 
Informe 
processado 
200 (OK) { 
    "protocoloRecebimento": 1234567, 
    "statusGeralProcessamento": "P", 
    "checksum": 
"ca46003634a7d2478c606759fd04ec32c7da9fe5887a8c54a348a
439f40aa60f", 
    "dataHoraProcessamento": "14/07/2020 16:30:49", 
    "totalInformesProcessados": 3, 
    "detalhes": { 
        "11.111.111/1111-11": { 
            "protocoloProcessamento": 10000000, 
            "statusProcessamento": "E", 
           "mensagensAssociadas": [ 
              "O usuário (CPF: XXXX) não possui permissão para 
enviar informe diário para este fundo", 
              “mensagem de erro 2”, 
              “mensagem de erro 3” 
            ] 
        }, 
            "22.222.222/2222-22": { 
            "protocoloProcessamento": 10000001, 
            "statusProcessamento": "S",
"mensagensAssociadas": [] 
        } 
            "11.111.111/1111-11": { 
            "protocoloProcessamento": 10000000, 
            "statusProcessamento": "E", 
           "mensagensAssociadas": [ 
              "Patrimônmio Líquido inválido" 
            ] 
        } 
    } 
} 
A resposta esperada não quer dizer que o informe foi processado com 
sucesso, isso é detalhado no corpo do JSON retornado, como detalhado a 
seguir. Um código de retorno 200 implica que o processamento ocorreu 
sem falhas. 
Detalhes do JSON de retorno 
Chave Definição 
protocoloRecebimento Número do protocolo de recebimento –indica 
que a CVM recepcionou o informe com 
sucesso. Não implica automaticamente no 
processamento do mesmo. 
statusGeralProcessamento Indica o status geral do processamento do 
informe enviado, podendo ter os seguintes 
valores: 
 
 
Valor Significado 
S Sucesso – Todos os 
informes 
recepcionados foram 
processados com 
sucesso. 
P Sucesso parcial. 
Indica que nem 
todos os informes 
foram processados 
com sucesso. 
E Erro geral. Todos os 
informes enviados 
tiveram erros de 
validação. 
N Erro interno – 
Ocorreu algum erro 
nos servidores da 
CVM durante o 
processamento. 
Nesse caso, a
orientação inicial é 
reenviar o informe e 
caso o erro persista, 
acionar o Suporte a 
Sistemas da CVM. 
 
checksum Esse campo é uma “hash” usando o algoritmo 
SHA-256 do XML enviado no corpo da 
requisição. Na geração do hash todos os 
espaços entre tags, no início e final do arquivo 
são removidos, bem como a quebras de linha. 
 
Por exemplo, o XML abaixo (formatado e com 
espaços entre tags):  
<CAB> 
  <INF1>xxx</INF1>   <INF2>qqq</INF2> 
</CAB> 
<CORPO> 
<A>b</A> 
<B>c</B> 
</CORPO> 
 
Irá ser convertido para a seguinte “String”, em 
linha única: 
 
<CAB><INF1>xxx</INF1><INF2>qqq</INF2>
</CAB><CORPO><A>b</A><B>c</B></COR
PO> 
 
É dessa última string que o checksum SHA-
256 será gerado e retornado. 
dataHoraProcessamento Data e hora exata em que o processamento 
do informe foi efetuado. 
totalInformesProcessados Total de informes processados. 
detalhes Mapa com os detalhes do processamento. 
Cada chave no mapa é um CNPJ dos que 
foram enviados no informe e o valor é um 
objeto com três chaves, conforme detalhado 
abaixo. 
         
protocoloProcessamento 
Número do protocolo de processamento para 
o CNPJ em questão. 
      statusProcessamento Status do processamento do informe 
específico, podendo ter os valores: 
Valor Significado 
S Sucesso 
E Erro 
 
      mensagensAssociadas Lista de strings com mensagens detalhando 
os erros. Se o processamento tiver sido com 
sucesso, este campo será uma lista vazia.
 Respostas com erro: 
 
Situação Código de retorno 
HTTP 
Corpo da resposta 
Token de acesso 
inválido ou expirado 
401 (Unauthorized)  
Erro interno 500 (Internal 
Server Error)

---
_Espelho textual gerado automaticamente a partir de conteudo.cvm.gov.br. Texto completo normatizado nos PDFs citados; verificacao final deve ser feita no original (DOU/site CVM)._
